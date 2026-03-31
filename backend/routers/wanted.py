from math import ceil

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import desc, func, select
from sqlalchemy.orm import Session, aliased

from database import get_db
from deps import get_current_user
from models import User, WantedPost
from schemas import WantedListResponse, WantedPostCreate, WantedPostOut, WantedPostUpdate

router = APIRouter(prefix="/api/wanted", tags=["wanted"])


def _assert_same_school_wanted(db: Session, w: WantedPost, user: User) -> None:
    if user.is_admin:
        return
    author = db.get(User, w.user_id)
    if author is None or author.school_name != user.school_name:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="구매 희망글을 찾을 수 없습니다.")


def _wanted_out(db: Session, w: WantedPost, viewer: User | None) -> WantedPostOut:
    author = db.get(User, w.user_id)
    return WantedPostOut(
        wanted_id=w.wanted_id,
        user_id=w.user_id,
        author_name=author.name if author else w.user_id,
        title=w.title,
        description=w.description,
        max_price=w.max_price,
        preferred_location=w.preferred_location,
        created_at=w.created_at,
        updated_at=w.updated_at,
        is_owner=bool(viewer and viewer.user_id == w.user_id),
    )


@router.get("", response_model=WantedListResponse)
def list_wanted(
    page: int = Query(1, ge=1),
    page_size: int = Query(12, ge=1, le=48),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> WantedListResponse:
    author = aliased(User)
    count_q = select(func.count()).select_from(WantedPost).join(author, WantedPost.user_id == author.user_id)
    if not user.is_admin:
        count_q = count_q.where(author.school_name == user.school_name)
    total = db.scalar(count_q) or 0

    stmt = select(WantedPost).join(author, WantedPost.user_id == author.user_id)
    if not user.is_admin:
        stmt = stmt.where(author.school_name == user.school_name)
    stmt = stmt.order_by(desc(WantedPost.created_at)).offset((page - 1) * page_size).limit(page_size)

    rows = db.execute(stmt).scalars().all()
    items = [_wanted_out(db, w, user) for w in rows]
    pages = ceil(total / page_size) if total else 0
    return WantedListResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        pages=pages,
    )


@router.get("/{wanted_id}", response_model=WantedPostOut)
def get_wanted(
    wanted_id: int,
    db: Session = Depends(get_db),
    viewer: User = Depends(get_current_user),
) -> WantedPostOut:
    w = db.get(WantedPost, wanted_id)
    if w is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="구매 희망글을 찾을 수 없습니다.")
    _assert_same_school_wanted(db, w, viewer)
    return _wanted_out(db, w, viewer)


@router.post("", response_model=WantedPostOut, status_code=status.HTTP_201_CREATED)
def create_wanted(
    body: WantedPostCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> WantedPostOut:
    w = WantedPost(
        user_id=user.user_id,
        title=body.title.strip(),
        description=body.description.strip() if body.description else None,
        max_price=body.max_price,
        preferred_location=body.preferred_location.strip() if body.preferred_location else None,
    )
    db.add(w)
    db.commit()
    db.refresh(w)
    return _wanted_out(db, w, user)


@router.patch("/{wanted_id}", response_model=WantedPostOut)
def update_wanted(
    wanted_id: int,
    body: WantedPostUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> WantedPostOut:
    w = db.get(WantedPost, wanted_id)
    if w is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="구매 희망글을 찾을 수 없습니다.")
    if w.user_id != user.user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="수정 권한이 없습니다.")
    data = body.model_dump(exclude_unset=True)
    if "title" in data and data["title"] is not None:
        data["title"] = data["title"].strip()
    if "description" in data and data["description"] is not None:
        data["description"] = data["description"].strip()
    if "preferred_location" in data and data["preferred_location"] is not None:
        data["preferred_location"] = data["preferred_location"].strip()
    for k, v in data.items():
        setattr(w, k, v)
    db.commit()
    db.refresh(w)
    return _wanted_out(db, w, user)


@router.delete("/{wanted_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_wanted(
    wanted_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> None:
    w = db.get(WantedPost, wanted_id)
    if w is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="구매 희망글을 찾을 수 없습니다.")
    if w.user_id != user.user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="삭제 권한이 없습니다.")
    db.delete(w)
    db.commit()
