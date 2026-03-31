from typing import Literal

from pydantic import BaseModel, Field


class UserLogin(BaseModel):
    user_id: str = Field(..., min_length=1, max_length=50)
    password: str = Field(..., min_length=1, max_length=128)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class RegisterResponse(BaseModel):
    user_id: str
    name: str
    message: str = "가입 신청이 접수되었습니다. 관리자 승인 후 로그인할 수 있습니다."


class LoginUserInfo(BaseModel):
    user_id: str
    name: str
    email: str
    is_admin: bool = False


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: LoginUserInfo


class AdminUserOut(BaseModel):
    user_id: str
    name: str
    school_name: str
    phone: str
    email: str
    student_id: str | None
    student_verified: bool
    manner_score: float
    trust_score: float
    interest_major: str | None
    account_status: str
    is_admin: bool
    registration_status: str
    student_id_card_path: str
    created_at: object | None = None
    updated_at: object | None = None

    model_config = {"from_attributes": True}


class AdminUserListResponse(BaseModel):
    items: list[AdminUserOut]
    total: int
    page: int
    page_size: int
    pages: int


class AdminUserUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=50)
    school_name: str | None = Field(None, min_length=1, max_length=100)
    phone: str | None = Field(None, min_length=1, max_length=20)
    email: str | None = Field(None, min_length=1, max_length=100)
    student_id: str | None = Field(None, max_length=20)
    interest_major: str | None = Field(None, max_length=100)
    manner_score: float | None = None
    trust_score: float | None = None
    student_verified: bool | None = None
    account_status: Literal["ACTIVE", "DORMANT", "DELETED"] | None = None
    registration_status: Literal["PENDING", "APPROVED", "REJECTED"] | None = None
    is_admin: bool | None = None


class AdminBoardOut(BaseModel):
    board_id: int
    user_id: str
    title: str
    price: int
    status: str
    trade_type: str
    created_at: object | None = None
    updated_at: object | None = None

    model_config = {"from_attributes": True}


class AdminBoardListResponse(BaseModel):
    items: list[AdminBoardOut]
    total: int
    page: int
    page_size: int
    pages: int


class AdminBoardUpdate(BaseModel):
    title: str | None = Field(None, min_length=1, max_length=200)
    price: int | None = Field(None, ge=0)
    status: Literal["ON_SALE", "RESERVED", "SOLD"] | None = None
    trade_type: Literal["DIRECT", "DELIVERY", "BOTH"] | None = None


class AdminReportOut(BaseModel):
    report_id: int
    board_id: int
    board_title: str
    seller_id: str
    reporter_id: str
    reporter_name: str
    reason: str
    status: str
    created_at: object | None = None
    reviewed_at: object | None = None
    reviewed_by: str | None = None
    reviewer_name: str | None = None
    admin_note: str | None = None


class AdminReportListResponse(BaseModel):
    items: list[AdminReportOut]
    total: int
    page: int
    page_size: int
    pages: int


class AdminReportUpdate(BaseModel):
    status: Literal["PENDING", "REVIEWED", "DISMISSED", "ACTION_TAKEN"] | None = None
    admin_note: str | None = Field(None, max_length=2000)


# --- Marketplace (판매 게시글) ---

class BoardImageOut(BaseModel):
    image_id: int
    path: str
    sort_order: int

    model_config = {"from_attributes": True}


class BoardListItem(BaseModel):
    board_id: int
    user_id: str
    seller_name: str
    title: str
    price: int
    location: str | None
    trade_type: str
    status: str
    thumbnail_path: str | None
    created_at: object | None = None
    is_favorited: bool = False
    favorite_count: int = 0


class BoardListResponse(BaseModel):
    items: list[BoardListItem]
    total: int
    page: int
    page_size: int
    pages: int


class BoardDetailOut(BaseModel):
    board_id: int
    user_id: str
    seller_name: str
    title: str
    price: int
    description: str | None
    location: str | None
    trade_type: str
    status: str
    images: list[BoardImageOut]
    created_at: object | None = None
    updated_at: object | None = None
    is_favorited: bool = False
    is_owner: bool = False
    my_purchase_request_status: str | None = None
    favorite_count: int = 0


class BoardUpdate(BaseModel):
    title: str | None = Field(None, min_length=1, max_length=200)
    price: int | None = Field(None, ge=0)
    description: str | None = None
    location: str | None = Field(None, max_length=255)
    trade_type: Literal["DIRECT", "DELIVERY", "BOTH"] | None = None


class BoardStatusUpdate(BaseModel):
    status: Literal["ON_SALE", "RESERVED", "SOLD"]


class PurchaseRequestOut(BaseModel):
    id: int
    board_id: int
    buyer_id: str
    buyer_name: str
    status: str
    created_at: object | None = None


class PurchaseRequestStatusUpdate(BaseModel):
    status: Literal["ACCEPTED", "REJECTED"]


class ReportCreate(BaseModel):
    reason: str = Field(..., min_length=1, max_length=2000)


class WantedPostOut(BaseModel):
    wanted_id: int
    user_id: str
    author_name: str
    title: str
    description: str | None
    max_price: int | None
    preferred_location: str | None
    created_at: object | None = None
    updated_at: object | None = None
    is_owner: bool = False

    model_config = {"from_attributes": True}


class WantedPostCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    description: str | None = None
    max_price: int | None = Field(None, ge=0)
    preferred_location: str | None = Field(None, max_length=255)


class WantedPostUpdate(BaseModel):
    title: str | None = Field(None, min_length=1, max_length=200)
    description: str | None = None
    max_price: int | None = Field(None, ge=0)
    preferred_location: str | None = Field(None, max_length=255)


class WantedListResponse(BaseModel):
    items: list[WantedPostOut]
    total: int
    page: int
    page_size: int
    pages: int


class FeedItemOut(BaseModel):
    """홈 거래 피드: 판매글(board) + 구매 희망글(wanted) 통합."""

    kind: Literal["board", "wanted"]
    board_id: int | None = None
    wanted_id: int | None = None
    title: str
    price: int | None = None
    created_at: object | None = None
    author_name: str
    location: str | None = None
    thumbnail_path: str | None = None
    status: str | None = None
    trade_type: str | None = None
    is_favorited: bool = False
    favorite_count: int = 0
    is_owner: bool = False


class FeedListResponse(BaseModel):
    items: list[FeedItemOut]
    total: int
    page: int
    page_size: int
    pages: int


# --- Chat (거래 1:1) ---


class OpenChatRoomRequest(BaseModel):
    kind: Literal["board", "wanted"]
    board_id: int | None = None
    wanted_id: int | None = None


class ChatRoomOpenOut(BaseModel):
    room_id: int


class ChatRoomSummaryOut(BaseModel):
    room_id: int
    listing_kind: Literal["board", "wanted"]
    peer_user_id: str
    peer_name: str
    listing_title: str
    listing_price: int | None
    thumbnail_path: str | None = None
    last_message_preview: str | None = None
    last_message_at: object | None = None
    closed_at: object | None = None


class ChatMessageOut(BaseModel):
    message_id: int
    sender_id: str
    body: str
    created_at: object | None = None


class ChatMessagesResponse(BaseModel):
    messages: list[ChatMessageOut]


class SendChatMessageRequest(BaseModel):
    body: str = Field(..., min_length=1, max_length=2000)
