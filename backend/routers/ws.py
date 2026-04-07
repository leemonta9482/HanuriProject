import asyncio

from fastapi import APIRouter, Query, WebSocket, WebSocketDisconnect

from database import SessionLocal
from models import User
from realtime_events import register_ws, unregister_ws
from security import decode_token_claims

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


@router.websocket("/api/ws")
async def websocket_live(
    websocket: WebSocket,
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
    finally:
        db.close()

    register_ws(user_id, websocket)
    await websocket.send_json({"type": "connected"})
    hb = asyncio.create_task(_heartbeat(websocket))
    try:
        while True:
            try:
                raw = await websocket.receive_text()
            except WebSocketDisconnect:
                break
            if raw.strip().lower() == "ping":
                await websocket.send_json({"type": "pong"})
    finally:
        hb.cancel()
        try:
            await hb
        except asyncio.CancelledError:
            pass
        unregister_ws(user_id, websocket)
