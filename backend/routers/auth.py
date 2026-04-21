import hashlib
import os
import tempfile
from io import BytesIO
from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from starlette.datastructures import Headers, UploadFile as StarletteUploadFile

from database import get_db
from deps import get_current_user
from models import User
from ocr import ocr_texts_contain_name_and_school, run_ocr_on_image_path
from schemas import (
    LoginResponse,
    LoginUserInfo,
    PasswordChangeBody,
    RegisterResponse,
    StudentIdVerifyResponse,
    UserLogin,
    UserProfileOut,
)
from security import (
    create_access_token,
    create_student_id_verify_token,
    decode_student_id_verify_token,
    hash_password,
    verify_password,
)
from upload_storage import delete_uploaded_file, save_profile_image, save_student_id_card

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/verify-student-id", response_model=StudentIdVerifyResponse)
async def verify_student_id(
    name: str = Form(..., min_length=1, max_length=50),
    school_name: str = Form(..., min_length=1, max_length=100),
    student_id_card: UploadFile = File(..., description="학생증 이미지"),
) -> StudentIdVerifyResponse:
    """입력한 이름·학교명이 학생증 OCR 결과에 포함되는지 검사 후, 회원가입용 짧은 수명 토큰을 발급합니다."""
    raw = await student_id_card.read()
    if len(raw) == 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="빈 파일은 업로드할 수 없습니다.")
    file_hash = hashlib.sha256(raw).hexdigest()

    fd, tmp_path = tempfile.mkstemp(suffix=".jpg")
    os.close(fd)
    try:
        Path(tmp_path).write_bytes(raw)
        try:
            texts = run_ocr_on_image_path(tmp_path)
        except RuntimeError as e:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=str(e),
            ) from e
        except FileNotFoundError as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="이미지를 읽을 수 없습니다.") from e
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"학생증 인식에 실패했습니다: {e!s}",
            ) from e

        if not ocr_texts_contain_name_and_school(texts, name, school_name):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="학생증에서 입력하신 이름 또는 학교명을 찾지 못했습니다. 사진이 선명한지, 이름·학교명이 카드에 적힌 대로인지 확인해 주세요.",
            )

        token = create_student_id_verify_token(name, school_name, file_hash)
        return StudentIdVerifyResponse(verified=True, verification_token=token)
    finally:
        try:
            os.unlink(tmp_path)
        except OSError:
            pass


@router.post("/register", response_model=RegisterResponse)
async def register(
    user_id: str = Form(..., min_length=1, max_length=50),
    password: str = Form(..., min_length=8, max_length=128),
    name: str = Form(..., min_length=1, max_length=50),
    school_name: str = Form(..., min_length=1, max_length=100),
    phone: str = Form(..., min_length=1, max_length=20),
    email: str = Form(..., min_length=1, max_length=100),
    student_id: str | None = Form(None),
    interest_major: str | None = Form(None),
    student_id_verification_token: str = Form(..., description="POST /verify-student-id 로 발급받은 토큰"),
    student_id_card: UploadFile = File(..., description="학생증 이미지"),
    db: Session = Depends(get_db),
) -> RegisterResponse:
    raw = await student_id_card.read()
    if len(raw) == 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="빈 파일은 업로드할 수 없습니다.")
    file_hash = hashlib.sha256(raw).hexdigest()
    try:
        vn, vs, vh = decode_student_id_verify_token(student_id_verification_token)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e
    if vh != file_hash:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="학생증 이미지가 인증 당시와 다릅니다. 동일한 사진으로 다시 인증해 주세요.",
        )
    if vn != name.strip() or vs != school_name.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="이름 또는 학교명이 학생증 인증 당시와 일치하지 않습니다.",
        )

    upload = StarletteUploadFile(
        file=BytesIO(raw),
        filename=student_id_card.filename or "student_id.jpg",
        headers=Headers({"content-type": student_id_card.content_type or "image/jpeg"}),
    )
    relative_path = await save_student_id_card(upload)
    user = User(
        user_id=user_id.strip(),
        password=hash_password(password),
        name=name.strip(),
        school_name=school_name.strip(),
        phone=phone.strip(),
        email=email.strip().lower(),
        student_id=student_id.strip() if student_id else None,
        interest_major=interest_major.strip() if interest_major else None,
        registration_status="PENDING",
        student_id_card_path=relative_path,
    )
    db.add(user)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        delete_uploaded_file(relative_path)
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="이미 사용 중인 아이디, 전화번호 또는 이메일입니다.",
        ) from None
    except Exception:
        db.rollback()
        delete_uploaded_file(relative_path)
        raise
    db.refresh(user)
    return RegisterResponse(user_id=user.user_id, name=user.name)


@router.post("/login", response_model=LoginResponse)
def login(body: UserLogin, db: Session = Depends(get_db)) -> LoginResponse:
    user = db.get(User, body.user_id.strip())
    if user is None or not verify_password(body.password, user.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="아이디 또는 비밀번호가 올바르지 않습니다.",
        )
    if user.account_status != "ACTIVE":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="비활성화된 계정입니다.",
        )
    if not user.is_admin:
        if user.registration_status == "PENDING":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="관리자 승인 대기 중입니다. 승인 후 로그인할 수 있습니다.",
            )
        if user.registration_status == "REJECTED":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="가입이 거절된 계정입니다. 관리자에게 문의해 주세요.",
            )
    user.token_version = int(user.token_version) + 1
    db.commit()
    db.refresh(user)
    token = create_access_token(
        user.user_id,
        is_admin=user.is_admin,
        token_version=user.token_version,
    )
    return LoginResponse(
        access_token=token,
        token_type="bearer",
        user=LoginUserInfo(
            user_id=user.user_id,
            name=user.name,
            email=user.email,
            school_name=user.school_name,
            is_admin=user.is_admin,
            profile_image_path=user.profile_image_path,
        ),
    )


@router.get("/me", response_model=LoginUserInfo)
def get_me(user: User = Depends(get_current_user)) -> LoginUserInfo:
    return LoginUserInfo(
        user_id=user.user_id,
        name=user.name,
        email=user.email,
        school_name=user.school_name,
        is_admin=user.is_admin,
        profile_image_path=user.profile_image_path,
    )


@router.get("/me/profile", response_model=UserProfileOut)
def get_my_profile(user: User = Depends(get_current_user)) -> UserProfileOut:
    return UserProfileOut(
        user_id=user.user_id,
        name=user.name,
        email=user.email,
        school_name=user.school_name,
        phone=user.phone,
        interest_major=user.interest_major,
        profile_image_path=user.profile_image_path,
        is_admin=user.is_admin,
    )


@router.patch("/me/profile")
async def update_my_profile(
    phone: str = Form(..., min_length=1, max_length=20),
    interest_major: str | None = Form(None),
    profile_image: UploadFile | None = File(None),
    clear_profile_image: str | None = Form(None),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> UserProfileOut:
    phone_stripped = phone.strip()
    if phone_stripped != user.phone:
        dup = db.scalars(
            select(User).where(User.phone == phone_stripped, User.user_id != user.user_id),
        ).first()
        if dup is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="이미 사용 중인 전화번호입니다.",
            )

    im: str | None = None
    if interest_major is not None:
        s = interest_major.strip()
        im = s if s else None

    user.phone = phone_stripped
    user.interest_major = im

    if profile_image is not None and profile_image.filename:
        rel = await save_profile_image(profile_image)
        if user.profile_image_path:
            delete_uploaded_file(user.profile_image_path)
        user.profile_image_path = rel
    elif clear_profile_image and clear_profile_image.strip().lower() in ("1", "true", "yes"):
        if user.profile_image_path:
            delete_uploaded_file(user.profile_image_path)
        user.profile_image_path = None

    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="이미 사용 중인 전화번호입니다.",
        ) from None
    db.refresh(user)
    return UserProfileOut(
        user_id=user.user_id,
        name=user.name,
        email=user.email,
        school_name=user.school_name,
        phone=user.phone,
        interest_major=user.interest_major,
        profile_image_path=user.profile_image_path,
        is_admin=user.is_admin,
    )


@router.post("/me/password")
def change_my_password(
    body: PasswordChangeBody,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict[str, bool]:
    if not verify_password(body.current_password, user.password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="현재 비밀번호가 일치하지 않습니다.",
        )
    user.password = hash_password(body.new_password)
    db.commit()
    return {"ok": True}
