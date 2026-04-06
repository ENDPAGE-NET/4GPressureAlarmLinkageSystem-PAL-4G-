export const APP_CONFIG = {
  API_BASE: 'http://127.0.0.1:8000/api/v1',
  WS_URL: 'ws://127.0.0.1:8000/api/v1/ws/events',
  POLLING_INTERVAL: 20000,
  HEARTBEAT_INTERVAL: 25000,
  WECHAT_LOGIN_ENABLED: true,
  SUBSCRIPTION_TEMPLATE_IDS: [],
}

export function getApiBase() {
  return APP_CONFIG.API_BASE
}

export function getWsUrl() {
  return APP_CONFIG.WS_URL
}
