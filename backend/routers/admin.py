from datetime import datetime
from math import ceil

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, aliased

from database import get_db
from deps import require_admin
from models import Board, Report, User
from schemas import (
    AdminBoardListResponse,
    AdminBoardOut,
    AdminBoardUpdate,
    AdminReportListResponse,
    AdminReportOut,
    AdminReportUpdate,
    AdminUserListResponse,
    AdminUserOut,
    AdminUserUpdate,
)
from upload_storage import delete_uploaded_file

router = APIRouter(prefix="/api/admin", tags=["admin"])


def _admin_report_out(db: Session, r: Report) -> AdminReportOut:
    board = db.get(Board, r.board_id)
    reporter = db.get(User, r.reporter_id)
    reviewer = db.get(User, r.reviewed_by) if r.reviewed_by else None
    return AdminReportOut(
        report_id=r.report_id,
        board_id=r.board_id,
        board_title=board.title if board else "(삭제됨)",
        seller_id=board.user_id if board else "",
        reporter_id=r.reporter_id,
        reporter_name=reporter.name if reporter else r.reporter_id,
        reason=r.reason,
        status=r.status,
        created_at=r.created_at,
        reviewed_at=r.reviewed_at,
        reviewed_by=r.reviewed_by,
        reviewer_name=reviewer.name if reviewer else None,
        admin_note=r.admin_note,
    )


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
    author_name: str | None = Query(None, description="작성자 이름 검색(부분일치, User.name)"),
    _: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> AdminBoardListResponse:
    stmt = select(Board)
    if author_name and author_name.strip():
        stmt = stmt.join(User, Board.user_id == User.user_id)
    filters = []
    if board_id is not None:
        filters.append(Board.board_id == board_id)
    if title:
        filters.append(Board.title.like(f"%{title.strip()}%"))
    if user_id:
        filters.append(Board.user_id.like(f"%{user_id.strip()}%"))
    if author_name and author_name.strip():
        filters.append(User.name.like(f"%{author_name.strip()}%"))
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


@router.patch("/boards/{board_id}", response_model=AdminBoardOut)
def admin_update_board(
    board_id: int,
    body: AdminBoardUpdate,
    _: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> AdminBoardOut:
    board = db.get(Board, board_id)
    if board is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="게시글을 찾을 수 없습니다.")
    data = body.model_dump(exclude_unset=True)
    if not data:
        return AdminBoardOut.model_validate(board)
    for key, value in data.items():
        setattr(board, key, value)
    db.commit()
    db.refresh(board)
    return AdminBoardOut.model_validate(board)


@router.delete("/boards/{board_id}", status_code=status.HTTP_204_NO_CONTENT)
def admin_delete_board(
    board_id: int,
    _: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> None:
    board = db.get(Board, board_id)
    if board is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="게시글을 찾을 수 없습니다.")
    for img in list(board.images):
        delete_uploaded_file(img.path)
    db.delete(board)
    db.commit()


@router.get("/reports", response_model=AdminReportListResponse)
def list_reports(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status_filter: str | None = Query(None, alias="status", description="PENDING|REVIEWED|DISMISSED|ACTION_TAKEN"),
    _: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> AdminReportListResponse:
    reporter = aliased(User)
    reviewer = aliased(User)
    count_q = select(func.count(Report.report_id)).join(Board, Report.board_id == Board.board_id)
    if status_filter in ("PENDING", "REVIEWED", "DISMISSED", "ACTION_TAKEN"):
        count_q = count_q.where(Report.status == status_filter)
    total = db.scalar(count_q) or 0
    pages = ceil(total / page_size) if total else 0
    offset = (page - 1) * page_size

    stmt = (
        select(Report, Board.title, Board.user_id, reporter.name, reviewer.name)
        .join(Board, Report.board_id == Board.board_id)
        .join(reporter, Report.reporter_id == reporter.user_id)
        .outerjoin(reviewer, Report.reviewed_by == reviewer.user_id)
    )
    if status_filter in ("PENDING", "REVIEWED", "DISMISSED", "ACTION_TAKEN"):
        stmt = stmt.where(Report.status == status_filter)
    stmt = stmt.order_by(Report.created_at.desc()).offset(offset).limit(page_size)

    rows = db.execute(stmt).all()
    items: list[AdminReportOut] = []
    for r, board_title, seller_id, reporter_name, reviewer_name in rows:
        items.append(
            AdminReportOut(
                report_id=r.report_id,
                board_id=r.board_id,
                board_title=board_title,
                seller_id=seller_id,
                reporter_id=r.reporter_id,
                reporter_name=reporter_name,
                reason=r.reason,
                status=r.status,
                created_at=r.created_at,
                reviewed_at=r.reviewed_at,
                reviewed_by=r.reviewed_by,
                reviewer_name=reviewer_name,
                admin_note=r.admin_note,
            )
        )
    return AdminReportListResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        pages=pages,
    )


@router.patch("/reports/{report_id}", response_model=AdminReportOut)
def patch_report(
    report_id: int,
    body: AdminReportUpdate,
    admin_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> AdminReportOut:
    r = db.get(Report, report_id)
    if r is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="신고를 찾을 수 없습니다.")
    data = body.model_dump(exclude_unset=True)
    if not data:
        return _admin_report_out(db, r)
    r.reviewed_at = datetime.now()
    r.reviewed_by = admin_user.user_id
    for key, value in data.items():
        setattr(r, key, value)
    db.commit()
    db.refresh(r)
    return _admin_report_out(db, r)
