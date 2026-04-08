import { createRouter, createWebHistory } from 'vue-router'
import type { RouteLocationNormalized } from 'vue-router'

import { messages } from '@/i18n/messages'
import { useAuthStore } from '@/stores/auth'
import { useSettingsStore } from '@/stores/settings'

declare module 'vue-router' {
  interface RouteMeta {
    title?: string
    titleKey?: string
    requiresAuth?: boolean
    guestOnly?: boolean
    navLabel?: string
    navLabelKey?: string
    navIcon?: string
    navOrder?: number
    navSection?: 'business' | 'admin'
    adminOnly?: boolean
  }
}

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/login',
      name: 'login',
      component: () => import('@/views/LoginView.vue'),
      meta: {
        titleKey: 'auth.login',
        guestOnly: true,
      },
    },
    {
      path: '/',
      component: () => import('@/layouts/AppLayout.vue'),
      meta: {
        requiresAuth: true,
      },
      children: [
        {
          path: '',
          redirect: '/dashboard',
        },
        {
          path: '/dashboard',
          name: 'dashboard',
          component: () => import('@/views/DashboardView.vue'),
          meta: {
            titleKey: 'dashboard.title',
            navLabelKey: 'nav.dashboard',
            navIcon: 'DataBoard',
            navOrder: 1,
            navSection: 'business',
            requiresAuth: true,
          },
        },
        {
          path: '/alarms',
          name: 'alarms',
          component: () => import('@/views/AlarmListView.vue'),
          meta: {
            titleKey: 'alarms.title',
            navLabelKey: 'nav.alarms',
            navIcon: 'Bell',
            navOrder: 2,
            navSection: 'business',
            requiresAuth: true,
          },
        },
        {
          path: '/devices',
          name: 'devices',
          component: () => import('@/views/DeviceListView.vue'),
          meta: {
            titleKey: 'devices.title',
            navLabelKey: 'nav.devices',
            navIcon: 'Monitor',
            navOrder: 3,
            navSection: 'business',
            requiresAuth: true,
          },
        },
        {
          path: '/devices/:id',
          name: 'device-detail',
          component: () => import('@/views/DeviceDetailView.vue'),
          meta: {
            titleKey: 'deviceDetail.title',
            requiresAuth: true,
          },
        },
        {
          path: '/admin/users',
          name: 'users',
          component: () => import('@/views/UserManagementView.vue'),
          meta: {
            titleKey: 'users.title',
            navLabelKey: 'nav.users',
            navIcon: 'User',
            navOrder: 11,
            navSection: 'admin',
            requiresAuth: true,
            adminOnly: true,
          },
        },
        {
          path: '/profile',
          name: 'profile',
          component: () => import('@/views/ProfileView.vue'),
          meta: {
            titleKey: 'profile.title',
            navLabelKey: 'nav.profile',
            navIcon: 'Setting',
            navOrder: 30,
            navSection: 'business',
            requiresAuth: true,
          },
        },
        {
          path: '/forbidden',
          name: 'forbidden',
          component: () => import('@/views/ForbiddenView.vue'),
          meta: {
            titleKey: 'auth.forbidden',
            requiresAuth: true,
          },
        },
      ],
    },
    {
      path: '/:pathMatch(.*)*',
      name: 'not-found',
      component: () => import('@/views/NotFoundView.vue'),
      meta: {
        titleKey: 'notFound.title',
      },
    },
  ],
})

function getRedirectPath(target: RouteLocationNormalized) {
  const path = target.fullPath === '/login' ? '/dashboard' : target.fullPath
  return `/login?redirect=${encodeURIComponent(path)}`
}

function resolveTitle(titleKey?: string, fallback?: string) {
  if (!titleKey) return fallback || 'PAL 4G'
  const settingsStore = useSettingsStore()
  const localeMessages = messages[settingsStore.localeCode]
  const segments = titleKey.split('.')
  let current: any = localeMessages

  for (const segment of segments) {
    current = current?.[segment]
  }

  return typeof current === 'string' ? current : fallback || titleKey
}

router.beforeEach(async (to) => {
  const authStore = useAuthStore()

  if (!authStore.bootstrapped) {
    await authStore.initialize()
  }

  if (to.meta.requiresAuth && !authStore.isAuthenticated) {
    return getRedirectPath(to)
  }

  if (to.meta.adminOnly && authStore.profile?.role !== 'super_admin') {
    return '/forbidden'
  }

  if (to.meta.guestOnly && authStore.isAuthenticated) {
    return '/dashboard'
  }

  document.title = `${resolveTitle('app.name', 'PAL 4G')} · ${resolveTitle(to.meta.titleKey, to.meta.title)}`
  return true
})

export default router
