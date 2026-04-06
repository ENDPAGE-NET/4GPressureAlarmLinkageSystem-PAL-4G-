import { reactive, readonly } from 'vue'

import { APP_CONFIG } from '@/utils/config'
import { getSubscriptionState, setSubscriptionState } from '@/utils/storage'

const state = reactive({
  ...getSubscriptionState(),
})

function persist(nextState) {
  state.enabled = Boolean(nextState.enabled)
  state.updatedAt = nextState.updatedAt || ''
  state.source = nextState.source || 'local'
  setSubscriptionState({
    enabled: state.enabled,
    updatedAt: state.updatedAt,
    source: state.source,
  })
}

export function useSubscriptionStore() {
  async function requestAlarmSubscription() {
    if (!Array.isArray(APP_CONFIG.SUBSCRIPTION_TEMPLATE_IDS) || !APP_CONFIG.SUBSCRIPTION_TEMPLATE_IDS.length) {
      throw new Error('订阅消息模板尚未配置，当前仅保留前端授权入口')
    }

    if (typeof uni.requestSubscribeMessage !== 'function') {
      throw new Error('当前环境不支持订阅消息授权，请在微信小程序中使用')
    }

    const result = await new Promise((resolve, reject) => {
      uni.requestSubscribeMessage({
        tmplIds: APP_CONFIG.SUBSCRIPTION_TEMPLATE_IDS,
        success: resolve,
        fail: reject,
      })
    })

    const granted = Object.values(result || {}).some((item) => item === 'accept')
    persist({
      enabled: granted,
      updatedAt: new Date().toISOString(),
      source: granted ? 'local' : 'local-denied',
    })
    return granted
  }

  function markPendingBackend() {
    persist({
      enabled: state.enabled,
      updatedAt: state.updatedAt,
      source: state.source || 'local',
    })
  }

  return {
    state: readonly(state),
    requestAlarmSubscription,
    markPendingBackend,
  }
}
