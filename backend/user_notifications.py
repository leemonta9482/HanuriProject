"""사용자 알림(채팅·찜) DB 기록 — WebSocket과 별개로 오프라인 수신자에게도 유지."""

from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from models import UserNotification


def upsert_chat_notification(
    db: Session,
    *,
    recipient_id: str,
    room_id: int,
    title: str,
    body: str,
) -> None:
    """같은 방 채팅 알림은 한 줄로 유지하고, 새 메시지 시 미읽음으로 되돌림."""
    row = db.scalars(
        select(UserNotification).where(
            UserNotification.user_id == recipient_id.strip(),
            UserNotification.kind == "CHAT_MESSAGE",
            UserNotification.room_id == room_id,
        ),
    ).first()
    now = datetime.now(UTC).replace(tzinfo=None)
    if row:
        row.title = title.strip()[:200]
        row.body = body.strip()
        row.created_at = now
        row.read_at = None
    else:
        db.add(
            UserNotification(
                user_id=recipient_id.strip(),
                kind="CHAT_MESSAGE",
                room_id=room_id,
                board_id=None,
                title=title.strip()[:200],
                body=body.strip(),
                read_at=None,
            ),
        )


def insert_favorite_notification(
    db: Session,
    *,
    seller_id: str,
    board_id: int,
    title: str,
    body: str,
) -> None:
    db.add(
        UserNotification(
            user_id=seller_id.strip(),
            kind="BOARD_FAVORITED",
            room_id=None,
            board_id=board_id,
            title=title.strip()[:200],
            body=body.strip(),
            read_at=None,
        ),
    )
