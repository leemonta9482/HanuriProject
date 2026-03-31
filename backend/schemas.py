from pydantic import BaseModel, EmailStr, Field


class UserRegister(BaseModel):
    user_id: str = Field(..., min_length=1, max_length=50)
    password: str = Field(..., min_length=8, max_length=128)
    name: str = Field(..., min_length=1, max_length=50)
    phone: str = Field(..., min_length=1, max_length=20)
    email: EmailStr
    student_id: str | None = Field(None, max_length=20)
    interest_major: str | None = Field(None, max_length=100)


class UserLogin(BaseModel):
    user_id: str = Field(..., min_length=1, max_length=50)
    password: str = Field(..., min_length=1, max_length=128)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class RegisterResponse(BaseModel):
    user_id: str
    name: str
    message: str = "회원가입이 완료되었습니다."


class LoginUserInfo(BaseModel):
    user_id: str
    name: str
    email: str


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: LoginUserInfo
