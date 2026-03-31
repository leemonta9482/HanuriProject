from datetime import UTC, datetime, timedelta

import bcrypt
from jose import JWTError, jwt

from config import settings


def hash_password(plain: str) -> str:
    return bcrypt.hashpw(plain.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))


def create_access_token(subject: str, *, is_admin: bool = False, token_version: int = 0) -> str:
    expire = datetime.now(UTC) + timedelta(minutes=settings.access_token_expire_minutes)
    payload = {
        "sub": subject,
        "exp": expire,
        "is_admin": is_admin,
        "tv": int(token_version),
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def decode_access_token(token: str) -> dict:
    return jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])


def decode_token_claims(token: str) -> tuple[str, int]:
    """JWT에서 user_id와 token_version(tv)을 꺼냅니다. tv가 없으면 0(구버전 토큰)으로 봅니다."""
    try:
        payload = decode_access_token(token)
    except JWTError as e:
        raise ValueError("유효하지 않은 토큰입니다.") from e
    sub = payload.get("sub")
    if not isinstance(sub, str) or not sub:
        raise ValueError("유효하지 않은 토큰입니다.")
    raw_tv = payload.get("tv")
    if raw_tv is None:
        tv = 0
    else:
        try:
            tv = int(raw_tv)
        except (TypeError, ValueError) as e:
            raise ValueError("유효하지 않은 토큰입니다.") from e
    return sub, tv


def verify_token_subject(token: str) -> str:
    """레거시 호환. tv 검증은 하지 않습니다."""
    user_id, _ = decode_token_claims(token)
    return user_id
