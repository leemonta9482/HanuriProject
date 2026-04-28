from datetime import UTC, datetime, timedelta

import bcrypt
from jose import JWTError, jwt

from config import settings

STUDENT_ID_VERIFY_PURPOSE = "student_id_verify"


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


def create_student_id_verify_token(
    name: str,
    school_name: str,
    student_id: str,
    file_sha256_hex: str,
) -> str:
    """학생증 OCR 인증 성공 후, 회원가입 시 동일 이미지·이름·학교·학번 검증용 짧은 수명 JWT."""
    expire = datetime.now(UTC) + timedelta(minutes=20)
    payload = {
        "pur": STUDENT_ID_VERIFY_PURPOSE,
        "n": name.strip(),
        "s": school_name.strip(),
        "sid": student_id.strip(),
        "h": file_sha256_hex,
        "exp": expire,
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def decode_student_id_verify_token(token: str) -> tuple[str, str, str, str]:
    """(name, school_name, student_id, file_sha256_hex) 반환."""
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
    except JWTError as e:
        raise ValueError("학생증 인증이 만료되었거나 유효하지 않습니다. 다시 인증해 주세요.") from e
    if payload.get("pur") != STUDENT_ID_VERIFY_PURPOSE:
        raise ValueError("유효하지 않은 학생증 인증 토큰입니다.")
    n = payload.get("n")
    s = payload.get("s")
    sid = payload.get("sid")
    h = payload.get("h")
    if (
        not isinstance(n, str)
        or not isinstance(s, str)
        or not isinstance(sid, str)
        or not isinstance(h, str)
    ):
        raise ValueError("유효하지 않은 학생증 인증 토큰입니다.")
    return n.strip(), s.strip(), sid.strip(), h.strip()
