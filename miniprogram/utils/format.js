function pad(value) {
  return String(value).padStart(2, '0')
}

export function formatDateTime(value, fallback = '--') {
  if (!value) {
    return fallback
  }

  const date = new Date(value)
  if (Number.isNaN(date.getTime())) {
    return fallback
  }

  return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())} ${pad(
    date.getHours(),
  )}:${pad(date.getMinutes())}:${pad(date.getSeconds())}`
}

export function formatBattery(value, fallback = '--') {
  return value == null ? fallback : `${value}%`
}

export function formatVoltage(value, fallback = '--') {
  return value == null ? fallback : `${Number(value).toFixed(2)} V`
}

export function formatCount(value, fallback = '0') {
  return value == null ? fallback : String(value)
}

export function formatRole(role) {
  switch (role) {
    case 'super_admin':
      return '超级管理员'
    case 'manager':
      return '设备账号'
    case 'device_user':
      return '终端用户'
    default:
      return role || '--'
  }
}
