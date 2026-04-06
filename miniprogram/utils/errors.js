const MESSAGE_MAP = {
  'Incorrect username or password': '账号或密码错误',
  'User is inactive': '当前账号已停用，请联系管理员',
  'WeChat account is not bound to any user': '当前微信尚未绑定设备账号',
  'This WeChat account is already bound to another user': '该微信已绑定其他账号，请更换后重试',
  'No WeChat subscribe template id configured': '报警订阅模板未配置，请联系管理员',
  'Not authenticated': '登录已失效，请重新登录',
  'Could not validate credentials': '登录凭证无效，请重新登录',
  'Network request failed': '网络请求失败，请检查网络连接',
  'Request timeout': '请求超时，请稍后重试',
  'socket error': '实时连接异常，已切换为轮询模式',
  'socket closed': '实时连接已断开，已切换为轮询模式',
  'missing token': '当前未检测到登录状态，请重新登录',
  'missing ws url': '实时服务地址未配置，已切换为轮询模式',
}

function mapStatusCodeMessage(statusCode, fallback) {
  switch (statusCode) {
    case 400:
      return fallback || '请求参数有误，请检查后重试'
    case 401:
      return '登录已失效，请重新登录'
    case 403:
      return '当前账号暂无权限执行此操作'
    case 404:
      return '未找到对应服务或数据'
    case 409:
      return fallback || '数据状态已变更，请刷新后重试'
    case 422:
      return fallback || '提交内容不符合要求，请检查后重试'
    case 500:
      return '服务器暂时异常，请稍后重试'
    default:
      return fallback || '操作失败，请稍后重试'
  }
}

export function normalizeErrorMessage(message, statusCode, fallback = '') {
  const raw = typeof message === 'string' ? message.trim() : ''
  if (!raw) {
    return mapStatusCodeMessage(statusCode, fallback)
  }

  if (MESSAGE_MAP[raw]) {
    return MESSAGE_MAP[raw]
  }

  const lower = raw.toLowerCase()

  if (lower.includes('timeout')) {
    return '请求超时，请稍后重试'
  }

  if (
    lower.includes('connection refused') ||
    lower.includes('fail connect') ||
    lower.includes('unable to resolve host')
  ) {
    return '无法连接到服务器，请确认后端服务已启动'
  }

  if (
    lower.includes('network') ||
    lower.includes('err_network') ||
    lower.includes('request:fail')
  ) {
    return '网络请求失败，请检查网络连接'
  }

  if (lower.includes('not found')) {
    return '未找到对应服务或数据'
  }

  if (lower.includes('unauthorized') || lower.includes('unauthenticated')) {
    return '登录已失效，请重新登录'
  }

  if (lower.includes('forbidden') || lower.includes('permission denied')) {
    return '当前账号暂无权限执行此操作'
  }

  if (lower.includes('inactive')) {
    return '当前账号已停用，请联系管理员'
  }

  if (lower.includes('invalid') && lower.includes('password')) {
    return '账号或密码错误'
  }

  if (lower.includes('subscribe')) {
    return fallback || '订阅消息处理失败，请稍后重试'
  }

  if (lower.includes('wechat')) {
    return fallback || '微信授权处理失败，请稍后重试'
  }

  if (statusCode >= 400) {
    return mapStatusCodeMessage(statusCode, raw || fallback)
  }

  return raw || fallback || '操作失败，请稍后重试'
}

export function extractErrorMessage(error, fallback = '操作失败，请稍后重试') {
  if (!error) {
    return fallback
  }

  if (typeof error === 'string') {
    return normalizeErrorMessage(error, 0, fallback)
  }

  const statusCode = Number(error.statusCode || error.status || 0)

  if (typeof error.detail === 'string' && error.detail.trim()) {
    return normalizeErrorMessage(error.detail, statusCode, fallback)
  }

  if (typeof error.message === 'string' && error.message.trim()) {
    return normalizeErrorMessage(error.message, statusCode, fallback)
  }

  return mapStatusCodeMessage(statusCode, fallback)
}

export function showRequestError(error, fallback) {
  uni.showToast({
    title: extractErrorMessage(error, fallback),
    icon: 'none',
    duration: 2200,
  })
}
