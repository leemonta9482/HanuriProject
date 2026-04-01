import { computed, ref } from 'vue'
import { defineStore } from 'pinia'

import { fetchCurrentUser, loginUser } from '@/api/auth'
import type { LoginUserInfo } from '@/api/types'

const TOKEN_KEY = 'hanuri_token'
const USER_KEY = 'hanuri_user'

function loadStoredUser(): LoginUserInfo | null {
  try {
    const raw = localStorage.getItem(USER_KEY)
    if (!raw) return null
    const u = JSON.parse(raw) as Partial<LoginUserInfo>
    if (!u.user_id || !u.email) return null
    return {
      user_id: u.user_id,
      name: typeof u.name === 'string' ? u.name.trim() : '',
      email: u.email,
      is_admin: Boolean(u.is_admin),
      profile_image_path:
        typeof u.profile_image_path === 'string' && u.profile_image_path.trim()
          ? u.profile_image_path.trim()
          : null,
    }
  } catch {
    return null
  }
}

export const useAuthStore = defineStore('auth', () => {
  const token = ref<string | null>(localStorage.getItem(TOKEN_KEY))
  const user = ref<LoginUserInfo | null>(loadStoredUser())

  const isLoggedIn = computed(() => Boolean(token.value))
  const isAdmin = computed(() => Boolean(user.value?.is_admin))

  function setSession(accessToken: string, u: LoginUserInfo) {
    token.value = accessToken
    user.value = u
    localStorage.setItem(TOKEN_KEY, accessToken)
    localStorage.setItem(USER_KEY, JSON.stringify(u))
  }

  function logout() {
    token.value = null
    user.value = null
    localStorage.removeItem(TOKEN_KEY)
    localStorage.removeItem(USER_KEY)
  }

  async function login(userId: string, password: string) {
    const data = await loginUser({ user_id: userId, password })
    setSession(data.access_token, data.user)
  }

  /** 토큰이 있으면 서버에서 최신 프로필(이름 등)을 받아 저장합니다. */
  async function hydrateFromServer() {
    const t = token.value ?? localStorage.getItem(TOKEN_KEY)
    if (!t) return
    try {
      const u = await fetchCurrentUser()
      setSession(t, u)
    } catch {
      logout()
    }
  }

  return { token, user, isLoggedIn, isAdmin, setSession, logout, login, hydrateFromServer }
})
