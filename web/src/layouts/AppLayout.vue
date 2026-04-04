<template>
  <div class="layout-shell" :class="{ 'layout-shell--menu-open': menuOpen }">
    <aside class="layout-sidebar">
      <div class="layout-brand">
        <div class="layout-brand__mark">PAL</div>
        <div>
          <strong>{{ t('app.name') }}</strong>
          <p>{{ t('app.subtitle') }}</p>
        </div>
      </div>

      <div class="layout-nav-groups">
        <section v-for="section in navSections" :key="section.key" class="layout-nav-group">
          <div class="layout-nav-group__title">{{ t(section.titleKey) }}</div>
          <el-menu
            :default-active="route.path"
            class="layout-menu"
            background-color="transparent"
            text-color="#8faab6"
            active-text-color="#d7e2e9"
            router
          >
            <el-menu-item
              v-for="item in section.routes"
              :key="item.path"
              :index="item.path"
              @click="menuOpen = false"
            >
              <el-icon><component :is="resolveIcon(item.meta.navIcon)" /></el-icon>
              <span>{{ item.meta.navLabelKey ? t(item.meta.navLabelKey) : item.meta.navLabel }}</span>
            </el-menu-item>
          </el-menu>
        </section>
      </div>

      <div class="layout-sidebar__footer">
        <div class="layout-role">{{ roleLabel }}</div>
        <span>{{ authStore.profile?.username }}</span>
      </div>
    </aside>

    <div class="layout-backdrop" @click="menuOpen = false" />

    <div class="layout-main">
      <header class="layout-header">
        <div class="layout-header__left">
          <el-button class="layout-header__menu" circle @click="menuOpen = !menuOpen">
            <el-icon><Menu /></el-icon>
          </el-button>
          <div>
            <div class="layout-header__eyebrow">{{ t('app.phase') }}</div>
            <h1>{{ pageTitle }}</h1>
          </div>
        </div>

        <div class="layout-header__right">
          <el-dropdown trigger="click">
            <span class="layout-user">
              {{ currentLocaleLabel }}
              <el-icon><ArrowDown /></el-icon>
            </span>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item
                  v-for="locale in localeOptions"
                  :key="locale.value"
                  @click="settingsStore.setLocale(locale.value)"
                >
                  {{ locale.label }}
                </el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
          <el-button plain @click="settingsStore.toggleTheme()">
            {{ currentThemeLabel }}
          </el-button>
          <el-tag type="primary" effect="dark" round>{{ roleLabel }}</el-tag>
          <el-dropdown trigger="click">
            <span class="layout-user">
              {{ authStore.profile?.username }}
              <el-icon><ArrowDown /></el-icon>
            </span>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item @click="router.push('/profile')">{{ t('auth.profile') }}</el-dropdown-item>
                <el-dropdown-item divided @click="handleLogout">{{ t('auth.logout') }}</el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </div>
      </header>

      <main class="layout-content">
        <div class="section-banner" style="margin-bottom: 20px">
          <div>
            <strong>{{ settingsStore.realtimeEnabled ? t('common.realtime') : t('common.realtimePolling') }}</strong>
            <div style="margin-top: 4px; color: var(--pal-text-muted)">
              {{ realtimeStatusLabel }}
            </div>
          </div>
          <div class="section-banner__meta">
            <el-tag :type="realtimeTagType" effect="dark" round>{{ realtimeStatusLabel }}</el-tag>
            <el-tag effect="plain" round>{{ settingsStore.themeMode }}</el-tag>
            <el-tag effect="plain" round>{{ settingsStore.localeCode }}</el-tag>
          </div>
        </div>
        <router-view />
      </main>
    </div>
  </div>
</template>

<script setup lang="ts">
import {
  ArrowDown,
  Bell,
  Clock,
  Connection,
  DataBoard,
  DataAnalysis,
  Download,
  FolderOpened,
  Menu,
  Monitor,
  Setting,
  Tickets,
  User,
} from '@element-plus/icons-vue'
import { computed, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'

import { useI18n } from '@/composables/useI18n'
import { useRealtime } from '@/composables/useRealtime'
import { useAuthStore } from '@/stores/auth'
import { useSettingsStore } from '@/stores/settings'
import { localeLabels, themeLabels } from '@/i18n/messages'

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()
const settingsStore = useSettingsStore()
const { t } = useI18n()
const { realtimeStatus, realtimeStatusLabel } = useRealtime('layout')
const menuOpen = ref(false)

const iconRegistry = {
  Bell,
  Clock,
  Connection,
  DataBoard,
  DataAnalysis,
  Download,
  FolderOpened,
  Monitor,
  Setting,
  Tickets,
  User,
}

const navigationRoutes = computed(() => {
  const currentRole = authStore.profile?.role
  return router
    .getRoutes()
    .filter((item) => item.meta.navLabelKey)
    .filter((item) => !item.meta.adminOnly || currentRole === 'super_admin')
    .sort((a, b) => (a.meta.navOrder || 99) - (b.meta.navOrder || 99))
})

const navSections = computed(() =>
  ['business', 'admin', 'ops']
    .map((section) => ({
      key: section,
      titleKey: `nav.${section}`,
      routes: navigationRoutes.value.filter((item) => item.meta.navSection === section),
    }))
    .filter((section) => section.routes.length > 0),
)

const roleLabel = computed(() => {
  const role = authStore.profile?.role
  const resolved = t(`roles.${role || 'guest'}`)
  return resolved === `roles.${role || 'guest'}` ? role || t('roles.guest') : resolved
})

const pageTitle = computed(() => {
  if (route.meta.titleKey) {
    return t(route.meta.titleKey)
  }
  return route.meta.title || t('app.name')
})

const localeOptions = computed(() =>
  Object.entries(localeLabels).map(([value, label]) => ({
    value: value as keyof typeof localeLabels,
    label,
  })),
)

const currentLocaleLabel = computed(() => localeLabels[settingsStore.localeCode])
const currentThemeLabel = computed(() => themeLabels[settingsStore.themeMode][settingsStore.localeCode])
const realtimeTagType = computed(() => {
  if (realtimeStatus.value === 'connected') return 'success'
  if (realtimeStatus.value === 'connecting') return 'warning'
  if (realtimeStatus.value === 'error') return 'danger'
  return 'info'
})

function resolveIcon(name?: string) {
  if (!name) {
    return Monitor
  }
  return iconRegistry[name as keyof typeof iconRegistry] || Monitor
}

function handleLogout() {
  authStore.logout()
  router.push('/login')
}
</script>

<style scoped>
.layout-shell {
  position: relative;
  min-height: 100vh;
  display: grid;
  grid-template-columns: 280px minmax(0, 1fr);
}

.layout-sidebar {
  position: sticky;
  top: 0;
  display: flex;
  flex-direction: column;
  gap: 26px;
  height: 100vh;
  padding: 24px 20px;
  border-right: 1px solid var(--pal-line);
  background:
    linear-gradient(180deg, rgba(6, 18, 25, 0.94), rgba(8, 23, 31, 0.98)),
    radial-gradient(circle at top, rgba(51, 198, 216, 0.08), transparent 35%);
  backdrop-filter: blur(18px);
}

.layout-brand {
  display: flex;
  gap: 14px;
  align-items: center;
  padding: 14px;
  border-radius: var(--pal-radius-lg);
  border: 1px solid var(--pal-line);
  background: rgba(255, 255, 255, 0.03);
}

.layout-brand strong {
  display: block;
  font-size: 1rem;
}

.layout-brand p {
  margin: 4px 0 0;
  color: var(--pal-text-muted);
  font-size: 0.82rem;
}

.layout-brand__mark {
  width: 48px;
  height: 48px;
  border-radius: 16px;
  display: grid;
  place-items: center;
  font-family:
    'DIN Alternate',
    'Bahnschrift',
    sans-serif;
  font-weight: 700;
  letter-spacing: 0.12em;
  color: #031218;
  background: linear-gradient(135deg, var(--pal-primary), #8fe6ef);
}

.layout-menu {
  border-right: none;
}

.layout-menu :deep(.el-menu-item) {
  margin-bottom: 10px;
  height: 48px;
  border-radius: 14px;
}

.layout-nav-groups {
  display: grid;
  gap: 18px;
  flex: 1;
  overflow-y: auto;
}

.layout-nav-group__title {
  margin: 0 0 8px;
  color: var(--pal-accent);
  font-size: 0.78rem;
  letter-spacing: 0.16em;
  text-transform: uppercase;
}

.layout-menu :deep(.el-menu-item.is-active) {
  background: linear-gradient(90deg, rgba(21, 123, 144, 0.85), rgba(51, 198, 216, 0.22));
}

.layout-sidebar__footer {
  display: grid;
  gap: 4px;
  padding: 14px;
  border-radius: var(--pal-radius-md);
  border: 1px solid var(--pal-line);
  color: var(--pal-text-muted);
  background: rgba(255, 255, 255, 0.02);
}

.layout-role {
  color: var(--pal-accent);
  font-size: 0.82rem;
}

.layout-main {
  min-width: 0;
}

.layout-header {
  position: sticky;
  top: 0;
  z-index: 5;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 18px;
  padding: 18px 28px;
  background: rgba(5, 19, 28, 0.72);
  backdrop-filter: blur(18px);
  border-bottom: 1px solid var(--pal-line);
}

.layout-header__left,
.layout-header__right {
  display: flex;
  align-items: center;
  gap: 14px;
}

.layout-header__eyebrow {
  color: var(--pal-accent);
  font-size: 0.8rem;
  text-transform: uppercase;
  letter-spacing: 0.16em;
}

.layout-header h1 {
  margin: 4px 0 0;
  font-size: 1.35rem;
  font-family:
    'DIN Alternate',
    'Bahnschrift',
    'Noto Sans SC',
    sans-serif;
}

.layout-content {
  padding: 28px;
}

.layout-user {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  color: var(--pal-text);
  cursor: pointer;
}

.layout-header__menu,
.layout-backdrop {
  display: none;
}

@media (max-width: 960px) {
  .layout-shell {
    grid-template-columns: 1fr;
  }

  .layout-header__menu,
  .layout-backdrop {
    display: inline-flex;
  }

  .layout-sidebar {
    position: fixed;
    z-index: 12;
    width: 280px;
    transform: translateX(-100%);
    transition: transform 0.24s ease;
  }

  .layout-shell--menu-open .layout-sidebar {
    transform: translateX(0);
  }

  .layout-backdrop {
    position: fixed;
    inset: 0;
    z-index: 11;
    background: rgba(2, 10, 15, 0.52);
    opacity: 0;
    pointer-events: none;
    transition: opacity 0.24s ease;
  }

  .layout-shell--menu-open .layout-backdrop {
    opacity: 1;
    pointer-events: auto;
  }

  .layout-header,
  .layout-content {
    padding-left: 18px;
    padding-right: 18px;
  }

  .layout-header {
    align-items: flex-start;
  }
}
</style>
