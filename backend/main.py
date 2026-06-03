from contextlib import asynccontextmanager

import asyncio

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from config import settings
from realtime_events import process_pending_loop
from routers import admin, auth, boards, chat, feed, wanted, ws, ws_chat


@asynccontextmanager
async def lifespan(app: FastAPI):
    pending_task = asyncio.create_task(process_pending_loop())
    yield
    pending_task.cancel()
    try:
        await pending_task
    except asyncio.CancelledError:
        pass


app = FastAPI(title="HanuriProject API", lifespan=lifespan)
app.include_router(auth.router)
app.include_router(admin.router)
app.include_router(boards.router)
app.include_router(feed.router)
app.include_router(wanted.router)
app.include_router(chat.router)
app.include_router(ws.router)
app.include_router(ws_chat.router)

uploads_dir = settings.upload_dir
uploads_dir.mkdir(parents=True, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=str(uploads_dir)), name="uploads")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def health_check():
    return {"status": "ok"}
