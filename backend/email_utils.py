"""SMTP 기반 단순 메일 발송 유틸.

운영 환경에서는 `backend/.env` 에 `smtp_host`, `smtp_port`, `smtp_user`,
`smtp_password`, `smtp_from_email` 등을 설정하면 실제로 메일이 전송됩니다.
설정이 비어 있으면 전송은 생략하고 콘솔에 본문을 출력합니다(개발 편의).
"""

from __future__ import annotations

import logging
import smtplib
from email.message import EmailMessage

from config import settings

log = logging.getLogger(__name__)


def _smtp_configured() -> bool:
    return bool(settings.smtp_host and settings.smtp_from_email)


def send_email(to_email: str, subject: str, body: str) -> bool:
    """단순 텍스트 메일 전송. 실패해도 예외를 던지지 않고 False 반환."""
    if not to_email or not to_email.strip():
        return False
    to_email = to_email.strip()

    if not _smtp_configured():
        log.warning(
            "SMTP 미설정으로 메일을 콘솔에만 기록합니다. TO=%s SUBJECT=%s",
            to_email,
            subject,
        )
        print(
            "\n[EMAIL DRY-RUN] (SMTP 미설정)\n"
            f"  TO     : {to_email}\n"
            f"  SUBJECT: {subject}\n"
            f"  BODY   :\n{body}\n"
        )
        return False

    msg = EmailMessage()
    from_addr = (
        f"{settings.smtp_from_name} <{settings.smtp_from_email}>"
        if settings.smtp_from_name
        else settings.smtp_from_email
    )
    msg["From"] = from_addr
    msg["To"] = to_email
    msg["Subject"] = subject
    msg.set_content(body)

    try:
        if settings.smtp_use_tls:
            with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=15) as s:
                s.ehlo()
                s.starttls()
                if settings.smtp_user:
                    s.login(settings.smtp_user, settings.smtp_password or "")
                s.send_message(msg)
        else:
            with smtplib.SMTP_SSL(settings.smtp_host, settings.smtp_port, timeout=15) as s:
                if settings.smtp_user:
                    s.login(settings.smtp_user, settings.smtp_password or "")
                s.send_message(msg)
        log.info("메일 전송 완료 → %s (%s)", to_email, subject)
        return True
    except Exception as e:  # noqa: BLE001
        log.error("메일 전송 실패(TO=%s): %s", to_email, e)
        return False


def build_registration_rejected_email(
    name: str,
    school_name: str | None,
    reason: str | None,
) -> tuple[str, str]:
    """가입 거절 안내 메일 (제목, 본문) 생성."""
    subject = "[하누리] 회원가입이 거절되었습니다"
    school_part = f"{school_name} " if school_name else ""
    reason_block = ""
    if reason and reason.strip():
        reason_block = f"\n■ 거절 사유\n{reason.strip()}\n"

    register_url = settings.app_public_url.rstrip("/") + "/register"

    body = (
        f"안녕하세요, {name}님.\n\n"
        f"신청해 주신 {school_part}하누리 회원가입이 관리자 검토 결과 거절되어\n"
        f"해당 계정 정보가 삭제되었습니다.\n"
        f"{reason_block}\n"
        "■ 다시 가입하기\n"
        "  - 학생증 사진이 흐리거나 빛 반사가 있다면 선명하게 다시 촬영해 주세요.\n"
        "  - 이름·학교명·학번이 학생증에 표기된 그대로인지 확인해 주세요.\n"
        "  - 가입 페이지에서 새로 신청해 주시면 다시 검토해 드립니다.\n\n"
        f"가입 페이지: {register_url}\n\n"
        "본 메일은 발신 전용으로, 회신을 받지 않습니다.\n"
        "감사합니다.\n"
        "하누리 운영팀 드림\n"
    )
    return subject, body
