import hashlib
import hmac
import secrets
from datetime import UTC, datetime, timedelta

import bcrypt
from jose import JWTError, jwt

from config import settings

STUDENT_ID_VERIFY_PURPOSE = "student_id_verify"
EMAIL_CODE_CHALLENGE_PURPOSE = "email_reg_code"
EMAIL_REG_VERIFIED_PURPOSE = "email_reg_ok"
PASSWORD_RESET_PURPOSE = "pwd_reset"


def normalize_registration_email(email: str) -> str:
    return email.strip().lower()


def _email_code_hmac_key() -> bytes:
    return hashlib.sha256((settings.jwt_secret + "|HanuriEmailRegCode").encode("utf-8")).digest()


def create_email_code_challenge_token(normalized_email: str, code_four_digits: str) -> str:
    email = normalize_registration_email(normalized_email)
    digest = hmac.new(
        _email_code_hmac_key(),
        f"{email}\x00{code_four_digits}".encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()
    expire = datetime.now(UTC) + timedelta(minutes=5)
    payload = {
        "pur": EMAIL_CODE_CHALLENGE_PURPOSE,
        "e": email,
        "d": digest,
        "exp": expire,
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def verify_email_code_challenge(challenge_token: str, code_input: str) -> str:
    digits = "".join(c for c in code_input if c.isdigit())
    if len(digits) != 4:
        raise ValueError("인증번호 4자리를 입력해 주세요.")
    try:
        payload = jwt.decode(challenge_token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
    except JWTError as e:
        raise ValueError("인증 시간이 만료되었거나 유효하지 않습니다. 인증번호를 다시 받아 주세요.") from e
    if payload.get("pur") != EMAIL_CODE_CHALLENGE_PURPOSE:
        raise ValueError("유효하지 않은 이메일 인증 요청입니다.")
    email = payload.get("e")
    expected_d = payload.get("d")
    if not isinstance(email, str) or not isinstance(expected_d, str):
        raise ValueError("유효하지 않은 이메일 인증 요청입니다.")
    email = normalize_registration_email(email)
    digest = hmac.new(
        _email_code_hmac_key(),
        f"{email}\x00{digits}".encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()
    if not hmac.compare_digest(digest, expected_d):
        raise ValueError("인증번호가 일치하지 않습니다.")
    return email


def create_email_registration_verified_token(normalized_email: str) -> str:
    email = normalize_registration_email(normalized_email)
    expire = datetime.now(UTC) + timedelta(minutes=5)
    payload = {
        "pur": EMAIL_REG_VERIFIED_PURPOSE,
        "e": email,
        "exp": expire,
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def decode_email_registration_verified_token(token: str) -> str:
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
    except JWTError as e:
        raise ValueError("이메일 인증이 만료되었거나 유효하지 않습니다. 이메일 인증을 다시 진행해 주세요.") from e
    if payload.get("pur") != EMAIL_REG_VERIFIED_PURPOSE:
        raise ValueError("유효하지 않은 이메일 인증 토큰입니다.")
    e = payload.get("e")
    if not isinstance(e, str) or not e.strip():
        raise ValueError("유효하지 않은 이메일 인증 토큰입니다.")
    return normalize_registration_email(e)


def registration_email_verification_code() -> str:
    return f"{secrets.randbelow(10000):04d}"


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


def create_password_reset_token(user_id: str) -> str:
    """비밀번호 재설정 링크용 JWT (5분 유효)."""
    uid = user_id.strip()
    if not uid:
        raise ValueError("아이디가 비어 있습니다.")
    expire = datetime.now(UTC) + timedelta(minutes=5)
    payload = {
        "pur": PASSWORD_RESET_PURPOSE,
        "sub": uid,
        "exp": expire,
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def decode_password_reset_token(token: str) -> str:
    """비밀번호 재설정 JWT에서 user_id 반환. 만료·위조 시 ValueError."""
    try:
        payload = jwt.decode(token.strip(), settings.jwt_secret, algorithms=[settings.jwt_algorithm])
    except JWTError as e:
        raise ValueError(
            "재설정 링크가 만료되었거나 유효하지 않습니다. 비밀번호 찾기를 다시 요청해 주세요."
        ) from e
    if payload.get("pur") != PASSWORD_RESET_PURPOSE:
        raise ValueError("유효하지 않은 재설정 링크입니다.")
    sub = payload.get("sub")
    if not isinstance(sub, str) or not sub.strip():
        raise ValueError("유효하지 않은 재설정 링크입니다.")
    return sub.strip()
