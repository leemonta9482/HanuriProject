from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from database import get_db
from deps import get_current_user
from models import User
from schemas import LoginResponse, LoginUserInfo, RegisterResponse, UserLogin
from security import create_access_token, hash_password, verify_password
from upload_storage import delete_uploaded_file, save_student_id_card

router = APIRouter(prefix="/api/auth", tags=["auth"])


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
    student_id_card: UploadFile = File(..., description="학생증 이미지"),
    db: Session = Depends(get_db),
) -> RegisterResponse:
    relative_path = await save_student_id_card(student_id_card)
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
            is_admin=user.is_admin,
        ),
    )


@router.get("/me", response_model=LoginUserInfo)
def get_me(user: User = Depends(get_current_user)) -> LoginUserInfo:
    return LoginUserInfo(
        user_id=user.user_id,
        name=user.name,
        email=user.email,
        is_admin=user.is_admin,
    )
