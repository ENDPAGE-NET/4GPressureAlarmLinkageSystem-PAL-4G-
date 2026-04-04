import { computed } from 'vue'

import { messages } from '@/i18n/messages'
import { useSettingsStore } from '@/stores/settings'

function resolvePath(path: string, locale: string) {
  const segments = path.split('.')
  let current: any = messages[locale as keyof typeof messages]

  for (const segment of segments) {
    if (current && typeof current === 'object' && segment in current) {
      current = current[segment]
    } else {
      return path
    }
  }

  return typeof current === 'string' ? current : path
}

export function useI18n() {
  const settingsStore = useSettingsStore()

  const locale = computed(() => settingsStore.localeCode)

  function t(path: string) {
    return resolvePath(path, locale.value)
  }

  return {
    locale,
    t,
  }
}
