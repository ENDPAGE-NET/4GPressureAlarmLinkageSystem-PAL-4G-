import { computed, onBeforeUnmount, onMounted } from 'vue'

import { useI18n } from './useI18n'
import { useSettingsStore } from '@/stores/settings'

let socket: WebSocket | null = null
let socketInitialized = false
let subscriberCount = 0

function initializeSocket(settingsStore: ReturnType<typeof useSettingsStore>) {
  if (socketInitialized || !settingsStore.wsUrl) {
    return
  }

  socketInitialized = true
  settingsStore.setRealtimeState('connecting')

  try {
    socket = new WebSocket(settingsStore.wsUrl)

    socket.addEventListener('open', () => {
      settingsStore.setRealtimeState('connected')
    })

    socket.addEventListener('close', () => {
      settingsStore.setRealtimeState('fallback')
      socket = null
      socketInitialized = false
    })

    socket.addEventListener('error', () => {
      settingsStore.setRealtimeState('error')
    })
  } catch {
    settingsStore.setRealtimeState('error')
    socket = null
    socketInitialized = false
  }
}

export function useRealtime(channelName?: string) {
  const settingsStore = useSettingsStore()
  const { t } = useI18n()

  const statusLabel = computed(() => {
    switch (settingsStore.realtimeStatus) {
      case 'connected':
        return t('realtime.connected')
      case 'connecting':
        return t('realtime.connecting')
      case 'error':
        return t('realtime.error')
      case 'fallback':
        return t('realtime.fallback')
      default:
        return t('realtime.unsupported')
    }
  })

  onMounted(() => {
    if (!settingsStore.realtimeEnabled) {
      settingsStore.setRealtimeState(
        'unsupported',
        `${channelName || 'default'} polling mode`,
      )
      return
    }

    subscriberCount += 1
    initializeSocket(settingsStore)
  })

  onBeforeUnmount(() => {
    if (!settingsStore.realtimeEnabled) {
      return
    }

    subscriberCount = Math.max(0, subscriberCount - 1)
    if (subscriberCount === 0) {
      socket?.close()
      socket = null
      socketInitialized = false
    }
  })

  return {
    realtimeStatus: computed(() => settingsStore.realtimeStatus),
    realtimeStatusLabel: statusLabel,
  }
}
