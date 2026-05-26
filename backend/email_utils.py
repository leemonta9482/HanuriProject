"""SMTP 기반 단순 메일 발송 유틸.

운영 환경에서는 `backend/.env` 에 `smtp_host`, `smtp_port`, `smtp_user`,
`smtp_password`, `smtp_from_email` 등을 설정하면 실제로 메일이 전송됩니다.
설정이 비어 있으면 전송은 생략하고 콘솔에 본문을 출력합니다(개발 편의).
"""

from __future__ import annotations

import logging
import smtplib
from email.message import EmailMessage
from html import escape

from config import settings

log = logging.getLogger(__name__)


def _smtp_configured() -> bool:
    return bool(settings.smtp_host and settings.smtp_from_email)


def send_email(to_email: str, subject: str, body: str, *, html_body: str | None = None) -> bool:
    """메일 전송. `html_body`가 있으면 multipart/alternative(plain + HTML). 실패 시 False."""
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
            f"  PLAIN  :\n{body}\n"
            + (
                f"  HTML   :\n{html_body}\n"
                if html_body
                else ""
            ),
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
    if html_body:
        msg.add_alternative(html_body, subtype="html")

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


def build_registration_email_code_message(code: str) -> tuple[str, str]:
    """회원가입 이메일 인증(4자리) — (제목, 본문)."""
    subject = "[하누리] 회원가입 이메일 인증번호"
    body = (
        f"인증번호: {code}\n\n"
        "회원가입 화면에 위 4자리 번호를 5분 이내에 입력해 주세요.\n"
        "본인이 요청하지 않았다면 이 메일을 무시하셔도 됩니다.\n\n"
        "본 메일은 발신 전용입니다.\n"
        "하누리 운영팀\n"
    )
    return subject, body


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


def build_password_reset_email(
    reset_url: str,
    user_id_display: str,
    *,
    valid_minutes: int = 5,
) -> tuple[str, str, str]:
    """비밀번호 재설정 메일 — (제목, plain, html). HTML에는 버튼형 링크."""
    subject = "[하누리] 비밀번호 재설정 안내"
    uid_plain = user_id_display
    url_html = escape(reset_url, quote=True)
    uid_html = escape(user_id_display, quote=True)

    body = (
        f"안녕하세요.\n\n"
        f"아이디 「{uid_plain}」 계정의 비밀번호 재설정을 요청하셨다면,\n"
        "지원하는 메일 앱에서는 ‘비밀번호 재설정’ 버튼으로 이동할 수 있습니다.\n"
        f"■ 링크 유효 시간: 발송 후 {valid_minutes}분 (만료 후에는 다시 ‘비밀번호 찾기’를 이용해 주세요.)\n\n"
        "─── 아래 주소는 일부 환경(텍스트 전용)에서만 필요합니다 ───\n"
        f"{reset_url}\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "⚠ 본인이 요청한 적이 없다면\n"
        "   링크를 열거나 버튼을 누르지 마시고 이 메일을 무시·삭제해 주세요.\n"
        "   계정 도용 시도일 수 있습니다.\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "본 메일은 발신 전용입니다.\n"
        "하누리 운영팀\n"
    )

    # 인라인 스타일: Gmail·Apple Mail 등에서 버튼처럼 보이게
    html = f"""<!DOCTYPE html>
<html lang="ko">
<head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"></head>
<body style="margin:0;padding:24px;background:#f6f7f8;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;line-height:1.6;color:#222;">
  <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="max-width:560px;margin:0 auto;">
    <tr><td style="background:#fff;border-radius:12px;padding:28px 24px;border:1px solid #e8eaeb;">
      <p style="margin:0 0 16px;">안녕하세요.</p>
      <p style="margin:0 0 12px;">아이디 「{uid_html}」 계정의 비밀번호 재설정을 요청하셨다면, 아래 버튼을 눌러 새 비밀번호를 설정해 주세요.</p>
      <p style="margin:0 0 20px;font-size:14px;color:#555;">링크 유효 시간: 발송 후 <strong>{valid_minutes}분</strong> (만료 후에는 다시 ‘비밀번호 찾기’를 이용해 주세요.)</p>
      <table role="presentation" cellspacing="0" cellpadding="0" style="margin:24px 0;">
        <tr>
          <td style="border-radius:8px;background:#3d9a9e;">
            <a href="{url_html}" style="display:inline-block;padding:14px 32px;color:#ffffff;text-decoration:none;font-weight:600;font-size:15px;">비밀번호 재설정</a>
          </td>
        </tr>
      </table>
      <p style="margin:16px 0 0;font-size:12px;color:#888;">
        <a href="{url_html}" style="color:#5c6b70;">링크가 열리지 않으면 여기를 눌러 주세요.</a>
      </p>
      <hr style="border:none;border-top:1px solid #e8eaeb;margin:24px 0;" />
      <p style="margin:0;font-size:14px;color:#a93030;">⚠ 본인이 요청한 적이 <strong>없다면</strong> 버튼·링크를 누르지 마시고 이 메일을 무시·삭제해 주세요. 계정 도용 시도일 수 있습니다.</p>
      <p style="margin:20px 0 0;font-size:12px;color:#888;">본 메일은 발신 전용입니다.<br/>하누리 운영팀</p>
    </td></tr>
  </table>
</body>
</html>"""

    return subject, body, html
