export interface RegisterPayload {
  user_id: string
  password: string
  name: string
  school_name: string
  phone: string
  email: string
  student_id?: string | null
  interest_major?: string | null
}

/** multipart 회원가입 (학생증 이미지 필수) */
export type RegisterWithStudentCardPayload = RegisterPayload & {
  student_id_card: File
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
  is_admin: boolean
}

export interface LoginResponse {
  access_token: string
  token_type: string
  user: LoginUserInfo
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

export interface AdminBoardListResponse {
  items: AdminBoard[]
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
  title: string
  price: number
  location: string | null
  trade_type: TradeType
  status: BoardStatus
  thumbnail_path: string | null
  created_at?: string | null
  is_favorited: boolean
}

export interface BoardListResponse {
  items: BoardListItem[]
  total: number
  page: number
  page_size: number
  pages: number
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
  my_purchase_request_status: string | null
}

export interface BoardUpdatePayload {
  title?: string
  price?: number
  description?: string | null
  location?: string | null
  trade_type?: TradeType
}

export interface PurchaseRequest {
  id: number
  board_id: number
  buyer_id: string
  buyer_name: string
  status: string
  created_at?: string | null
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
  location: string | null
  thumbnail_path: string | null
  status: string | null
  trade_type: string | null
  is_favorited: boolean
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

/** 채팅 목록 */
export interface ChatRoomSummary {
  room_id: number
  listing_kind: 'board' | 'wanted'
  peer_user_id: string
  peer_name: string
  listing_title: string
  listing_price: number | null
  thumbnail_path: string | null
  last_message_preview: string | null
  last_message_at?: string | null
  /** 설정 시 대화 종료(메시지 전송 불가) */
  closed_at?: string | null
}

export interface ChatMessage {
  message_id: number
  sender_id: string
  body: string
  created_at?: string | null
}
