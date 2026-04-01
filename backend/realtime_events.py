"""메모리 기반 사용자별 이벤트 큐(SSE 푸시용). DB 테이블 없음. 단일 프로세스 전제."""

from __future__ import annotations

import asyncio
import json
import queue
from collections import defaultdict
from typing import Any

from fastapi import Request

_subscribers: dict[str, list[queue.Queue[dict[str, Any]]]] = defaultdict(list)


def subscribe(user_id: str) -> queue.Queue[dict[str, Any]]:
    q: queue.Queue[dict[str, Any]] = queue.Queue(maxsize=256)
    _subscribers[user_id].append(q)
    return q


def unsubscribe(user_id: str, q: queue.Queue[dict[str, Any]]) -> None:
    lst = _subscribers.get(user_id)
    if not lst:
        return
    try:
        lst.remove(q)
    except ValueError:
        pass


def publish_event(user_id: str, payload: dict[str, Any]) -> None:
    for q in list(_subscribers.get(user_id, [])):
        try:
            q.put_nowait(payload)
        except queue.Full:
            pass


def _event_wait(q: queue.Queue[dict[str, Any]], timeout: float) -> dict[str, Any] | None:
    try:
        return q.get(timeout=timeout)
    except queue.Empty:
        return None


# 대기 시간이 길면 서버 reload 시 to_thread가 끝날 때까지 종료가 지연됨 → 짧게 유지
_SSE_POLL_SEC = 2.5


async def sse_event_generator(user_id: str, request: Request):
    q = subscribe(user_id)
    try:
        yield f"data: {json.dumps({'type': 'connected'}, ensure_ascii=False)}\n\n"
        while True:
            if await request.is_disconnected():
                break
            item = await asyncio.to_thread(_event_wait, q, _SSE_POLL_SEC)
            if item is None:
                yield f"data: {json.dumps({'type': 'ping'}, ensure_ascii=False)}\n\n"
            else:
                yield f"data: {json.dumps(item, ensure_ascii=False)}\n\n"
    finally:
        unsubscribe(user_id, q)
