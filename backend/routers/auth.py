from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from database import get_db
from models import User
from schemas import LoginResponse, LoginUserInfo, RegisterResponse, UserLogin, UserRegister
from security import create_access_token, hash_password, verify_password

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/register", response_model=RegisterResponse)
def register(body: UserRegister, db: Session = Depends(get_db)) -> RegisterResponse:
    user = User(
        user_id=body.user_id.strip(),
        password=hash_password(body.password),
        name=body.name.strip(),
        phone=body.phone.strip(),
        email=str(body.email).strip().lower(),
        student_id=body.student_id.strip() if body.student_id else None,
        interest_major=body.interest_major.strip() if body.interest_major else None,
    )
    db.add(user)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="이미 사용 중인 아이디, 전화번호 또는 이메일입니다.",
        ) from None
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
    token = create_access_token(user.user_id)
    return LoginResponse(
        access_token=token,
        token_type="bearer",
        user=LoginUserInfo(user_id=user.user_id, name=user.name, email=user.email),
    )
