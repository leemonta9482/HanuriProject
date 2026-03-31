from math import ceil

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile, status
from sqlalchemy import asc, desc, func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, aliased, selectinload

from database import get_db
from deps import get_current_user
from models import Board, BoardImage, Favorite, PurchaseRequest, Report, User
from schemas import (
    BoardDetailOut,
    BoardImageOut,
    BoardListItem,
    BoardListResponse,
    BoardStatusUpdate,
    BoardUpdate,
    PurchaseRequestOut,
    PurchaseRequestStatusUpdate,
    ReportCreate,
)
from realtime_events import publish_event
from upload_storage import MAX_BOARD_IMAGES, delete_uploaded_file, save_board_image

router = APIRouter(prefix="/api", tags=["boards"])


def _assert_same_school_board(db: Session, board: Board, user: User) -> None:
    """관리자가 아니면 판매자의 학교가 요청자와 같을 때만 접근 가능."""
    if user.is_admin:
        return
    seller = db.get(User, board.user_id)
    if seller is None or seller.school_name != user.school_name:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="게시글을 찾을 수 없습니다.")


def _first_thumbnails(db: Session, board_ids: list[int]) -> dict[int, str]:
    if not board_ids:
        return {}
    rows = (
        db.execute(
            select(BoardImage.board_id, BoardImage.path, BoardImage.sort_order)
            .where(BoardImage.board_id.in_(board_ids))
            .order_by(BoardImage.board_id, BoardImage.sort_order)
        )
        .all()
    )
    out: dict[int, str] = {}
    for bid, path, _ in rows:
        if bid not in out:
            out[bid] = path
    return out


def _favorited_ids(db: Session, user_id: str | None, board_ids: list[int]) -> set[int]:
    if not user_id or not board_ids:
        return set()
    rows = (
        db.execute(
            select(Favorite.board_id).where(
                Favorite.user_id == user_id,
                Favorite.board_id.in_(board_ids),
            )
        )
        .scalars()
        .all()
    )
    return set(rows)


def _favorite_counts(db: Session, board_ids: list[int]) -> dict[int, int]:
    if not board_ids:
        return {}
    rows = db.execute(
        select(Favorite.board_id, func.count(Favorite.id))
        .where(Favorite.board_id.in_(board_ids))
        .group_by(Favorite.board_id)
    ).all()
    return {int(r[0]): int(r[1]) for r in rows}


@router.get("/boards", response_model=BoardListResponse)
def list_boards(
    page: int = Query(1, ge=1),
    page_size: int = Query(12, ge=1, le=48),
    sort: str = Query("latest", description="latest | price_asc | price_desc"),
    status_filter: str | None = Query(None, alias="status"),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> BoardListResponse:
    seller = aliased(User)
    count_q = select(func.count(Board.board_id)).join(seller, Board.user_id == seller.user_id)
    if not user.is_admin:
        count_q = count_q.where(seller.school_name == user.school_name)
    if status_filter in ("ON_SALE", "RESERVED", "SOLD"):
        count_q = count_q.where(Board.status == status_filter)
    total = db.scalar(count_q) or 0

    stmt = select(Board, seller.name).join(seller, Board.user_id == seller.user_id)
    if not user.is_admin:
        stmt = stmt.where(seller.school_name == user.school_name)
    if status_filter in ("ON_SALE", "RESERVED", "SOLD"):
        stmt = stmt.where(Board.status == status_filter)
    pages = ceil(total / page_size) if total else 0
    offset = (page - 1) * page_size

    if sort == "price_asc":
        stmt = stmt.order_by(asc(Board.price), desc(Board.created_at))
    elif sort == "price_desc":
        stmt = stmt.order_by(desc(Board.price), desc(Board.created_at))
    else:
        stmt = stmt.order_by(desc(Board.created_at))

    rows = db.execute(stmt.offset(offset).limit(page_size)).all()
    board_ids = [b.board_id for b, _ in rows]
    thumbs = _first_thumbnails(db, board_ids)
    favs = _favorited_ids(db, user.user_id, board_ids)
    fav_counts = _favorite_counts(db, board_ids)

    items: list[BoardListItem] = []
    for b, seller_name in rows:
        items.append(
            BoardListItem(
                board_id=b.board_id,
                user_id=b.user_id,
                seller_name=seller_name,
                title=b.title,
                price=b.price,
                location=b.location,
                trade_type=b.trade_type,
                status=b.status,
                thumbnail_path=thumbs.get(b.board_id),
                created_at=b.created_at,
                is_favorited=b.board_id in favs,
                favorite_count=fav_counts.get(b.board_id, 0),
            )
        )
    return BoardListResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        pages=pages,
    )


def _board_detail_out(
    db: Session,
    board: Board,
    seller_name: str,
    viewer: User | None,
) -> BoardDetailOut:
    imgs = sorted(board.images, key=lambda x: x.sort_order)
    image_out = [BoardImageOut.model_validate(i) for i in imgs]
    is_fav = False
    my_pr: str | None = None
    if viewer:
        is_fav = (
            db.scalar(
                select(func.count())
                .select_from(Favorite)
                .where(Favorite.user_id == viewer.user_id, Favorite.board_id == board.board_id)
            )
            or 0
        ) > 0
        if viewer.user_id != board.user_id:
            pr = db.execute(
                select(PurchaseRequest).where(
                    PurchaseRequest.board_id == board.board_id,
                    PurchaseRequest.buyer_id == viewer.user_id,
                )
            ).scalar_one_or_none()
            if pr:
                my_pr = pr.status
    fav_count = (
        db.scalar(select(func.count(Favorite.id)).where(Favorite.board_id == board.board_id)) or 0
    )
    return BoardDetailOut(
        board_id=board.board_id,
        user_id=board.user_id,
        seller_name=seller_name,
        title=board.title,
        price=board.price,
        description=board.description,
        location=board.location,
        trade_type=board.trade_type,
        status=board.status,
        images=image_out,
        created_at=board.created_at,
        updated_at=board.updated_at,
        is_favorited=is_fav,
        is_owner=bool(viewer and viewer.user_id == board.user_id),
        my_purchase_request_status=my_pr,
        favorite_count=int(fav_count),
    )


@router.get("/boards/{board_id}", response_model=BoardDetailOut)
def get_board(
    board_id: int,
    db: Session = Depends(get_db),
    viewer: User = Depends(get_current_user),
) -> BoardDetailOut:
    board = db.execute(
        select(Board)
        .where(Board.board_id == board_id)
        .options(selectinload(Board.images))
    ).scalar_one_or_none()
    if board is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="게시글을 찾을 수 없습니다.")
    _assert_same_school_board(db, board, viewer)
    seller = db.get(User, board.user_id)
    seller_name = seller.name if seller else ""
    return _board_detail_out(db, board, seller_name, viewer)


@router.post("/boards", response_model=BoardDetailOut)
async def create_board(
    title: str = Form(..., min_length=1, max_length=200),
    price: int = Form(..., ge=0),
    description: str | None = Form(None),
    location: str | None = Form(None, max_length=255),
    trade_type: str = Form("BOTH"),
    files: list[UploadFile] | None = File(None),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> BoardDetailOut:
    if trade_type not in ("DIRECT", "DELIVERY", "BOTH"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="거래 방식이 올바르지 않습니다.")
    upload_list = files or []
    if len(upload_list) > MAX_BOARD_IMAGES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"이미지는 최대 {MAX_BOARD_IMAGES}장까지 업로드할 수 있습니다.",
        )
    board = Board(
        user_id=user.user_id,
        title=title.strip(),
        price=price,
        description=description.strip() if description else None,
        location=location.strip() if location else None,
        trade_type=trade_type,
        status="ON_SALE",
    )
    db.add(board)
    db.flush()
    for idx, uf in enumerate(upload_list):
        rel = await save_board_image(uf)
        db.add(BoardImage(board_id=board.board_id, path=rel, sort_order=idx))
    db.commit()
    db.refresh(board)
    _ = board.images
    return _board_detail_out(db, board, user.name, user)


@router.patch("/boards/{board_id}", response_model=BoardDetailOut)
def update_board(
    board_id: int,
    body: BoardUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> BoardDetailOut:
    board = db.get(Board, board_id)
    if board is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="게시글을 찾을 수 없습니다.")
    if board.user_id != user.user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="수정 권한이 없습니다.")
    data = body.model_dump(exclude_unset=True)
    for k, v in data.items():
        setattr(board, k, v)
    db.commit()
    db.refresh(board)
    _ = board.images
    seller = db.get(User, board.user_id)
    return _board_detail_out(db, board, seller.name if seller else "", user)


@router.patch("/boards/{board_id}/status", response_model=BoardDetailOut)
def update_board_status(
    board_id: int,
    body: BoardStatusUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> BoardDetailOut:
    board = db.get(Board, board_id)
    if board is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="게시글을 찾을 수 없습니다.")
    if board.user_id != user.user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="권한이 없습니다.")
    board.status = body.status
    db.commit()
    db.refresh(board)
    _ = board.images
    seller = db.get(User, board.user_id)
    return _board_detail_out(db, board, seller.name if seller else "", user)


@router.delete("/boards/{board_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_board(
    board_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> None:
    board = db.get(Board, board_id)
    if board is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="게시글을 찾을 수 없습니다.")
    if board.user_id != user.user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="삭제 권한이 없습니다.")
    for img in list(board.images):
        delete_uploaded_file(img.path)
    db.delete(board)
    db.commit()


@router.post("/boards/{board_id}/images", response_model=BoardDetailOut)
async def add_board_images(
    board_id: int,
    files: list[UploadFile] = File(...),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> BoardDetailOut:
    board = db.get(Board, board_id)
    if board is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="게시글을 찾을 수 없습니다.")
    if board.user_id != user.user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="권한이 없습니다.")
    if not files:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="업로드할 이미지를 선택하세요.")
    current = len(board.images)
    if current + len(files) > MAX_BOARD_IMAGES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"이미지는 합쳐서 최대 {MAX_BOARD_IMAGES}장입니다.",
        )
    start = max((i.sort_order for i in board.images), default=-1) + 1
    for idx, uf in enumerate(files):
        rel = await save_board_image(uf)
        db.add(BoardImage(board_id=board.board_id, path=rel, sort_order=start + idx))
    db.commit()
    db.refresh(board)
    _ = board.images
    seller = db.get(User, board.user_id)
    return _board_detail_out(db, board, seller.name if seller else "", user)


@router.delete("/boards/{board_id}/images/{image_id}", response_model=BoardDetailOut)
def delete_board_image(
    board_id: int,
    image_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> BoardDetailOut:
    board = db.get(Board, board_id)
    if board is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="게시글을 찾을 수 없습니다.")
    if board.user_id != user.user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="권한이 없습니다.")
    img = db.get(BoardImage, image_id)
    if img is None or img.board_id != board_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="이미지를 찾을 수 없습니다.")
    delete_uploaded_file(img.path)
    db.delete(img)
    db.commit()
    db.refresh(board)
    _ = board.images
    seller = db.get(User, board.user_id)
    return _board_detail_out(db, board, seller.name if seller else "", user)


@router.post("/boards/{board_id}/favorite", response_model=BoardDetailOut)
def add_favorite(
    board_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> BoardDetailOut:
    board = db.get(Board, board_id)
    if board is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="게시글을 찾을 수 없습니다.")
    _assert_same_school_board(db, board, user)
    if board.user_id == user.user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="자신이 올린 판매글은 찜할 수 없습니다.",
        )
    db.add(Favorite(user_id=user.user_id, board_id=board_id))
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
    else:
        if board.user_id != user.user_id:
            favoriter = db.get(User, user.user_id)
            display = ((favoriter.name or "").strip() or user.user_id) if favoriter else user.user_id
            publish_event(
                board.user_id,
                {
                    "type": "favorite",
                    "board_id": board_id,
                    "title": "찜 알림",
                    "body": f"{display}님이 내 판매글을 찜했습니다.",
                },
            )
    db.refresh(board)
    _ = board.images
    seller = db.get(User, board.user_id)
    return _board_detail_out(db, board, seller.name if seller else "", user)


@router.delete("/boards/{board_id}/favorite", response_model=BoardDetailOut)
def remove_favorite(
    board_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> BoardDetailOut:
    board = db.get(Board, board_id)
    if board is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="게시글을 찾을 수 없습니다.")
    _assert_same_school_board(db, board, user)
    fav = db.execute(
        select(Favorite).where(Favorite.user_id == user.user_id, Favorite.board_id == board_id)
    ).scalar_one_or_none()
    if fav:
        db.delete(fav)
        db.commit()
    db.refresh(board)
    _ = board.images
    seller = db.get(User, board.user_id)
    return _board_detail_out(db, board, seller.name if seller else "", user)


@router.get("/me/favorites", response_model=BoardListResponse)
def list_my_favorites(
    page: int = Query(1, ge=1),
    page_size: int = Query(12, ge=1, le=48),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> BoardListResponse:
    seller = aliased(User)
    stmt = (
        select(Board, seller.name)
        .join(Favorite, Favorite.board_id == Board.board_id)
        .join(seller, Board.user_id == seller.user_id)
        .where(Favorite.user_id == user.user_id)
    )
    if not user.is_admin:
        stmt = stmt.where(seller.school_name == user.school_name)
    stmt = stmt.order_by(desc(Favorite.id))
    count_q = (
        select(func.count(Favorite.id))
        .join(Board, Favorite.board_id == Board.board_id)
        .join(seller, Board.user_id == seller.user_id)
        .where(Favorite.user_id == user.user_id)
    )
    if not user.is_admin:
        count_q = count_q.where(seller.school_name == user.school_name)
    total = db.scalar(count_q) or 0
    pages = ceil(total / page_size) if total else 0
    offset = (page - 1) * page_size
    rows = db.execute(stmt.offset(offset).limit(page_size)).all()
    board_ids = [b.board_id for b, _ in rows]
    thumbs = _first_thumbnails(db, board_ids)
    favs = _favorited_ids(db, user.user_id, board_ids)
    fav_counts = _favorite_counts(db, board_ids)
    items = []
    for b, seller_name in rows:
        sn = (seller_name or "").strip() if isinstance(seller_name, str) else (str(seller_name).strip() if seller_name else "")
        items.append(
            BoardListItem(
                board_id=b.board_id,
                user_id=b.user_id,
                seller_name=sn or "회원",
                title=b.title,
                price=b.price,
                location=b.location,
                trade_type=b.trade_type,
                status=b.status,
                thumbnail_path=thumbs.get(b.board_id),
                created_at=b.created_at,
                is_favorited=b.board_id in favs,
                favorite_count=fav_counts.get(b.board_id, 0),
            )
        )
    return BoardListResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        pages=pages,
    )


@router.get("/me/boards", response_model=BoardListResponse)
def list_my_boards(
    page: int = Query(1, ge=1),
    page_size: int = Query(12, ge=1, le=48),
    status_filter: str | None = Query(None, alias="status"),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> BoardListResponse:
    """내가 작성한 판매글만 조회 (내 상점)."""
    seller = aliased(User)
    stmt = (
        select(Board, seller.name)
        .join(seller, Board.user_id == seller.user_id)
        .where(Board.user_id == user.user_id)
    )
    if status_filter in ("ON_SALE", "RESERVED", "SOLD"):
        stmt = stmt.where(Board.status == status_filter)

    count_q = select(func.count(Board.board_id)).where(Board.user_id == user.user_id)
    if status_filter in ("ON_SALE", "RESERVED", "SOLD"):
        count_q = count_q.where(Board.status == status_filter)
    total = db.scalar(count_q) or 0
    pages = ceil(total / page_size) if total else 0
    offset = (page - 1) * page_size

    stmt = stmt.order_by(desc(Board.created_at)).offset(offset).limit(page_size)
    rows = db.execute(stmt).all()
    board_ids = [b.board_id for b, _ in rows]
    thumbs = _first_thumbnails(db, board_ids)
    favs = _favorited_ids(db, user.user_id, board_ids)
    fav_counts = _favorite_counts(db, board_ids)

    items: list[BoardListItem] = []
    for b, seller_name in rows:
        sn = (
            (seller_name or "").strip()
            if isinstance(seller_name, str)
            else (str(seller_name).strip() if seller_name else "")
        )
        items.append(
            BoardListItem(
                board_id=b.board_id,
                user_id=b.user_id,
                seller_name=sn or "회원",
                title=b.title,
                price=b.price,
                location=b.location,
                trade_type=b.trade_type,
                status=b.status,
                thumbnail_path=thumbs.get(b.board_id),
                created_at=b.created_at,
                is_favorited=b.board_id in favs,
                favorite_count=fav_counts.get(b.board_id, 0),
            )
        )
    return BoardListResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        pages=pages,
    )


@router.post("/boards/{board_id}/purchase-requests", response_model=PurchaseRequestOut)
def create_purchase_request(
    board_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> PurchaseRequestOut:
    board = db.get(Board, board_id)
    if board is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="게시글을 찾을 수 없습니다.")
    _assert_same_school_board(db, board, user)
    if board.user_id == user.user_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="본인 게시글에는 구매 신청을 할 수 없습니다.")
    pr = PurchaseRequest(board_id=board_id, buyer_id=user.user_id, status="REQUESTED")
    db.add(pr)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="이미 구매 신청한 게시글입니다.",
        ) from None
    db.refresh(pr)
    buyer = db.get(User, user.user_id)
    return PurchaseRequestOut(
        id=pr.id,
        board_id=pr.board_id,
        buyer_id=pr.buyer_id,
        buyer_name=buyer.name if buyer else pr.buyer_id,
        status=pr.status,
        created_at=pr.created_at,
    )


@router.get("/boards/{board_id}/purchase-requests", response_model=list[PurchaseRequestOut])
def list_purchase_requests(
    board_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> list[PurchaseRequestOut]:
    board = db.get(Board, board_id)
    if board is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="게시글을 찾을 수 없습니다.")
    if board.user_id != user.user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="판매자만 조회할 수 있습니다.")
    rows = db.execute(
        select(PurchaseRequest, User.name)
        .join(User, PurchaseRequest.buyer_id == User.user_id)
        .where(PurchaseRequest.board_id == board_id)
        .order_by(desc(PurchaseRequest.created_at))
    ).all()
    return [
        PurchaseRequestOut(
            id=pr.id,
            board_id=pr.board_id,
            buyer_id=pr.buyer_id,
            buyer_name=name,
            status=pr.status,
            created_at=pr.created_at,
        )
        for pr, name in rows
    ]


@router.patch("/purchase-requests/{request_id}", response_model=PurchaseRequestOut)
def update_purchase_request(
    request_id: int,
    body: PurchaseRequestStatusUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> PurchaseRequestOut:
    pr = db.get(PurchaseRequest, request_id)
    if pr is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="구매 요청을 찾을 수 없습니다.")
    board = db.get(Board, pr.board_id)
    if board is None or board.user_id != user.user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="판매자만 처리할 수 있습니다.")
    if pr.status != "REQUESTED":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="이미 처리된 요청입니다.")
    pr.status = body.status
    if body.status == "ACCEPTED":
        board.status = "RESERVED"
        others = db.execute(
            select(PurchaseRequest).where(
                PurchaseRequest.board_id == board.board_id,
                PurchaseRequest.id != pr.id,
                PurchaseRequest.status == "REQUESTED",
            )
        ).scalars().all()
        for o in others:
            o.status = "REJECTED"
    db.commit()
    db.refresh(pr)
    buyer = db.get(User, pr.buyer_id)
    return PurchaseRequestOut(
        id=pr.id,
        board_id=pr.board_id,
        buyer_id=pr.buyer_id,
        buyer_name=buyer.name if buyer else pr.buyer_id,
        status=pr.status,
        created_at=pr.created_at,
    )


@router.post("/boards/{board_id}/reports", status_code=status.HTTP_201_CREATED)
def report_board(
    board_id: int,
    body: ReportCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> dict[str, str]:
    board = db.get(Board, board_id)
    if board is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="게시글을 찾을 수 없습니다.")
    _assert_same_school_board(db, board, user)
    if board.user_id == user.user_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="본인 게시글은 신고할 수 없습니다.")
    db.add(
        Report(
            board_id=board_id,
            reporter_id=user.user_id,
            reason=body.reason.strip(),
            status="PENDING",
        )
    )
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="이미 신고한 게시글입니다.",
        ) from None
    return {"message": "신고가 접수되었습니다."}
