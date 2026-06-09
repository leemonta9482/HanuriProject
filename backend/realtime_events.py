"""사용자별 WebSocket 연결. 동기 라우트에서 publish_event 시 스레드 안전 큐로 async 브로드캐스트."""

from __future__ import annotations

import asyncio
import queue
from collections import defaultdict
from typing import Any

from starlette.websockets import WebSocket

_connections: dict[str, list[WebSocket]] = defaultdict(list)
_pending: queue.Queue[tuple[str, dict[str, Any]]] = queue.Queue()


def register_ws(user_id: str, ws: WebSocket) -> None:
    _connections[user_id].append(ws)


def unregister_ws(user_id: str, ws: WebSocket) -> None:
    lst = _connections.get(user_id)
    if not lst:
        return
    try:
        lst.remove(ws)
    except ValueError:
        pass
    if not lst:
        _connections.pop(user_id, None)


def publish_event(user_id: str, payload: dict[str, Any]) -> None:
    _pending.put((user_id, payload))


def _get_pending_item() -> tuple[str, dict[str, Any]] | None:
    try:
        return _pending.get(timeout=0.5)
    except queue.Empty:
        return None


async def _broadcast(user_id: str, payload: dict[str, Any]) -> None:
    conns = list(_connections.get(user_id, []))
    dead: list[WebSocket] = []
    for ws in conns:
        try:
            await ws.send_json(payload)
        except Exception:
            dead.append(ws)
    for ws in dead:
        unregister_ws(user_id, ws)


async def process_pending_loop() -> None:
    while True:
        item = await asyncio.to_thread(_get_pending_item)
        if item is None:
            await asyncio.sleep(0)
            continue
        uid, payload = item
        await _broadcast(uid, payload)


_chat_connections: dict[int, list[WebSocket]] = defaultdict(list)


def register_chat_ws(room_id: int, ws: WebSocket) -> None:
    _chat_connections[room_id].append(ws)


def unregister_chat_ws(room_id: int, ws: WebSocket) -> None:
    lst = _chat_connections.get(room_id)
    if not lst:
        return
    try:
        lst.remove(ws)
    except ValueError:
        pass
    if not lst:
        _chat_connections.pop(room_id, None)


async def broadcast_chat(room_id: int, payload: dict[str, Any]) -> None:
    conns = list(_chat_connections.get(room_id, []))
    dead: list[WebSocket] = []
    for ws in conns:
        try:
            await ws.send_json(payload)
        except Exception:
            dead.append(ws)
    for ws in dead:
        unregister_chat_ws(room_id, ws)
