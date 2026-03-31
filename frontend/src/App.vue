<script setup lang="ts">
import { RouterLink, RouterView } from 'vue-router'

import { useAuthStore } from '@/stores/auth'

const auth = useAuthStore()

function onLogout() {
  auth.logout()
}
</script>

<template>
  <div class="layout">
    <header class="header">
      <RouterLink to="/" class="brand">Hanuri</RouterLink>
      <nav class="nav">
        <RouterLink to="/">홈</RouterLink>
        <template v-if="auth.isLoggedIn">
          <RouterLink v-if="auth.isAdmin" to="/admin/users" class="admin-link">관리자 페이지</RouterLink>
          <span class="user"
            >{{ auth.user?.name }}님<span v-if="auth.isAdmin" class="badge">관리자</span></span
          >
          <button type="button" class="ghost" @click="onLogout">로그아웃</button>
        </template>
        <template v-else>
          <RouterLink to="/login">로그인</RouterLink>
          <RouterLink to="/register">회원가입</RouterLink>
        </template>
        <RouterLink to="/about">About</RouterLink>
      </nav>
    </header>
    <main class="main">
      <RouterView />
    </main>
  </div>
</template>

<style scoped>
.layout {
  display: flex;
  flex-direction: column;
  min-height: 100vh;
}

.header {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: space-between;
  gap: 1rem;
  padding-bottom: 1rem;
  margin-bottom: 0.5rem;
  border-bottom: 1px solid var(--color-border);
}

.brand {
  font-weight: 700;
  font-size: 1.25rem;
  color: var(--color-heading);
}

.nav {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 0.75rem 1rem;
  font-size: 0.95rem;
}

.nav a.router-link-exact-active {
  color: var(--color-heading);
  font-weight: 600;
}

.admin-link {
  font-weight: 600;
  font-size: 0.95rem;
}

.user {
  font-size: 0.9rem;
  color: var(--color-text);
}

.badge {
  margin-left: 0.35rem;
  padding: 0.1rem 0.4rem;
  font-size: 0.75rem;
  font-weight: 600;
  border-radius: 4px;
  background: hsla(160, 100%, 37%, 0.2);
  color: hsla(160, 100%, 28%, 1);
  vertical-align: middle;
}

.ghost {
  padding: 0.35rem 0.65rem;
  border-radius: 6px;
  border: 1px solid var(--color-border);
  background: transparent;
  color: var(--color-text);
  font-size: 0.9rem;
  cursor: pointer;
}

.ghost:hover {
  border-color: var(--color-border-hover);
}

.main {
  flex: 1;
  display: flex;
  flex-direction: column;
}
</style>
