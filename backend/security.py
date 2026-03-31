from datetime import UTC, datetime, timedelta

import bcrypt
from jose import JWTError, jwt

from config import settings


def hash_password(plain: str) -> str:
    return bcrypt.hashpw(plain.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))


def create_access_token(subject: str, *, is_admin: bool = False) -> str:
    expire = datetime.now(UTC) + timedelta(minutes=settings.access_token_expire_minutes)
    payload = {"sub": subject, "exp": expire, "is_admin": is_admin}
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def decode_access_token(token: str) -> dict:
    return jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])


def verify_token_subject(token: str) -> str:
    try:
        payload = decode_access_token(token)
        sub = payload.get("sub")
        if not isinstance(sub, str) or not sub:
            raise JWTError("invalid sub")
        return sub
    except JWTError as e:
        raise ValueError("유효하지 않은 토큰입니다.") from e
