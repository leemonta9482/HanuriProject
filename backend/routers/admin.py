from math import ceil

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from database import get_db
from deps import require_admin
from models import Board, User
from schemas import (
    AdminBoardListResponse,
    AdminBoardOut,
    AdminUserListResponse,
    AdminUserOut,
    AdminUserUpdate,
)

router = APIRouter(prefix="/api/admin", tags=["admin"])


@router.get("/users", response_model=AdminUserListResponse)
def list_users(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    user_id: str | None = Query(None, description="아이디 검색(부분일치)"),
    name: str | None = Query(None, description="이름 검색(부분일치)"),
    school_name: str | None = Query(None, description="학교명 검색(부분일치)"),
    _: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> AdminUserListResponse:
    stmt = select(User)
    filters = []
    if user_id:
        filters.append(User.user_id.like(f"%{user_id.strip()}%"))
    if name:
        filters.append(User.name.like(f"%{name.strip()}%"))
    if school_name:
        filters.append(User.school_name.like(f"%{school_name.strip()}%"))
    if filters:
        stmt = stmt.where(*filters)

    total = db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
    pages = ceil(total / page_size) if total else 0
    offset = (page - 1) * page_size
    rows = (
        db.execute(stmt.order_by(User.created_at.desc()).offset(offset).limit(page_size)).scalars().all()
    )
    items = [AdminUserOut.model_validate(u) for u in rows]
    return AdminUserListResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        pages=pages,
    )


@router.patch("/users/{user_id}", response_model=AdminUserOut)
def update_user(
    user_id: str,
    body: AdminUserUpdate,
    _: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> AdminUserOut:
    u = db.get(User, user_id.strip())
    if u is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="사용자를 찾을 수 없습니다.")
    data = body.model_dump(exclude_unset=True)
    if not data:
        return AdminUserOut.model_validate(u)
    for key, value in data.items():
        setattr(u, key, value)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="전화번호 또는 이메일이 이미 사용 중입니다.",
        ) from None
    db.refresh(u)
    return AdminUserOut.model_validate(u)


@router.get("/boards", response_model=AdminBoardListResponse)
def list_boards(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    board_id: int | None = Query(None, description="게시글 번호 검색(정확히)"),
    title: str | None = Query(None, description="게시글 제목 검색(부분일치)"),
    user_id: str | None = Query(None, description="작성자 아이디 검색(부분일치)"),
    _: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> AdminBoardListResponse:
    stmt = select(Board)
    filters = []
    if board_id is not None:
        filters.append(Board.board_id == board_id)
    if title:
        filters.append(Board.title.like(f"%{title.strip()}%"))
    if user_id:
        filters.append(Board.user_id.like(f"%{user_id.strip()}%"))
    if filters:
        stmt = stmt.where(*filters)

    total = db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
    pages = ceil(total / page_size) if total else 0
    offset = (page - 1) * page_size
    rows = (
        db.execute(stmt.order_by(Board.created_at.desc()).offset(offset).limit(page_size)).scalars().all()
    )
    items = [AdminBoardOut.model_validate(b) for b in rows]
    return AdminBoardListResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        pages=pages,
    )
