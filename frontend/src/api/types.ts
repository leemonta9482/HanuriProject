export interface RegisterPayload {
  user_id: string
  password: string
  name: string
  phone: string
  email: string
  student_id?: string | null
  interest_major?: string | null
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
}

export interface LoginResponse {
  access_token: string
  token_type: string
  user: LoginUserInfo
}
