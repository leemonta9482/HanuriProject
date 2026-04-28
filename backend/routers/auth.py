import hashlib
import os
import tempfile
from io import BytesIO
from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from starlette.datastructures import Headers, UploadFile as StarletteUploadFile

from database import get_db
from deps import get_current_user
from models import School, User
from ocr import (
    normalize_student_id,
    ocr_texts_contain_name_and_school,
    ocr_texts_contain_student_id,
    run_ocr_on_image_path,
)
from email_utils import build_registration_email_code_message, send_email
from schemas import (
    LoginResponse,
    LoginUserInfo,
    PasswordChangeBody,
    PublicSchoolItem,
    PublicSchoolListResponse,
    RegistrationEmailCodeSendBody,
    RegistrationEmailCodeSendResponse,
    RegistrationEmailCodeVerifyBody,
    RegistrationEmailCodeVerifyResponse,
    RegisterResponse,
    StudentIdVerifyResponse,
    UserIdAvailabilityResponse,
    UserLogin,
    UserProfileOut,
)
from security import (
    create_access_token,
    create_email_code_challenge_token,
    create_email_registration_verified_token,
    create_student_id_verify_token,
    decode_email_registration_verified_token,
    decode_student_id_verify_token,
    hash_password,
    normalize_registration_email,
    registration_email_verification_code,
    verify_email_code_challenge,
    verify_password,
)
from upload_storage import delete_uploaded_file, save_profile_image, save_student_id_card

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.get("/schools", response_model=PublicSchoolListResponse)
def list_public_schools(db: Session = Depends(get_db)) -> PublicSchoolListResponse:
    """회원가입 화면용 학교 목록(노출 활성화된 학교만, 이름순)."""
    rows = (
        db.execute(
            select(School).where(School.is_active == True).order_by(School.name.asc())  # noqa: E712
        )
        .scalars()
        .all()
    )
    return PublicSchoolListResponse(items=[PublicSchoolItem.model_validate(s) for s in rows])


@router.get("/user-id-available", response_model=UserIdAvailabilityResponse)
def check_user_id_available(
    user_id: str = Query(..., min_length=1, max_length=50),
    db: Session = Depends(get_db),
) -> UserIdAvailabilityResponse:
    """회원가입 전 아이디 사용 가능 여부(이미 존재하면 available=False)."""
    uid = user_id.strip()
    if not uid:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="아이디를 입력해 주세요.")
    taken = db.get(User, uid) is not None
    return UserIdAvailabilityResponse(available=not taken)


@router.post("/registration-email/send", response_model=RegistrationEmailCodeSendResponse)
def send_registration_email_code(
    body: RegistrationEmailCodeSendBody,
    db: Session = Depends(get_db),
) -> RegistrationEmailCodeSendResponse:
    """회원가입 전 이메일로 4자리 인증번호를 발송하고, 다음 단계(번호 확인)용 챌린지 JWT를 반환합니다."""
    normalized = normalize_registration_email(str(body.email))
    existing = db.scalars(select(User).where(User.email == normalized)).first()
    if existing is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="이미 가입된 이메일입니다.",
        )
    code = registration_email_verification_code()
    challenge_token = create_email_code_challenge_token(normalized, code)
    subject, text_body = build_registration_email_code_message(code)
    send_email(normalized, subject, text_body)
    return RegistrationEmailCodeSendResponse(challenge_token=challenge_token)


@router.post("/registration-email/verify", response_model=RegistrationEmailCodeVerifyResponse)
def verify_registration_email_code(body: RegistrationEmailCodeVerifyBody) -> RegistrationEmailCodeVerifyResponse:
    """챌린지 JWT와 사용자가 입력한 인증번호가 일치하면 회원가입 제출용 이메일 인증 JWT를 발급합니다."""
    try:
        verified_email = verify_email_code_challenge(body.challenge_token.strip(), body.code)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e
    proof = create_email_registration_verified_token(verified_email)
    return RegistrationEmailCodeVerifyResponse(email_verification_token=proof)


def _find_existing_user_by_school_and_student_id(
    db: Session, school_name: str, student_id: str
) -> User | None:
    """동일 학교 + 동일 학번 회원이 이미 존재하는지 확인.

    OCR 등 외부 입력은 공백/하이픈 등이 섞일 수 있으므로 normalize 후 비교합니다.
    """
    target = normalize_student_id(student_id)
    if not target:
        return None
    rows = (
        db.execute(
            select(User).where(
                User.school_name == school_name.strip(),
                User.student_id.is_not(None),
            )
        )
        .scalars()
        .all()
    )
    for u in rows:
        if u.student_id and normalize_student_id(u.student_id) == target:
            return u
    return None


@router.post("/verify-student-id", response_model=StudentIdVerifyResponse)
async def verify_student_id(
    name: str = Form(..., min_length=1, max_length=50),
    school_name: str = Form(..., min_length=1, max_length=100),
    student_id: str = Form(..., min_length=1, max_length=20),
    student_id_card: UploadFile = File(..., description="학생증 이미지"),
    db: Session = Depends(get_db),
) -> StudentIdVerifyResponse:
    """입력한 이름·학교명·학번이 학생증 OCR 결과에 포함되는지 검사하고,
    동일 학교·학번으로 이미 가입된 회원이 없는지 확인한 뒤 회원가입용 짧은 수명 토큰을 발급합니다.
    """
    if _find_existing_user_by_school_and_student_id(db, school_name, student_id) is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="해당 학교의 동일 학번으로 이미 가입된 계정이 있습니다.",
        )

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
        if not ocr_texts_contain_student_id(texts, student_id):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="학생증에서 입력하신 학번을 찾지 못했습니다. 학번이 카드에 적힌 그대로인지, 사진이 선명한지 확인해 주세요.",
            )

        token = create_student_id_verify_token(name, school_name, student_id, file_hash)
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
    student_id: str = Form(..., min_length=1, max_length=20),
    interest_major: str | None = Form(None),
    student_id_verification_token: str = Form(..., description="POST /verify-student-id 로 발급받은 토큰"),
    email_verification_token: str = Form(..., description="POST /registration-email/verify 로 발급받은 토큰"),
    student_id_card: UploadFile = File(..., description="학생증 이미지"),
    db: Session = Depends(get_db),
) -> RegisterResponse:
    raw = await student_id_card.read()
    if len(raw) == 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="빈 파일은 업로드할 수 없습니다.")
    file_hash = hashlib.sha256(raw).hexdigest()
    try:
        vn, vs, vsid, vh = decode_student_id_verify_token(student_id_verification_token)
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
    if normalize_student_id(vsid) != normalize_student_id(student_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="학번이 학생증 인증 당시와 일치하지 않습니다. 학생증 인증을 다시 진행해 주세요.",
        )

    try:
        verified_email = decode_email_registration_verified_token(email_verification_token.strip())
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e
    email_norm = email.strip().lower()
    if verified_email != email_norm:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="이메일 인증이 입력하신 이메일과 일치하지 않습니다. 이메일을 바꾼 경우 인증을 다시 진행해 주세요.",
        )

    school_name_stripped = school_name.strip()
    school_row = db.execute(
        select(School).where(School.name == school_name_stripped, School.is_active == True)  # noqa: E712
    ).scalar_one_or_none()
    if school_row is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="등록되지 않은 학교입니다. 가입 화면의 학교 목록에서 선택해 주세요.",
        )

    if _find_existing_user_by_school_and_student_id(db, school_name, student_id) is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="해당 학교의 동일 학번으로 이미 가입된 계정이 있습니다.",
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
        student_id=student_id.strip(),
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
