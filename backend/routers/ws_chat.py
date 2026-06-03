import asyncio
import json
from datetime import UTC, datetime

from fastapi import APIRouter, Query, WebSocket, WebSocketDisconnect
from sqlalchemy import select

from database import SessionLocal
from models import ChatMessage, ChatRoom, User, UserBlock
from realtime_events import broadcast_chat, publish_event, register_chat_ws, unregister_chat_ws
from security import decode_token_claims
from user_notifications import upsert_chat_notification

router = APIRouter(tags=["websocket"])


async def _heartbeat(ws: WebSocket) -> None:
    try:
        while True:
            await asyncio.sleep(25)
            await ws.send_json({"type": "ping"})
    except asyncio.CancelledError:
        raise
    except Exception:
        pass


@router.websocket("/api/ws/chat/{room_id}")
async def websocket_chat(
    websocket: WebSocket,
    room_id: int,
    token: str | None = Query(None),
) -> None:
    await websocket.accept()

    if not token:
        await websocket.send_json({"type": "error", "detail": "token_required"})
        await websocket.close(code=4000)
        return

    try:
        user_id, tv = decode_token_claims(token)
    except ValueError:
        await websocket.send_json({"type": "error", "detail": "invalid_token"})
        await websocket.close(code=4000)
        return

    db = SessionLocal()
    try:
        user = db.get(User, user_id)
        if user is None or tv != user.token_version:
            await websocket.send_json({"type": "error", "detail": "unauthorized"})
            await websocket.close(code=4000)
            return

        room = db.get(ChatRoom, room_id)
        if room is None or user_id not in (room.initiator_id, room.peer_id):
            await websocket.send_json({"type": "error", "detail": "room_not_found"})
            await websocket.close(code=4003)
            return

        peer_id = room.peer_id if room.initiator_id == user_id else room.initiator_id
    finally:
        db.close()

    register_chat_ws(room_id, websocket)
    await websocket.send_json({"type": "connected"})
    hb = asyncio.create_task(_heartbeat(websocket))

    try:
        while True:
            try:
                raw = await websocket.receive_text()
            except WebSocketDisconnect:
                break

            try:
                data = json.loads(raw)
            except json.JSONDecodeError:
                await websocket.send_json({"type": "error", "detail": "invalid_json"})
                continue

            if data.get("type") == "ping":
                await websocket.send_json({"type": "pong"})
                continue

            if data.get("type") != "message":
                continue

            body = str(data.get("body", "")).strip()
            if not body:
                await websocket.send_json({"type": "error", "detail": "empty_message"})
                continue
            if len(body) > 2000:
                await websocket.send_json({"type": "error", "detail": "message_too_long"})
                continue

            db = SessionLocal()
            try:
                room = db.get(ChatRoom, room_id)
                if room is None or room.closed_at is not None:
                    await websocket.send_json({"type": "error", "detail": "room_closed"})
                    continue

                blocked = db.scalar(
                    select(UserBlock.id).where(
                        UserBlock.blocker_id == peer_id,
                        UserBlock.blocked_id == user_id,
                    )
                )
                if blocked is not None:
                    await websocket.send_json({"type": "error", "detail": "blocked"})
                    continue

                msg = ChatMessage(room_id=room_id, sender_id=user_id, body=body)
                db.add(msg)
                room.last_message_at = datetime.now(UTC)

                sender = db.get(User, user_id)
                sender_name = ((sender.name or "").strip() or user_id) if sender else user_id
                preview = body if len(body) <= 120 else body[:119] + "…"

                upsert_chat_notification(
                    db,
                    recipient_id=peer_id,
                    room_id=room_id,
                    title="새 채팅",
                    body=f"{sender_name}: {preview}",
                )
                db.commit()
                db.refresh(msg)

                created_at_s = (
                    msg.created_at.isoformat()
                    if hasattr(msg.created_at, "isoformat")
                    else str(msg.created_at)
                )
                out = {
                    "type": "message",
                    "message_id": msg.message_id,
                    "sender_id": msg.sender_id,
                    "body": msg.body,
                    "created_at": created_at_s,
                }

                await broadcast_chat(room_id, out)

                publish_event(
                    peer_id,
                    {
                        "type": "chat",
                        "room_id": room_id,
                        "title": "새 채팅",
                        "body": f"{sender_name}: {preview}",
                        "message": out,
                    },
                )
            finally:
                db.close()
    finally:
        hb.cancel()
        try:
            await hb
        except asyncio.CancelledError:
            pass
        unregister_chat_ws(room_id, websocket)
