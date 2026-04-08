import {
  clearServiceOrigin as clearStoredServiceOrigin,
  getServiceOrigin as getStoredServiceOrigin,
  setServiceOrigin as setStoredServiceOrigin,
} from '@/utils/storage'

// 生产环境请替换为实际部署地址，如 https://usr-iot.endpage.net
const DEFAULT_SERVICE_ORIGIN = 'https://usr-iot.endpage.net'

function normalizeServiceOrigin(origin) {
  const raw = String(origin || '').trim()
  if (!raw) {
    return ''
  }

  const withProtocol = /^https?:\/\//i.test(raw) ? raw : `https://${raw}`

  try {
    const url = new URL(withProtocol)
    if (!/^https?:$/i.test(url.protocol)) {
      return ''
    }
    return url.origin.replace(/\/$/, '')
  } catch {
    return ''
  }
}

function resolveServiceOrigin() {
  return normalizeServiceOrigin(getStoredServiceOrigin()) || DEFAULT_SERVICE_ORIGIN
}

function buildApiBase(origin) {
  return `${origin}/api/v1`
}

function buildWsUrl(origin) {
  return `${origin.replace(/^http:\/\//i, 'ws://').replace(/^https:\/\//i, 'wss://')}/api/v1/ws/events`
}

export const APP_CONFIG = {
  get SERVICE_ORIGIN() {
    return resolveServiceOrigin()
  },
  get API_BASE() {
    return buildApiBase(resolveServiceOrigin())
  },
  get WS_URL() {
    return buildWsUrl(resolveServiceOrigin())
  },
  POLLING_INTERVAL: 20000,
  HEARTBEAT_INTERVAL: 25000,
  WECHAT_LOGIN_ENABLED: true,
  SUBSCRIPTION_TEMPLATE_IDS: [],
}

export function getServiceOrigin() {
  return resolveServiceOrigin()
}

export function setServiceOrigin(origin) {
  const normalizedOrigin = normalizeServiceOrigin(origin)
  if (!normalizedOrigin) {
    throw new Error('服务地址格式无效，请输入完整的 http:// 或 https:// 地址')
  }
  setStoredServiceOrigin(normalizedOrigin)
  return normalizedOrigin
}

export function clearServiceOrigin() {
  clearStoredServiceOrigin()
  return DEFAULT_SERVICE_ORIGIN
}

export function getApiBase() {
  return buildApiBase(resolveServiceOrigin())
}

export function getWsUrl() {
  return buildWsUrl(resolveServiceOrigin())
}
