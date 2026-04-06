import { reactive, readonly } from 'vue'

import { useAuthStore } from '@/stores/auth'
import { APP_CONFIG, getWsUrl } from '@/utils/config'

const state = reactive({
  status: 'fallback',
  lastEventAt: '',
  detail: '',
})

const NORMAL_CLOSE_CODE = 1000
const NORMAL_CLOSE_REASON = 'normal closure'

let socketTask = null
let reconnectTimer = null
let heartbeatTimer = null
let subscribers = 0
let manuallyClosed = false
const listeners = new Set()

function setState(status, detail = '') {
  state.status = status
  state.detail = detail
}

function clearReconnect() {
  if (reconnectTimer) {
    clearTimeout(reconnectTimer)
    reconnectTimer = null
  }
}

function clearHeartbeat() {
  if (heartbeatTimer) {
    clearInterval(heartbeatTimer)
    heartbeatTimer = null
  }
}

function notifyListeners(message) {
  listeners.forEach((listener) => listener(message))
}

function startHeartbeat() {
  clearHeartbeat()
  heartbeatTimer = setInterval(() => {
    if (socketTask) {
      try {
        socketTask.send({
          data: 'ping',
        })
      } catch (error) {
        console.warn('realtime heartbeat failed', error)
      }
    }
  }, APP_CONFIG.HEARTBEAT_INTERVAL)
}

function scheduleReconnect() {
  if (manuallyClosed || reconnectTimer || subscribers === 0) {
    return
  }

  reconnectTimer = setTimeout(() => {
    reconnectTimer = null
    connect()
  }, 3000)
}

function teardown() {
  clearReconnect()
  clearHeartbeat()
  if (socketTask) {
    try {
      socketTask.close({
        code: NORMAL_CLOSE_CODE,
        reason: NORMAL_CLOSE_REASON,
      })
    } catch (error) {
      console.warn('realtime socket close failed', error)
    }
  }
  socketTask = null
}

function connect() {
  const authStore = useAuthStore()
  if (!authStore.state.token) {
    setState('fallback', '未检测到登录状态')
    return
  }

  const baseUrl = getWsUrl()
  if (!baseUrl) {
    setState('fallback', '未配置实时服务地址')
    return
  }

  manuallyClosed = false
  clearReconnect()
  setState('connecting')

  socketTask = uni.connectSocket({
    url: `${baseUrl}?token=${encodeURIComponent(authStore.state.token)}`,
    complete: () => {},
  })

  socketTask.onOpen(() => {
    setState('connected')
    startHeartbeat()
  })

  socketTask.onMessage((event) => {
    try {
      const payload = JSON.parse(event.data)
      state.lastEventAt = new Date().toISOString()
      notifyListeners(payload)
    } catch (error) {
      console.warn('realtime parse failed', error)
    }
  })

  socketTask.onClose(() => {
    clearHeartbeat()
    socketTask = null
    if (!manuallyClosed) {
      setState('fallback', '实时连接已断开')
      scheduleReconnect()
    }
  })

  socketTask.onError(() => {
    setState('error', '实时连接异常')
    clearHeartbeat()
    socketTask = null
    scheduleReconnect()
  })
}

export function useRealtime() {
  function subscribe(listener) {
    listeners.add(listener)
    subscribers += 1

    if (subscribers === 1) {
      connect()
    }

    return () => {
      listeners.delete(listener)
      subscribers = Math.max(0, subscribers - 1)
      if (subscribers === 0) {
        manuallyClosed = true
        teardown()
      }
    }
  }

  function reconnect() {
    teardown()
    connect()
  }

  return {
    state: readonly(state),
    subscribe,
    reconnect,
  }
}
