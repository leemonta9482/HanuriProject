from typing import Literal

from pydantic import BaseModel, EmailStr, Field


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


class StudentIdVerifyResponse(BaseModel):
    verified: bool = True
    verification_token: str


class UserIdAvailabilityResponse(BaseModel):
    available: bool


class RegistrationEmailCodeSendBody(BaseModel):
    email: EmailStr


class RegistrationEmailCodeSendResponse(BaseModel):
    challenge_token: str


class RegistrationEmailCodeVerifyBody(BaseModel):
    challenge_token: str = Field(..., min_length=10)
    code: str = Field(..., min_length=1, max_length=32)


class RegistrationEmailCodeVerifyResponse(BaseModel):
    email_verification_token: str


class LoginUserInfo(BaseModel):
    user_id: str
    name: str
    email: str
    school_name: str
    is_admin: bool = False
    profile_image_path: str | None = None


class LoginResponse(BaseModel):
    """POST /api/auth/login 성공 시 액세스 토큰과 사용자 정보."""

    access_token: str
    token_type: str = "bearer"
    user: LoginUserInfo


class UserProfileOut(BaseModel):
    user_id: str
    name: str
    email: str
    school_name: str
    phone: str
    interest_major: str | None
    profile_image_path: str | None
    is_admin: bool = False


class PasswordChangeBody(BaseModel):
    current_password: str = Field(..., min_length=1, max_length=128)
    new_password: str = Field(..., min_length=8, max_length=128)


class PasswordResetRequestBody(BaseModel):
    user_id: str = Field(..., min_length=1, max_length=50)
    email: EmailStr


class PasswordResetRequestResponse(BaseModel):
    """성공 여부와 관계없이 동일 문구로 응답(계정 존재·이메일 일치 노출 방지)."""

    message: str = (
        "요청을 접수했습니다. 입력하신 이메일이 계정 정보와 일치하면 비밀번호 재설정 안내 메일이 발송됩니다."
    )


class PasswordResetStatusResponse(BaseModel):
    valid: bool
    detail: str | None = None


class PasswordResetConfirmBody(BaseModel):
    token: str = Field(..., min_length=10)
    new_password: str = Field(..., min_length=8, max_length=128)


class PasswordResetConfirmResponse(BaseModel):
    ok: bool = True
    message: str = "비밀번호가 변경되었습니다. 새 비밀번호로 로그인해 주세요."


class UserNotificationOut(BaseModel):
    notification_id: int
    kind: Literal["CHAT_MESSAGE", "BOARD_FAVORITED"]
    room_id: int | None = None
    board_id: int | None = None
    title: str
    body: str
    created_at: object | None = None
    read_at: object | None = None

    model_config = {"from_attributes": True}


class UserNotificationListResponse(BaseModel):
    items: list[UserNotificationOut]


class AdminUserOut(BaseModel):
    """관리자 회원 목록·상세 응답. 비밀번호는 포함하지 않습니다."""

    user_id: str
    name: str
    school_name: str
    phone: str
    email: str
    student_id: str | None = None
    student_verified: bool
    manner_score: float
    trust_score: float
    interest_major: str | None = None
    account_status: str
    is_admin: bool
    registration_status: str
    student_id_card_path: str
    profile_image_path: str | None = None
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
    # 가입 승인 거절(REJECTED) 시 안내 메일에 포함될 사유 (선택)
    rejection_reason: str | None = Field(None, max_length=500)


class AdminUserPatchResult(BaseModel):
    """회원 PATCH 결과. 계정이 삭제된 경우 user 는 null 입니다."""

    deleted: bool = False
    email_sent: bool = False
    user: AdminUserOut | None = None


class SchoolOut(BaseModel):
    school_id: int
    name: str
    region: str | None = None
    is_active: bool = True
    created_at: object | None = None
    updated_at: object | None = None

    model_config = {"from_attributes": True}


class AdminSchoolListResponse(BaseModel):
    items: list[SchoolOut]
    total: int
    page: int
    page_size: int
    pages: int


class AdminSchoolCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    region: str | None = Field(None, max_length=100)
    is_active: bool = True


class AdminSchoolUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=100)
    region: str | None = Field(None, max_length=100)
    is_active: bool | None = None


class PublicSchoolItem(BaseModel):
    school_id: int
    name: str
    region: str | None = None

    model_config = {"from_attributes": True}


class PublicSchoolListResponse(BaseModel):
    items: list[PublicSchoolItem]


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


class AdminWantedOut(BaseModel):
    wanted_id: int
    user_id: str
    title: str
    description: str | None = None
    max_price: int | None = None
    preferred_location: str | None = None
    created_at: object | None = None
    updated_at: object | None = None

    model_config = {"from_attributes": True}


class AdminWantedListResponse(BaseModel):
    items: list[AdminWantedOut]
    total: int
    page: int
    page_size: int
    pages: int


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
    seller_profile_image_path: str | None = None
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
    shop_owner_name: str | None = None
    shop_owner_profile_image_path: str | None = None


class BoardDetailOut(BaseModel):
    board_id: int
    user_id: str
    seller_name: str
    seller_profile_image_path: str | None = None
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
    favorite_count: int = 0


class BoardUpdate(BaseModel):
    title: str | None = Field(None, min_length=1, max_length=200)
    price: int | None = Field(None, ge=0)
    description: str | None = None
    location: str | None = Field(None, max_length=255)
    trade_type: Literal["DIRECT", "DELIVERY", "BOTH"] | None = None


class BoardStatusUpdate(BaseModel):
    status: Literal["ON_SALE", "RESERVED", "SOLD"]


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
    author_user_id: str | None = None
    author_profile_image_path: str | None = None
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
    listing_id: int
    peer_user_id: str
    peer_name: str
    listing_title: str
    listing_price: int | None
    thumbnail_path: str | None = None
    last_message_preview: str | None = None
    last_message_at: object | None = None
    closed_at: object | None = None
    i_am_peer: bool = False
    initiator_blocked_by_me: bool = False
    i_am_blocked_by_peer: bool = False


class BlockUserCreate(BaseModel):
    blocked_user_id: str = Field(..., min_length=1, max_length=50)


class UserBlockEntryOut(BaseModel):
    blocked_user_id: str
    blocked_name: str
    created_at: object | None = None


class ChatMessageOut(BaseModel):
    message_id: int
    sender_id: str
    body: str
    created_at: object | None = None


class ChatRoomClosedInfo(BaseModel):
    """종료된 방의 하단 안내. DB에는 누가 끊었는지 저장하지 않으므로 문구는 항상 동일합니다."""
    notice_text: str = "대화가 종료되었습니다."


class ChatMessagesResponse(BaseModel):
    messages: list[ChatMessageOut]
    room_closed: ChatRoomClosedInfo | None = None


class SendChatMessageRequest(BaseModel):
    body: str = Field(..., min_length=1, max_length=2000)
