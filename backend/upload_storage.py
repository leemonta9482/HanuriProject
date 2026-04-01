import uuid
from pathlib import Path

from fastapi import HTTPException, UploadFile, status

from config import settings

STUDENT_CARD_SUBDIR = "student_cards"
ALLOWED_IMAGE_TYPES = frozenset(
    {
        "image/jpeg",
        "image/png",
        "image/webp",
        "image/gif",
    }
)
EXT_BY_TYPE: dict[str, str] = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
    "image/gif": ".gif",
}
MAX_IMAGE_BYTES = 5 * 1024 * 1024


def _student_cards_dir() -> Path:
    return settings.upload_dir / STUDENT_CARD_SUBDIR


async def save_student_id_card(file: UploadFile) -> str:
    if not file.content_type or file.content_type not in ALLOWED_IMAGE_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="학생증은 이미지 파일(JPEG, PNG, WebP, GIF)만 업로드할 수 있습니다.",
        )
    ext = EXT_BY_TYPE.get(file.content_type, ".jpg")
    data = await file.read()
    if len(data) > MAX_IMAGE_BYTES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="학생증 이미지는 5MB 이하여야 합니다.",
        )
    if len(data) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="빈 파일은 업로드할 수 없습니다.",
        )
    name = f"{uuid.uuid4().hex}{ext}"
    dest_dir = _student_cards_dir()
    dest_dir.mkdir(parents=True, exist_ok=True)
    full_path = dest_dir / name
    full_path.write_bytes(data)
    return f"{STUDENT_CARD_SUBDIR}/{name}"


def delete_uploaded_file(relative_path: str) -> None:
    if not relative_path or ".." in relative_path:
        return
    p = settings.upload_dir / relative_path
    try:
        if p.is_file():
            p.unlink()
    except OSError:
        pass


BOARD_IMAGES_SUBDIR = "board_images"
MAX_BOARD_IMAGES = 10


def _board_images_dir() -> Path:
    return settings.upload_dir / BOARD_IMAGES_SUBDIR


async def save_board_image(file: UploadFile) -> str:
    if not file.content_type or file.content_type not in ALLOWED_IMAGE_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="이미지는 JPEG, PNG, WebP, GIF만 업로드할 수 있습니다.",
        )
    ext = EXT_BY_TYPE.get(file.content_type, ".jpg")
    data = await file.read()
    if len(data) > MAX_IMAGE_BYTES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="이미지는 5MB 이하여야 합니다.",
        )
    if len(data) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="빈 파일은 업로드할 수 없습니다.",
        )
    name = f"{uuid.uuid4().hex}{ext}"
    dest_dir = _board_images_dir()
    dest_dir.mkdir(parents=True, exist_ok=True)
    full_path = dest_dir / name
    full_path.write_bytes(data)
    return f"{BOARD_IMAGES_SUBDIR}/{name}"


PROFILE_IMAGES_SUBDIR = "profile_images"


def _profile_images_dir() -> Path:
    return settings.upload_dir / PROFILE_IMAGES_SUBDIR


async def save_profile_image(file: UploadFile) -> str:
    if not file.content_type or file.content_type not in ALLOWED_IMAGE_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="프로필 이미지는 JPEG, PNG, WebP, GIF만 업로드할 수 있습니다.",
        )
    ext = EXT_BY_TYPE.get(file.content_type, ".jpg")
    data = await file.read()
    if len(data) > MAX_IMAGE_BYTES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="프로필 이미지는 5MB 이하여야 합니다.",
        )
    if len(data) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="빈 파일은 업로드할 수 없습니다.",
        )
    name = f"{uuid.uuid4().hex}{ext}"
    dest_dir = _profile_images_dir()
    dest_dir.mkdir(parents=True, exist_ok=True)
    full_path = dest_dir / name
    full_path.write_bytes(data)
    return f"{PROFILE_IMAGES_SUBDIR}/{name}"
