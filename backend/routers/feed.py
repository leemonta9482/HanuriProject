from math import ceil

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, or_, select, text
from sqlalchemy.orm import Session, aliased

from database import get_db
from deps import get_current_user
from models import Board, User, WantedPost
from schemas import FeedItemOut, FeedListResponse

from .boards import _favorite_counts, _favorited_ids, _first_thumbnails

router = APIRouter(prefix="/api", tags=["feed"])

_ORDER_SQL = {
    "latest": "created_at DESC",
    "price_asc": "price_sort ASC, created_at DESC",
    "price_desc": "price_sort DESC, created_at DESC",
}

_MAX_SEARCH_LEN = 100


def _sanitize_search(q: str | None) -> str | None:
    """LIKE 와일드카드 제거 후 공백만 있으면 None."""
    if not q or not str(q).strip():
        return None
    s = str(q).strip()[:_MAX_SEARCH_LEN]
    s = "".join(c for c in s if c not in "%_\\")
    return s or None


def _feed_union_sql(board_where: str, wanted_where: str, order_sql: str) -> str:
    return f"""
SELECT kind, board_id, wanted_id, title, price_sort, created_at, seller_name, loc, board_status, trade_type, display_price, owner_user_id, author_profile_image_path
FROM (
  SELECT
    'board' AS kind,
    b.board_id AS board_id,
    CAST(NULL AS UNSIGNED) AS wanted_id,
    b.title,
    b.price AS price_sort,
    b.created_at,
    u.name AS seller_name,
    b.location AS loc,
    b.status AS board_status,
    b.trade_type AS trade_type,
    b.price AS display_price,
    b.user_id AS owner_user_id,
    u.profile_image_path AS author_profile_image_path
  FROM Board b
  INNER JOIN User u ON b.user_id = u.user_id
  WHERE {board_where}
  UNION ALL
  SELECT
    'wanted',
    CAST(NULL AS UNSIGNED),
    w.wanted_id,
    w.title,
    COALESCE(w.max_price, 0) AS price_sort,
    w.created_at,
    u.name,
    w.preferred_location,
    NULL,
    NULL,
    w.max_price AS display_price,
    w.user_id AS owner_user_id,
    u.profile_image_path AS author_profile_image_path
  FROM WantedPost w
  INNER JOIN User u ON w.user_id = u.user_id
  WHERE {wanted_where}
) AS t
ORDER BY {order_sql}
LIMIT :limit OFFSET :offset
"""


@router.get("/feed", response_model=FeedListResponse)
def list_feed(
    page: int = Query(1, ge=1),
    page_size: int = Query(12, ge=1, le=48),
    sort: str = Query("latest", description="latest | price_asc | price_desc"),
    q: str | None = Query(None, description="제목·설명·장소·작성자 학과 검색", max_length=_MAX_SEARCH_LEN),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> FeedListResponse:
    seller_b = aliased(User)
    author_w = aliased(User)
    search_kw = _sanitize_search(q)
    like_pat = f"%{search_kw}%" if search_kw else None

    if user.is_admin:
        if like_pat is not None:
            stmt_b = (
                select(func.count())
                .select_from(Board)
                .join(seller_b, Board.user_id == seller_b.user_id)
                .where(
                    or_(
                        Board.title.like(like_pat),
                        func.coalesce(Board.description, "").like(like_pat),
                        func.coalesce(Board.location, "").like(like_pat),
                        func.coalesce(seller_b.interest_major, "").like(like_pat),
                    )
                )
            )
            stmt_w = (
                select(func.count())
                .select_from(WantedPost)
                .join(author_w, WantedPost.user_id == author_w.user_id)
                .where(
                    or_(
                        WantedPost.title.like(like_pat),
                        func.coalesce(WantedPost.description, "").like(like_pat),
                        func.coalesce(WantedPost.preferred_location, "").like(like_pat),
                        func.coalesce(author_w.interest_major, "").like(like_pat),
                    )
                )
            )
        else:
            stmt_b = select(func.count()).select_from(Board)
            stmt_w = select(func.count()).select_from(WantedPost)
        count_board = db.scalar(stmt_b) or 0
        count_wanted = db.scalar(stmt_w) or 0
        school_sql = "1=1"
        count_params: dict = {}
    else:
        stmt_b = (
            select(func.count())
            .select_from(Board)
            .join(seller_b, Board.user_id == seller_b.user_id)
            .where(seller_b.school_name == user.school_name)
        )
        stmt_w = (
            select(func.count())
            .select_from(WantedPost)
            .join(author_w, WantedPost.user_id == author_w.user_id)
            .where(author_w.school_name == user.school_name)
        )
        if like_pat is not None:
            stmt_b = stmt_b.where(
                or_(
                    Board.title.like(like_pat),
                    func.coalesce(Board.description, "").like(like_pat),
                    func.coalesce(Board.location, "").like(like_pat),
                    func.coalesce(seller_b.interest_major, "").like(like_pat),
                )
            )
            stmt_w = stmt_w.where(
                or_(
                    WantedPost.title.like(like_pat),
                    func.coalesce(WantedPost.description, "").like(like_pat),
                    func.coalesce(WantedPost.preferred_location, "").like(like_pat),
                    func.coalesce(author_w.interest_major, "").like(like_pat),
                )
            )
        count_board = db.scalar(stmt_b) or 0
        count_wanted = db.scalar(stmt_w) or 0
        school_sql = "u.school_name = :school"
        count_params = {"school": user.school_name}

    if like_pat is None:
        board_where = wanted_where = school_sql
    else:
        search_board = (
            "(b.title LIKE :search OR IFNULL(b.description,'') LIKE :search OR IFNULL(b.location,'') LIKE :search "
            "OR IFNULL(u.interest_major,'') LIKE :search)"
        )
        search_wanted = (
            "(w.title LIKE :search OR IFNULL(w.description,'') LIKE :search OR IFNULL(w.preferred_location,'') LIKE :search "
            "OR IFNULL(u.interest_major,'') LIKE :search)"
        )
        board_where = f"({school_sql}) AND {search_board}"
        wanted_where = f"({school_sql}) AND {search_wanted}"

    total = count_board + count_wanted
    pages = ceil(total / page_size) if total else 0
    offset = (page - 1) * page_size

    order_sql = _ORDER_SQL.get(sort, _ORDER_SQL["latest"])
    sql = _feed_union_sql(board_where, wanted_where, order_sql)

    params: dict = {**count_params, "limit": page_size, "offset": offset}
    if like_pat is not None:
        params["search"] = like_pat
    rows = db.execute(text(sql), params).mappings().all()

    board_ids = [int(r["board_id"]) for r in rows if r["kind"] == "board" and r["board_id"] is not None]
    thumbs = _first_thumbnails(db, board_ids)
    favs = _favorited_ids(db, user.user_id, board_ids)
    fav_counts = _favorite_counts(db, board_ids)

    items: list[FeedItemOut] = []
    for r in rows:
        kind = r["kind"]
        oid = r.get("owner_user_id")
        is_owner = oid is not None and str(oid) == user.user_id
        if kind == "board":
            bid = int(r["board_id"])
            dp = r["display_price"]
            price = int(dp) if dp is not None else None
            oid_str = str(oid) if oid is not None else None
            pip = r.get("author_profile_image_path")
            pip_str = str(pip).strip() if pip is not None and str(pip).strip() else None
            items.append(
                FeedItemOut(
                    kind="board",
                    board_id=bid,
                    wanted_id=None,
                    title=r["title"],
                    price=price,
                    created_at=r["created_at"],
                    author_name=r["seller_name"],
                    author_user_id=oid_str,
                    author_profile_image_path=pip_str,
                    location=r["loc"],
                    thumbnail_path=thumbs.get(bid),
                    status=r["board_status"],
                    trade_type=r["trade_type"],
                    is_favorited=bid in favs,
                    favorite_count=fav_counts.get(bid, 0),
                    is_owner=is_owner,
                )
            )
        else:
            wid = int(r["wanted_id"])
            dp = r["display_price"]
            price = int(dp) if dp is not None else None
            oid_str = str(oid) if oid is not None else None
            pip = r.get("author_profile_image_path")
            pip_str = str(pip).strip() if pip is not None and str(pip).strip() else None
            items.append(
                FeedItemOut(
                    kind="wanted",
                    board_id=None,
                    wanted_id=wid,
                    title=r["title"],
                    price=price,
                    created_at=r["created_at"],
                    author_name=r["seller_name"],
                    author_user_id=oid_str,
                    author_profile_image_path=pip_str,
                    location=r["loc"],
                    thumbnail_path=None,
                    status=None,
                    trade_type=None,
                    is_favorited=False,
                    favorite_count=0,
                    is_owner=is_owner,
                )
            )

    return FeedListResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        pages=pages,
    )
