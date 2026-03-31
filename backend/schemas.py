from typing import Literal

from pydantic import BaseModel, Field


class UserLogin(BaseModel):
    user_id: str = Field(..., min_length=1, max_length=50)
    password: str = Field(..., min_length=1, max_length=128)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class RegisterResponse(BaseModel):
    user_id: str
    name: str
    message: str = "가입 신청이 접수되었습니다. 관리자 승인 후 로그인할 수 있습니다."


class LoginUserInfo(BaseModel):
    user_id: str
    name: str
    email: str
    is_admin: bool = False


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: LoginUserInfo


class AdminUserOut(BaseModel):
    user_id: str
    name: str
    school_name: str
    phone: str
    email: str
    student_id: str | None
    student_verified: bool
    manner_score: float
    trust_score: float
    interest_major: str | None
    account_status: str
    is_admin: bool
    registration_status: str
    student_id_card_path: str
    created_at: object | None = None
    updated_at: object | None = None

    model_config = {"from_attributes": True}


class AdminUserListResponse(BaseModel):
    items: list[AdminUserOut]
    total: int
    page: int
    page_size: int
    pages: int


class AdminUserUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=50)
    school_name: str | None = Field(None, min_length=1, max_length=100)
    phone: str | None = Field(None, min_length=1, max_length=20)
    email: str | None = Field(None, min_length=1, max_length=100)
    student_id: str | None = Field(None, max_length=20)
    interest_major: str | None = Field(None, max_length=100)
    manner_score: float | None = None
    trust_score: float | None = None
    student_verified: bool | None = None
    account_status: Literal["ACTIVE", "DORMANT", "DELETED"] | None = None
    registration_status: Literal["PENDING", "APPROVED", "REJECTED"] | None = None
    is_admin: bool | None = None


class AdminBoardOut(BaseModel):
    board_id: int
    user_id: str
    title: str
    price: int
    status: str
    trade_type: str
    created_at: object | None = None
    updated_at: object | None = None

    model_config = {"from_attributes": True}


class AdminBoardListResponse(BaseModel):
    items: list[AdminBoardOut]
    total: int
    page: int
    page_size: int
    pages: int
