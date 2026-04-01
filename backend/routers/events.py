from fastapi import APIRouter, Depends, Request
from fastapi.responses import StreamingResponse

from deps import get_current_user
from models import User
from realtime_events import sse_event_generator

router = APIRouter(prefix="/api/events", tags=["events"])


@router.get("/stream")
async def stream_events(
    request: Request,
    user: User = Depends(get_current_user),
) -> StreamingResponse:
    return StreamingResponse(
        sse_event_generator(user.user_id, request),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
