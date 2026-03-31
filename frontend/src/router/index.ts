import { createRouter, createWebHistory } from 'vue-router'

import { useAuthStore } from '@/stores/auth'
import HomeView from '../views/HomeView.vue'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/',
      name: 'home',
      component: HomeView,
    },
    {
      path: '/boards/new',
      redirect: { name: 'post-write' },
    },
    {
      path: '/write',
      name: 'post-write',
      component: () => import('../views/PostCreateView.vue'),
      meta: { requiresAuth: true },
    },
    {
      path: '/boards/:id/edit',
      name: 'board-edit',
      component: () => import('../views/BoardFormView.vue'),
      meta: { requiresAuth: true },
    },
    {
      path: '/boards/:id',
      name: 'board-detail',
      component: () => import('../views/BoardDetailView.vue'),
    },
    {
      path: '/favorites',
      name: 'favorites',
      component: () => import('../views/FavoritesView.vue'),
      meta: { requiresAuth: true },
    },
    {
      path: '/my-shop',
      name: 'my-shop',
      component: () => import('../views/MyShopView.vue'),
      meta: { requiresAuth: true },
    },
    {
      path: '/chat',
      name: 'chat',
      component: () => import('../views/ChatView.vue'),
      meta: { requiresAuth: true },
    },
    {
      path: '/wanted',
      redirect: '/',
    },
    {
      path: '/wanted/:id',
      name: 'wanted-detail',
      component: () => import('../views/WantedDetailView.vue'),
      meta: { requiresAuth: true },
    },
    {
      path: '/login',
      name: 'login',
      component: () => import('../views/LoginView.vue'),
    },
    {
      path: '/register',
      name: 'register',
      component: () => import('../views/RegisterView.vue'),
    },
    {
      path: '/admin',
      redirect: '/admin/users',
    },
    {
      path: '/admin/users',
      name: 'admin-users',
      component: () => import('../views/AdminUsersView.vue'),
      meta: { requiresAdmin: true },
    },
    {
      path: '/admin/boards',
      name: 'admin-boards',
      component: () => import('../views/AdminBoardsView.vue'),
      meta: { requiresAdmin: true },
    },
    {
      path: '/admin/reports',
      name: 'admin-reports',
      component: () => import('../views/AdminReportsView.vue'),
      meta: { requiresAdmin: true },
    },
  ],
})

router.beforeEach((to) => {
  const auth = useAuthStore()
  if (to.meta.requiresAdmin) {
    if (!auth.isLoggedIn) {
      return { name: 'login', query: { redirect: to.fullPath } }
    }
    if (!auth.isAdmin) {
      return { name: 'home' }
    }
  }
  if (to.meta.requiresAuth) {
    if (!auth.isLoggedIn) {
      return { name: 'login', query: { redirect: to.fullPath } }
    }
  }
})

export default router
