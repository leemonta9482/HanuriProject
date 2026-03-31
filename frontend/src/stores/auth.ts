import { computed, ref } from 'vue'
import { defineStore } from 'pinia'

import { loginUser } from '@/api/auth'
import type { LoginUserInfo } from '@/api/types'

const TOKEN_KEY = 'hanuri_token'
const USER_KEY = 'hanuri_user'

function loadStoredUser(): LoginUserInfo | null {
  try {
    const raw = localStorage.getItem(USER_KEY)
    if (!raw) return null
    const u = JSON.parse(raw) as Partial<LoginUserInfo>
    if (!u.user_id || !u.name || !u.email) return null
    return {
      user_id: u.user_id,
      name: u.name,
      email: u.email,
      is_admin: Boolean(u.is_admin),
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

  return { token, user, isLoggedIn, isAdmin, setSession, logout, login }
})
