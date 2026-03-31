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
