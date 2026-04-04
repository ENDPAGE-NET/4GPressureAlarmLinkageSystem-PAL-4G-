import { computed, onBeforeUnmount, onMounted } from 'vue'

import { useI18n } from './useI18n'
import { useAuthStore } from '@/stores/auth'
import { useSettingsStore } from '@/stores/settings'
import type { RealtimeEventMessage } from '@/types/domain'

let socket: WebSocket | null = null
let socketInitialized = false
let subscriberCount = 0
let reconnectTimer: number | null = null
let heartbeatTimer: number | null = null
let socketManuallyClosed = false

const listeners = new Set<(message: RealtimeEventMessage) => void>()
const HEARTBEAT_INTERVAL = 25000
const RECONNECT_INTERVAL = 3000

function clearHeartbeat() {
  if (heartbeatTimer !== null) {
    window.clearInterval(heartbeatTimer)
    heartbeatTimer = null
  }
}

function clearReconnectTimer() {
  if (reconnectTimer !== null) {
    window.clearTimeout(reconnectTimer)
    reconnectTimer = null
  }
}

function notifyListeners(message: RealtimeEventMessage) {
  listeners.forEach((listener) => listener(message))
}

function buildSocketUrl(baseUrl: string, token: string) {
  const url = new URL(baseUrl, window.location.origin)
  if (url.protocol === 'http:') {
    url.protocol = 'ws:'
  } else if (url.protocol === 'https:') {
    url.protocol = 'wss:'
  }
  url.searchParams.set('token', token)
  return url.toString()
}

function startHeartbeat() {
  clearHeartbeat()
  heartbeatTimer = window.setInterval(() => {
    if (socket?.readyState === WebSocket.OPEN) {
      socket.send('ping')
    }
  }, HEARTBEAT_INTERVAL)
}

function scheduleReconnect(
  settingsStore: ReturnType<typeof useSettingsStore>,
  authStore: ReturnType<typeof useAuthStore>,
) {
  if (socketManuallyClosed || reconnectTimer !== null || subscriberCount === 0) {
    return
  }

  if (!settingsStore.realtimeEnabled || !authStore.token) {
    settingsStore.setRealtimeState('fallback')
    return
  }

  reconnectTimer = window.setTimeout(() => {
    reconnectTimer = null
    void initializeSocket(settingsStore, authStore)
  }, RECONNECT_INTERVAL)
}

function initializeSocket(
  settingsStore: ReturnType<typeof useSettingsStore>,
  authStore: ReturnType<typeof useAuthStore>,
) {
  if (socketInitialized || !settingsStore.wsUrl) {
    return
  }

  if (!authStore.token) {
    settingsStore.setRealtimeState('fallback')
    return
  }

  socketInitialized = true
  socketManuallyClosed = false
  clearReconnectTimer()
  settingsStore.setRealtimeState('connecting')

  try {
    socket = new WebSocket(buildSocketUrl(settingsStore.wsUrl, authStore.token))

    socket.addEventListener('open', () => {
      settingsStore.setRealtimeState('connected')
      startHeartbeat()
    })

    socket.addEventListener('message', (event) => {
      try {
        const payload = JSON.parse(event.data) as RealtimeEventMessage
        if (!payload || typeof payload.event !== 'string') {
          return
        }
        notifyListeners(payload)
      } catch {
        // Ignore malformed payloads and keep the connection alive.
      }
    })

    socket.addEventListener('close', () => {
      clearHeartbeat()
      socket = null
      socketInitialized = false
      if (!socketManuallyClosed) {
        settingsStore.setRealtimeState('fallback')
        scheduleReconnect(settingsStore, authStore)
      }
    })

    socket.addEventListener('error', () => {
      settingsStore.setRealtimeState('error')
      scheduleReconnect(settingsStore, authStore)
    })
  } catch {
    settingsStore.setRealtimeState('error')
    clearHeartbeat()
    socket = null
    socketInitialized = false
    scheduleReconnect(settingsStore, authStore)
  }
}

export function useRealtime(channelName?: string, onEvent?: (message: RealtimeEventMessage) => void) {
  const authStore = useAuthStore()
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
    if (onEvent) {
      listeners.add(onEvent)
    }

    if (!settingsStore.realtimeEnabled) {
      settingsStore.setRealtimeState(
        'unsupported',
        `${channelName || 'default'} polling mode`,
      )
      return
    }

    subscriberCount += 1
    initializeSocket(settingsStore, authStore)
  })

  onBeforeUnmount(() => {
    if (onEvent) {
      listeners.delete(onEvent)
    }

    if (!settingsStore.realtimeEnabled) {
      return
    }

    subscriberCount = Math.max(0, subscriberCount - 1)
    if (subscriberCount === 0) {
      socketManuallyClosed = true
      clearHeartbeat()
      clearReconnectTimer()
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
