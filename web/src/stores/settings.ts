import { computed, ref } from 'vue'
import { defineStore } from 'pinia'

import type { LocaleCode, RealtimeStatus, ThemeMode } from '@/types/domain'

const THEME_KEY = 'pal4g-theme-mode'
const LOCALE_KEY = 'pal4g-locale'

function resolveWsUrl() {
  const explicitUrl = String(import.meta.env.VITE_WS_URL || '').trim()
  if (explicitUrl) {
    return explicitUrl
  }

  if (typeof window === 'undefined') {
    return ''
  }

  const apiBase = String(import.meta.env.VITE_API_BASE || '/api/v1').trim()
  if (!apiBase) {
    return ''
  }

  try {
    const wsUrl = new URL(apiBase, window.location.origin)
    wsUrl.protocol = wsUrl.protocol === 'https:' ? 'wss:' : 'ws:'
    wsUrl.pathname = `${wsUrl.pathname.replace(/\/$/, '')}/ws/events`
    wsUrl.search = ''
    return wsUrl.toString()
  } catch {
    return ''
  }
}

export const useSettingsStore = defineStore('settings', () => {
  const themeMode = ref<ThemeMode>((localStorage.getItem(THEME_KEY) as ThemeMode) || 'dark')
  const localeCode = ref<LocaleCode>((localStorage.getItem(LOCALE_KEY) as LocaleCode) || 'zh-CN')
  const realtimeStatus = ref<RealtimeStatus>(resolveWsUrl() ? 'fallback' : 'unsupported')
  const realtimeMessage = ref('')

  const wsUrl = computed(() => resolveWsUrl())
  const realtimeEnabled = computed(() => Boolean(wsUrl.value))

  function setTheme(mode: ThemeMode) {
    themeMode.value = mode
    localStorage.setItem(THEME_KEY, mode)
  }

  function toggleTheme() {
    setTheme(themeMode.value === 'dark' ? 'light' : 'dark')
  }

  function setLocale(locale: LocaleCode) {
    localeCode.value = locale
    localStorage.setItem(LOCALE_KEY, locale)
  }

  function setRealtimeState(status: RealtimeStatus, message = '') {
    realtimeStatus.value = status
    realtimeMessage.value = message
  }

  return {
    localeCode,
    realtimeEnabled,
    realtimeMessage,
    realtimeStatus,
    themeMode,
    wsUrl,
    setLocale,
    setRealtimeState,
    setTheme,
    toggleTheme,
  }
})
