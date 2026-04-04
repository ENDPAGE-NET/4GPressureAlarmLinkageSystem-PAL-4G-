import { computed, ref } from 'vue'
import { defineStore } from 'pinia'

import type { LocaleCode, RealtimeStatus, ThemeMode } from '@/types/domain'

const THEME_KEY = 'pal4g-theme-mode'
const LOCALE_KEY = 'pal4g-locale'
const WS_URL = import.meta.env.VITE_WS_URL || ''

export const useSettingsStore = defineStore('settings', () => {
  const themeMode = ref<ThemeMode>((localStorage.getItem(THEME_KEY) as ThemeMode) || 'dark')
  const localeCode = ref<LocaleCode>((localStorage.getItem(LOCALE_KEY) as LocaleCode) || 'zh-CN')
  const realtimeStatus = ref<RealtimeStatus>(WS_URL ? 'fallback' : 'unsupported')
  const realtimeMessage = ref('')

  const wsUrl = computed(() => WS_URL)
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
