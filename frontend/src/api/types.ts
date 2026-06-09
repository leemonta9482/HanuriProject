export interface RegisterPayload {
  user_id: string
  password: string
  name: string
  school_name: string
  phone: string
  email: string
  student_id: string
  interest_major?: string | null
}

/** multipart 회원가입 (학생증 이미지 필수) */
export type RegisterWithStudentCardPayload = RegisterPayload & {
  student_id_card: File
  /** POST /api/auth/verify-student-id 로 발급 (이름·학교·이미지와 일치) */
  student_id_verification_token: string
  /** POST /api/auth/registration-email/verify 로 발급 */
  email_verification_token: string
}

export interface RegisterResponse {
  user_id: string
  name: string
  message?: string
}

export interface LoginPayload {
  user_id: string
  password: string
}

export interface LoginUserInfo {
  user_id: string
  name: string
  email: string
  school_name: string
  is_admin: boolean
  profile_image_path?: string | null
}

/** GET /api/auth/me/profile */
export interface UserProfile {
  user_id: string
  name: string
  email: string
  school_name: string
  phone: string
  interest_major: string | null
  profile_image_path: string | null
  is_admin: boolean
}

export interface LoginResponse {
  access_token: string
  token_type: string
  user: LoginUserInfo
}

export interface PasswordResetRequestResponse {
  message: string
}

export interface PasswordResetStatusResponse {
  valid: boolean
  detail?: string | null
}

export interface PasswordResetConfirmResponse {
  ok: boolean
  message: string
}

export interface AdminUser {
  user_id: string
  name: string
  phone: string
  email: string
  student_id: string | null
  student_verified: boolean
  manner_score: number
  trust_score: number
  interest_major: string | null
  account_status: string
  is_admin: boolean
  registration_status: string
  student_id_card_path: string
  created_at?: string | null
  updated_at?: string | null
}

export interface AdminUserListResponse {
  items: AdminUser[]
  total: number
  page: number
  page_size: number
  pages: number
}

export interface AdminUserUpdatePayload {
  name?: string
  school_name?: string
  phone?: string
  email?: string
  student_id?: string | null
  interest_major?: string | null
  manner_score?: number
  trust_score?: number
  student_verified?: boolean
  account_status?: 'ACTIVE' | 'DORMANT' | 'DELETED'
  registration_status?: 'PENDING' | 'APPROVED' | 'REJECTED'
  is_admin?: boolean
  /** registration_status === 'REJECTED' 일 때 안내 메일에 포함될 사유(선택) */
  rejection_reason?: string | null
}

/** PATCH /api/admin/users/{user_id} 응답.
 * 계정이 거절/삭제되어 사라진 경우 deleted=true, user=null 입니다. */
export interface AdminUserPatchResult {
  deleted: boolean
  email_sent: boolean
  user: AdminUser | null
}

export interface AdminBoard {
  board_id: number
  user_id: string
  title: string
  price: number
  status: string
  trade_type: string
  created_at?: string | null
  updated_at?: string | null
}

export interface School {
  school_id: number
  name: string
  region: string | null
  is_active: boolean
  created_at?: string | null
  updated_at?: string | null
}

export interface AdminSchoolListResponse {
  items: School[]
  total: number
  page: number
  page_size: number
  pages: number
}

export interface AdminSchoolCreatePayload {
  name: string
  region?: string | null
  is_active?: boolean
}

export interface AdminSchoolUpdatePayload {
  name?: string
  region?: string | null
  is_active?: boolean
}

export interface PublicSchoolItem {
  school_id: number
  name: string
  region: string | null
}

export interface PublicSchoolListResponse {
  items: PublicSchoolItem[]
}

/** GET /api/auth/user-id-available */
export interface UserIdAvailabilityResponse {
  available: boolean
}

export interface AdminBoardListResponse {
  items: AdminBoard[]
  total: number
  page: number
  page_size: number
  pages: number
}

export interface AdminWanted {
  wanted_id: number
  user_id: string
  title: string
  description?: string | null
  max_price?: number | null
  preferred_location?: string | null
  created_at?: string | null
  updated_at?: string | null
}

export interface AdminWantedListResponse {
  items: AdminWanted[]
  total: number
  page: number
  page_size: number
  pages: number
}

export interface AdminBoardUpdatePayload {
  title?: string
  price?: number
  status?: 'ON_SALE' | 'RESERVED' | 'SOLD'
  trade_type?: 'DIRECT' | 'DELIVERY' | 'BOTH'
}

export type AdminReportStatus = 'PENDING' | 'REVIEWED' | 'DISMISSED' | 'ACTION_TAKEN'

export interface AdminReport {
  report_id: number
  board_id: number
  board_title: string
  seller_id: string
  reporter_id: string
  reporter_name: string
  reason: string
  status: AdminReportStatus
  created_at?: string | null
  reviewed_at?: string | null
  reviewed_by?: string | null
  reviewer_name?: string | null
  admin_note?: string | null
}

export interface AdminReportListResponse {
  items: AdminReport[]
  total: number
  page: number
  page_size: number
  pages: number
}

export interface AdminReportUpdatePayload {
  status?: AdminReportStatus
  admin_note?: string | null
}

/** 판매 게시판 */
export type TradeType = 'DIRECT' | 'DELIVERY' | 'BOTH'
export type BoardStatus = 'ON_SALE' | 'RESERVED' | 'SOLD'

export interface BoardListItem {
  board_id: number
  user_id: string
  seller_name: string
  seller_profile_image_path?: string | null
  title: string
  price: number
  location: string | null
  trade_type: TradeType
  status: BoardStatus
  thumbnail_path: string | null
  created_at?: string | null
  is_favorited: boolean
  favorite_count: number
}

export interface BoardListResponse {
  items: BoardListItem[]
  total: number
  page: number
  page_size: number
  pages: number
  shop_owner_name?: string | null
  shop_owner_profile_image_path?: string | null
}

export interface BoardImage {
  image_id: number
  path: string
  sort_order: number
}

export interface BoardDetail {
  board_id: number
  user_id: string
  seller_name: string
  seller_profile_image_path?: string | null
  title: string
  price: number
  description: string | null
  location: string | null
  trade_type: TradeType
  status: BoardStatus
  images: BoardImage[]
  created_at?: string | null
  updated_at?: string | null
  is_favorited: boolean
  is_owner: boolean
  favorite_count: number
}

export interface BoardUpdatePayload {
  title?: string
  price?: number
  description?: string | null
  location?: string | null
  trade_type?: TradeType
}

export interface WantedPost {
  wanted_id: number
  user_id: string
  author_name: string
  title: string
  description: string | null
  max_price: number | null
  preferred_location: string | null
  created_at?: string | null
  updated_at?: string | null
  is_owner: boolean
}

/** 홈 피드: 판매 + 구매 희망 */
export type FeedKind = 'board' | 'wanted'

export interface FeedItem {
  kind: FeedKind
  board_id: number | null
  wanted_id: number | null
  title: string
  price: number | null
  created_at?: string | null
  author_name: string
  author_user_id?: string | null
  author_profile_image_path?: string | null
  location: string | null
  thumbnail_path: string | null
  status: string | null
  trade_type: string | null
  is_favorited: boolean
  favorite_count: number
  /** 판매글: 본인 게시글 여부 (찜 버튼 비활성) */
  is_owner: boolean
}

export interface FeedListResponse {
  items: FeedItem[]
  total: number
  page: number
  page_size: number
  pages: number
}

export interface WantedPostPayload {
  title: string
  description?: string | null
  max_price?: number | null
  preferred_location?: string | null
}

export interface WantedListResponse {
  items: WantedPost[]
  total: number
  page: number
  page_size: number
  pages: number
}

/** 채팅 목록 */
export interface ChatRoomSummary {
  room_id: number
  listing_kind: 'board' | 'wanted'
  listing_id: number
  peer_user_id: string
  peer_name: string
  listing_title: string
  listing_price: number | null
  thumbnail_path: string | null
  last_message_preview: string | null
  last_message_at?: string | null
  /** 설정 시 대화 종료(메시지 전송 불가) */
  closed_at?: string | null
  /** 내가 판매자(peer)인지 */
  i_am_peer?: boolean
  /** 판매자일 때 구매자를 내가 차단했는지 */
  initiator_blocked_by_me?: boolean
  /** 구매자일 때 판매자에게 차단당했는지 */
  i_am_blocked_by_peer?: boolean
}

/** GET /api/chat/blocks */
export interface BlockedUserEntry {
  blocked_user_id: string
  blocked_name: string
  created_at?: string | null
}

export interface ChatMessage {
  message_id: number
  sender_id: string
  body: string
  created_at?: string | null
}

/** 종료 안내(마지막 줄). 새로고침 후에는 API가 누가 끊었는지 구분하지 않음 */
export interface ChatRoomClosed {
  notice_text: string
}

/** GET /api/auth/me/notifications */
export interface UserNotificationItem {
  notification_id: number
  kind: 'CHAT_MESSAGE' | 'BOARD_FAVORITED'
  room_id: number | null
  board_id: number | null
  title: string
  body: string
  created_at?: string | null
  read_at?: string | null
}

export interface UserNotificationListResponse {
  items: UserNotificationItem[]
}
