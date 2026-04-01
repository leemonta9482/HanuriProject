from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import and_, desc, func, or_, select
from sqlalchemy.orm import Session

from database import get_db
from deps import get_current_user
from models import Board, ChatMessage, ChatRoom, User, WantedPost
from realtime_events import publish_event
from routers.boards import _assert_same_school_board, _first_thumbnails
from schemas import (
    ChatMessageOut,
    ChatMessagesResponse,
    ChatRoomOpenOut,
    ChatRoomSummaryOut,
    OpenChatRoomRequest,
    SendChatMessageRequest,
)

router = APIRouter(prefix="/api/chat", tags=["chat"])


def _assert_same_school_wanted(db: Session, w: WantedPost, user: User) -> None:
    if user.is_admin:
        return
    author = db.get(User, w.user_id)
    if author is None or author.school_name != user.school_name:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="구매 희망글을 찾을 수 없습니다.")


def _peer_user_id(room: ChatRoom, me: str) -> str:
    return room.peer_id if room.initiator_id == me else room.initiator_id


def _participant_not_hidden(room: ChatRoom, user_id: str) -> bool:
    if room.initiator_id == user_id:
        return room.deleted_at_initiator is None
    if room.peer_id == user_id:
        return room.deleted_at_peer is None
    return False


def _assert_room_participant(room: ChatRoom | None, user: User) -> ChatRoom:
    if room is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="채팅방을 찾을 수 없습니다.")
    if user.user_id not in (room.initiator_id, room.peer_id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="접근할 수 없습니다.")
    return room


def _assert_not_hidden(room: ChatRoom, user_id: str) -> None:
    if not _participant_not_hidden(room, user_id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="목록에서 삭제한 대화입니다.")


def _restore_if_deleted(db: Session, room: ChatRoom, user_id: str) -> None:
    if room.initiator_id == user_id and room.deleted_at_initiator is not None:
        room.deleted_at_initiator = None
        db.commit()
        db.refresh(room)
    elif room.peer_id == user_id and room.deleted_at_peer is not None:
        room.deleted_at_peer = None
        db.commit()
        db.refresh(room)


def _listing_kind_api(db_kind: str) -> str:
    return "board" if db_kind == "BOARD" else "wanted"


def _room_summary(
    db: Session,
    room: ChatRoom,
    viewer: User,
) -> ChatRoomSummaryOut:
    peer_id = _peer_user_id(room, viewer.user_id)
    peer = db.get(User, peer_id)
    peer_name = ((peer.name or "").strip() or "회원") if peer else peer_id

    title = ""
    price: int | None = None
    thumb: str | None = None
    if room.listing_kind == "BOARD":
        b = db.get(Board, room.listing_id)
        if b:
            title = b.title
            price = b.price
            thumbs = _first_thumbnails(db, [b.board_id])
            thumb = thumbs.get(b.board_id)
    else:
        w = db.get(WantedPost, room.listing_id)
        if w:
            title = w.title
            price = w.max_price

    last_msg = db.execute(
        select(ChatMessage)
        .where(ChatMessage.room_id == room.room_id)
        .order_by(desc(ChatMessage.message_id))
        .limit(1)
    ).scalar_one_or_none()
    preview = None
    if last_msg:
        preview = last_msg.body[:120] + ("…" if len(last_msg.body) > 120 else "")

    return ChatRoomSummaryOut(
        room_id=room.room_id,
        listing_kind=_listing_kind_api(room.listing_kind),  # type: ignore[arg-type]
        listing_id=room.listing_id,
        peer_user_id=peer_id,
        peer_name=peer_name,
        listing_title=title or "(삭제된 글)",
        listing_price=price,
        thumbnail_path=thumb,
        last_message_preview=preview,
        last_message_at=last_msg.created_at if last_msg else None,
        closed_at=room.closed_at,
    )


@router.post("/rooms/open", response_model=ChatRoomOpenOut)
def open_chat_room(
    body: OpenChatRoomRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> ChatRoomOpenOut:
    if body.kind == "board":
        if body.board_id is None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="board_id가 필요합니다.")
        board = db.get(Board, body.board_id)
        if board is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="게시글을 찾을 수 없습니다.")
        _assert_same_school_board(db, board, user)
        if board.user_id == user.user_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="본인 판매글에는 채팅을 시작할 수 없습니다.",
            )
        peer_id = board.user_id
        listing_kind = "BOARD"
        listing_id = board.board_id
    elif body.kind == "wanted":
        if body.wanted_id is None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="wanted_id가 필요합니다.")
        w = db.get(WantedPost, body.wanted_id)
        if w is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="구매 희망글을 찾을 수 없습니다.")
        _assert_same_school_wanted(db, w, user)
        if w.user_id == user.user_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="본인 구매 희망글에는 채팅을 시작할 수 없습니다.",
            )
        peer_id = w.user_id
        listing_kind = "WANTED"
        listing_id = w.wanted_id
    else:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="kind가 올바르지 않습니다.")

    existing = db.scalar(
        select(ChatRoom).where(
            ChatRoom.listing_kind == listing_kind,
            ChatRoom.listing_id == listing_id,
            ChatRoom.initiator_id == user.user_id,
            ChatRoom.closed_at.is_(None),
        )
    )
    if existing:
        if existing.deleted_at_initiator is not None:
            existing.deleted_at_initiator = None
            db.commit()
            db.refresh(existing)
        return ChatRoomOpenOut(room_id=existing.room_id)

    room = ChatRoom(
        listing_kind=listing_kind,
        listing_id=listing_id,
        initiator_id=user.user_id,
        peer_id=peer_id,
    )
    db.add(room)
    db.commit()
    db.refresh(room)
    return ChatRoomOpenOut(room_id=room.room_id)


@router.get("/rooms", response_model=list[ChatRoomSummaryOut])
def list_my_chat_rooms(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> list[ChatRoomSummaryOut]:
    rooms = (
        db.execute(
            select(ChatRoom)
            .where(
                or_(
                    and_(ChatRoom.initiator_id == user.user_id, ChatRoom.deleted_at_initiator.is_(None)),
                    and_(ChatRoom.peer_id == user.user_id, ChatRoom.deleted_at_peer.is_(None)),
                )
            )
            .order_by(desc(func.coalesce(ChatRoom.last_message_at, ChatRoom.created_at)))
        )
        .scalars()
        .all()
    )
    return [_room_summary(db, r, user) for r in rooms]


@router.post("/rooms/{room_id}/close")
def close_chat_room(
    room_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> dict[str, str]:
    room = _assert_room_participant(db.get(ChatRoom, room_id), user)
    _assert_not_hidden(room, user.user_id)
    if room.closed_at is not None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="이미 종료된 대화입니다.")
    room.closed_at = datetime.now(UTC)
    db.commit()
    return {"ok": "true"}


@router.delete("/rooms/{room_id}")
def delete_chat_room(
    room_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> dict[str, str]:
    room = _assert_room_participant(db.get(ChatRoom, room_id), user)
    if room.closed_at is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="종료된 대화방만 삭제할 수 있습니다. 먼저 대화 끊기를 해 주세요.",
        )
    if room.initiator_id == user.user_id:
        if room.deleted_at_initiator is not None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="이미 삭제한 대화입니다.")
        room.deleted_at_initiator = datetime.now(UTC)
    else:
        if room.deleted_at_peer is not None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="이미 삭제한 대화입니다.")
        room.deleted_at_peer = datetime.now(UTC)
    if room.deleted_at_initiator is not None and room.deleted_at_peer is not None:
        db.delete(room)
    db.commit()
    return {"ok": "true"}


@router.get("/rooms/{room_id}/messages", response_model=ChatMessagesResponse)
def list_messages(
    room_id: int,
    after_id: int | None = Query(None, ge=1),
    limit: int = Query(100, ge=1, le=200),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> ChatMessagesResponse:
    room = _assert_room_participant(db.get(ChatRoom, room_id), user)
    _restore_if_deleted(db, room, user.user_id)

    if after_id is None:
        rows = db.execute(
            select(ChatMessage)
            .where(ChatMessage.room_id == room_id)
            .order_by(desc(ChatMessage.message_id))
            .limit(limit)
        ).scalars().all()
        rows = list(reversed(rows))
    else:
        rows = db.execute(
            select(ChatMessage)
            .where(ChatMessage.room_id == room_id, ChatMessage.message_id > after_id)
            .order_by(ChatMessage.message_id)
            .limit(limit)
        ).scalars().all()
    return ChatMessagesResponse(
        messages=[
            ChatMessageOut(
                message_id=m.message_id,
                sender_id=m.sender_id,
                body=m.body,
                created_at=m.created_at,
            )
            for m in rows
        ]
    )


@router.post("/rooms/{room_id}/messages", response_model=ChatMessageOut)
def send_message(
    room_id: int,
    body: SendChatMessageRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> ChatMessageOut:
    room = _assert_room_participant(db.get(ChatRoom, room_id), user)
    _restore_if_deleted(db, room, user.user_id)
    if room.closed_at is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="종료된 채팅방에는 메시지를 보낼 수 없습니다.",
        )

    msg = ChatMessage(room_id=room_id, sender_id=user.user_id, body=body.body.strip())
    db.add(msg)
    room.last_message_at = datetime.now(UTC)
    db.commit()
    db.refresh(msg)
    peer_id = _peer_user_id(room, user.user_id)
    sender = db.get(User, user.user_id)
    sender_name = ((sender.name or "").strip() or user.user_id) if sender else user.user_id
    preview = msg.body
    if len(preview) > 120:
        preview = preview[:119] + "…"
    publish_event(
        peer_id,
        {
            "type": "chat",
            "room_id": room_id,
            "title": "새 채팅",
            "body": f"{sender_name}: {preview}",
        },
    )
    return ChatMessageOut(
        message_id=msg.message_id,
        sender_id=msg.sender_id,
        body=msg.body,
        created_at=msg.created_at,
    )
