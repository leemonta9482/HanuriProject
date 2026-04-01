from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from config import settings
from routers import admin, auth, boards, chat, events, feed, wanted

app = FastAPI(title="HanuriProject API")
app.include_router(auth.router)
app.include_router(admin.router)
app.include_router(boards.router)
app.include_router(feed.router)
app.include_router(wanted.router)
app.include_router(chat.router)
app.include_router(events.router)

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