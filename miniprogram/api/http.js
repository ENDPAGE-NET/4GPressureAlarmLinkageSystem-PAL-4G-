import { useAuthStore } from '@/stores/auth'
import { getApiBase } from '@/utils/config'
import { normalizeErrorMessage } from '@/utils/errors'

function buildUrl(path) {
  if (/^https?:\/\//.test(path)) {
    return path
  }
  return `${getApiBase()}${path}`
}

function redirectToLogin() {
  const pages = getCurrentPages()
  const currentRoute = pages[pages.length - 1]?.route
  if (currentRoute !== 'pages/login/index') {
    uni.reLaunch({
      url: '/pages/login/index',
    })
  }
}

function sanitizeData(data) {
  if (!data || typeof data !== 'object' || Array.isArray(data)) {
    return data
  }

  return Object.fromEntries(
    Object.entries(data).filter(([, value]) => {
      return value !== undefined && value !== null && value !== ''
    }),
  )
}

export function request(options) {
  const authStore = useAuthStore()
  const method = options.method || 'GET'
  const requestData = method.toUpperCase() === 'GET' ? sanitizeData(options.data) : options.data

  return new Promise((resolve, reject) => {
    uni.request({
      url: buildUrl(options.url),
      method,
      timeout: options.timeout || 15000,
      data: requestData,
      header: {
        ...(options.header || {}),
        ...(authStore.state.token
          ? {
              Authorization: `Bearer ${authStore.state.token}`,
            }
          : {}),
      },
      success: (response) => {
        const { statusCode, data } = response

        if (statusCode >= 200 && statusCode < 300) {
          resolve(data)
          return
        }

        if (statusCode === 401) {
          authStore.logout(true)
          redirectToLogin()
        }

        const message = normalizeErrorMessage(
          data?.detail || data?.message || '',
          statusCode,
          `请求失败（${statusCode}）`,
        )
        const error = new Error(message)
        error.statusCode = statusCode
        error.detail = data?.detail || data?.message || ''
        reject(error)
      },
      fail: (error) => {
        reject(
          new Error(
            normalizeErrorMessage(error?.errMsg || '', 0, '网络请求失败，请检查网络连接'),
          ),
        )
      },
    })
  })
}
