from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import and_, desc, func, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from database import get_db
from deps import get_current_user
from models import Board, ChatMessage, ChatRoom, User, UserBlock, WantedPost
from realtime_events import publish_event
from routers.boards import _assert_same_school_board, _first_thumbnails
from schemas import (
    BlockUserCreate,
    ChatMessageOut,
    ChatMessagesResponse,
    ChatRoomClosedInfo,
    ChatRoomOpenOut,
    ChatRoomSummaryOut,
    OpenChatRoomRequest,
    SendChatMessageRequest,
    UserBlockEntryOut,
)
from user_notifications import upsert_chat_notification

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


def _peer_has_blocked_initiator(db: Session, peer_id: str, initiator_id: str) -> bool:
    row = db.scalar(
        select(UserBlock.id).where(
            UserBlock.blocker_id == peer_id,
            UserBlock.blocked_id == initiator_id,
        )
    )
    return row is not None


def _buyer_has_messaged(db: Session, room: ChatRoom) -> bool:
    """구매자(initiator)가 해당 방에 메시지를 보냈는지. 판매자에게 방을 보이게 하는 조건."""
    n = db.scalar(
        select(func.count(ChatMessage.message_id)).where(
            ChatMessage.room_id == room.room_id,
            ChatMessage.sender_id == room.initiator_id,
        )
    )
    return (n or 0) > 0


def _assert_peer_sees_room(db: Session, room: ChatRoom, user: User) -> None:
    """판매자(peer)는 구매자가 먼저 메시지를 보낸 방만 조회·채팅 가능."""
    if user.user_id != room.peer_id:
        return
    if not _buyer_has_messaged(db, room):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="채팅방을 찾을 수 없습니다.")


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
    last_at = last_msg.created_at if last_msg else None
    if room.closed_at:
        preview = "대화가 종료되었습니다."
        last_at = room.closed_at
    elif last_msg:
        preview = last_msg.body[:120] + ("…" if len(last_msg.body) > 120 else "")

    i_am_peer = viewer.user_id == room.peer_id
    initiator_blocked_by_me = False
    i_am_blocked_by_peer = False
    if i_am_peer:
        initiator_blocked_by_me = _peer_has_blocked_initiator(db, viewer.user_id, room.initiator_id)
    elif viewer.user_id == room.initiator_id:
        i_am_blocked_by_peer = _peer_has_blocked_initiator(db, room.peer_id, room.initiator_id)

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
        last_message_at=last_at,
        closed_at=room.closed_at,
        i_am_peer=i_am_peer,
        initiator_blocked_by_me=initiator_blocked_by_me,
        i_am_blocked_by_peer=i_am_blocked_by_peer,
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

    if _peer_has_blocked_initiator(db, peer_id, user.user_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="차단되었습니다. 이 판매자와는 대화를 시작할 수 없습니다.",
        )
    if _peer_has_blocked_initiator(db, user.user_id, peer_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="차단한 상대방과는 대화를 시작할 수 없습니다.",
        )

    existing = db.scalar(
        select(ChatRoom).where(
            ChatRoom.listing_kind == listing_kind,
            ChatRoom.listing_id == listing_id,
            ChatRoom.initiator_id == user.user_id,
            ChatRoom.closed_at.is_(None),
        )
    )
    if existing:
        if _peer_has_blocked_initiator(db, existing.peer_id, user.user_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="차단되었습니다. 이 판매자와는 대화를 시작할 수 없습니다.",
            )
        if _peer_has_blocked_initiator(db, user.user_id, existing.peer_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="차단한 상대방과는 대화를 시작할 수 없습니다.",
            )
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
    visible: list[ChatRoom] = []
    for r in rooms:
        if r.peer_id == user.user_id and not _buyer_has_messaged(db, r):
            continue
        visible.append(r)
    return [_room_summary(db, r, user) for r in visible]


@router.get("/blocks", response_model=list[UserBlockEntryOut])
def list_my_blocks(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> list[UserBlockEntryOut]:
    rows = db.execute(
        select(UserBlock, User.name)
        .join(User, UserBlock.blocked_id == User.user_id)
        .where(UserBlock.blocker_id == user.user_id)
        .order_by(desc(UserBlock.id))
    ).all()
    return [
        UserBlockEntryOut(
            blocked_user_id=ub.blocked_id,
            blocked_name=((name or "").strip() or ub.blocked_id) if isinstance(name, str) else ub.blocked_id,
            created_at=ub.created_at,
        )
        for ub, name in rows
    ]


@router.post("/blocks", response_model=UserBlockEntryOut)
def create_block(
    body: BlockUserCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> UserBlockEntryOut:
    blocked = body.blocked_user_id.strip()
    if blocked == user.user_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="자기 자신은 차단할 수 없습니다.")
    tgt = db.get(User, blocked)
    if tgt is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="사용자를 찾을 수 없습니다.")
    has_room = db.scalar(
        select(ChatRoom.room_id).where(
            ChatRoom.peer_id == user.user_id,
            ChatRoom.initiator_id == blocked,
        ).limit(1)
    )
    if has_room is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="대화를 받은 상대만 차단할 수 있습니다.",
        )
    ub = UserBlock(blocker_id=user.user_id, blocked_id=blocked)
    db.add(ub)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="이미 차단한 사용자입니다.",
        ) from None
    db.refresh(ub)
    room_ids = db.execute(
        select(ChatRoom.room_id).where(
            ChatRoom.peer_id == user.user_id,
            ChatRoom.initiator_id == blocked,
        )
    ).scalars().all()
    publish_event(
        blocked,
        {"type": "chat_blocked", "blocker_id": user.user_id, "room_ids": list(room_ids)},
    )
    return UserBlockEntryOut(
        blocked_user_id=blocked,
        blocked_name=((tgt.name or "").strip() or blocked),
        created_at=ub.created_at,
    )


@router.delete("/blocks/{blocked_user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_block(
    blocked_user_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> None:
    row = db.scalar(
        select(UserBlock).where(
            UserBlock.blocker_id == user.user_id,
            UserBlock.blocked_id == blocked_user_id,
        )
    )
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="차단 목록에 없습니다.")
    db.delete(row)
    db.commit()
    room_ids = db.execute(
        select(ChatRoom.room_id).where(
            ChatRoom.peer_id == user.user_id,
            ChatRoom.initiator_id == blocked_user_id,
        )
    ).scalars().all()
    publish_event(
        blocked_user_id,
        {"type": "chat_unblocked", "blocker_id": user.user_id, "room_ids": list(room_ids)},
    )


@router.post("/rooms/{room_id}/close")
def close_chat_room(
    room_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> dict[str, str | bool]:
    room = _assert_room_participant(db.get(ChatRoom, room_id), user)
    _assert_not_hidden(room, user.user_id)
    _assert_peer_sees_room(db, room, user)
    if room.closed_at is not None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="이미 종료된 대화입니다.")

    msg_count = (
        db.scalar(select(func.count(ChatMessage.message_id)).where(ChatMessage.room_id == room_id)) or 0
    )
    if msg_count == 0 and user.user_id == room.initiator_id:
        db.delete(room)
        db.commit()
        return {"ok": "true", "deleted": True}

    room.closed_at = datetime.now(UTC)
    db.commit()
    db.refresh(room)
    peer_id = _peer_user_id(room, user.user_id)
    closed_at_s = (
        room.closed_at.isoformat()
        if hasattr(room.closed_at, "isoformat")
        else str(room.closed_at)
    )
    publish_event(
        peer_id,
        {
            "type": "chat_room_closed",
            "room_id": room_id,
            "closed_at": closed_at_s,
        },
    )
    return {"ok": "true", "deleted": False}


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
    _assert_peer_sees_room(db, room, user)

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
    room_closed: ChatRoomClosedInfo | None = None
    if room.closed_at:
        room_closed = ChatRoomClosedInfo()
    return ChatMessagesResponse(
        messages=[
            ChatMessageOut(
                message_id=m.message_id,
                sender_id=m.sender_id,
                body=m.body,
                created_at=m.created_at,
            )
            for m in rows
        ],
        room_closed=room_closed,
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
    _assert_peer_sees_room(db, room, user)
    if room.closed_at is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="종료된 채팅방에는 메시지를 보낼 수 없습니다.",
        )
    if _peer_has_blocked_initiator(db, room.peer_id, room.initiator_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="차단된 대화방입니다. 메시지를 보낼 수 없습니다.",
        )

    msg = ChatMessage(room_id=room_id, sender_id=user.user_id, body=body.body.strip())
    db.add(msg)
    room.last_message_at = datetime.now(UTC)
    peer_id = _peer_user_id(room, user.user_id)
    sender = db.get(User, user.user_id)
    sender_name = ((sender.name or "").strip() or user.user_id) if sender else user.user_id
    preview = msg.body
    if len(preview) > 120:
        preview = preview[:119] + "…"
    upsert_chat_notification(
        db,
        recipient_id=peer_id,
        room_id=room_id,
        title="새 채팅",
        body=f"{sender_name}: {preview}",
    )
    db.commit()
    db.refresh(msg)
    out = ChatMessageOut(
        message_id=msg.message_id,
        sender_id=msg.sender_id,
        body=msg.body,
        created_at=msg.created_at,
    )
    publish_event(
        peer_id,
        {
            "type": "chat",
            "room_id": room_id,
            "title": "새 채팅",
            "body": f"{sender_name}: {preview}",
            "message": out.model_dump(mode="json"),
        },
    )
    return out
