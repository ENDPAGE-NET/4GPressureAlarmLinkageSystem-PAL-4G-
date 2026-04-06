import { reactive, readonly } from 'vue'

import {
  getSubscriptionStatusApi,
  subscribeNotificationsApi,
  unsubscribeNotificationsApi,
} from '@/api/notifications'
import { useAuthStore } from '@/stores/auth'
import { APP_CONFIG } from '@/utils/config'
import { getSubscriptionState, setSubscriptionState } from '@/utils/storage'

const state = reactive({
  ...getSubscriptionState(),
})

function persist(nextState) {
  state.enabled = Boolean(nextState.enabled)
  state.templateIds = Array.isArray(nextState.templateIds) ? nextState.templateIds : []
  state.availableTemplateIds = Array.isArray(nextState.availableTemplateIds)
    ? nextState.availableTemplateIds
    : []
  state.subscribedAt = nextState.subscribedAt || ''
  state.unsubscribedAt = nextState.unsubscribedAt || ''
  state.updatedAt = nextState.updatedAt || ''
  state.source = nextState.source || 'server'
  setSubscriptionState({
    enabled: state.enabled,
    templateIds: state.templateIds,
    availableTemplateIds: state.availableTemplateIds,
    subscribedAt: state.subscribedAt,
    unsubscribedAt: state.unsubscribedAt,
    updatedAt: state.updatedAt,
    source: state.source,
  })
}

function applyServerStatus(status) {
  persist({
    enabled: Boolean(status?.enabled),
    templateIds: Array.isArray(status?.template_ids) ? status.template_ids : [],
    availableTemplateIds: Array.isArray(status?.available_template_ids)
      ? status.available_template_ids
      : [],
    subscribedAt: status?.subscribed_at || '',
    unsubscribedAt: status?.unsubscribed_at || '',
    updatedAt: status?.updated_at || status?.subscribed_at || status?.unsubscribed_at || '',
    source: status?.source || 'server',
  })
  return readonly(state)
}

export function useSubscriptionStore() {
  const authStore = useAuthStore()

  async function syncStatus() {
    await authStore.initialize()
    if (!authStore.state.token) {
      persist({
        enabled: false,
        templateIds: [],
        availableTemplateIds: [],
        subscribedAt: '',
        unsubscribedAt: '',
        updatedAt: '',
        source: 'server',
      })
      return readonly(state)
    }

    const status = await getSubscriptionStatusApi()
    return applyServerStatus(status)
  }

  async function requestAlarmSubscription() {
    await authStore.initialize()
    if (!authStore.state.token) {
      throw new Error('请先登录后再申请订阅')
    }

    const availableTemplateIds = state.availableTemplateIds?.length
      ? state.availableTemplateIds
      : APP_CONFIG.SUBSCRIPTION_TEMPLATE_IDS

    if (!Array.isArray(availableTemplateIds) || !availableTemplateIds.length) {
      throw new Error('订阅消息模板尚未配置，请联系管理员补充模板编号')
    }

    if (typeof uni.requestSubscribeMessage !== 'function') {
      throw new Error('当前环境不支持订阅消息授权，请在微信小程序中使用')
    }

    const result = await new Promise((resolve, reject) => {
      uni.requestSubscribeMessage({
        tmplIds: availableTemplateIds,
        success: resolve,
        fail: reject,
      })
    })

    const acceptedTemplateIds = availableTemplateIds.filter((templateId) => {
      return result?.[templateId] === 'accept'
    })

    if (!acceptedTemplateIds.length) {
      const status = await unsubscribeNotificationsApi()
      applyServerStatus(status)
      return false
    }

    const status = await subscribeNotificationsApi({
      template_ids: acceptedTemplateIds,
      source: 'wechat-miniprogram',
    })
    applyServerStatus(status)
    return true
  }

  async function disableAlarmSubscription() {
    await authStore.initialize()
    if (!authStore.state.token) {
      throw new Error('请先登录后再操作')
    }

    const status = await unsubscribeNotificationsApi()
    applyServerStatus(status)
    return readonly(state)
  }

  function markPendingBackend() {
    persist({
      enabled: state.enabled,
      templateIds: state.templateIds,
      availableTemplateIds: state.availableTemplateIds,
      subscribedAt: state.subscribedAt,
      unsubscribedAt: state.unsubscribedAt,
      updatedAt: state.updatedAt,
      source: state.source || 'server',
    })
  }

  return {
    state: readonly(state),
    syncStatus,
    requestAlarmSubscription,
    disableAlarmSubscription,
    markPendingBackend,
  }
}
