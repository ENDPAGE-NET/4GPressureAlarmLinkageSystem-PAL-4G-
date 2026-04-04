import dayjs from 'dayjs'

export function formatDateTime(value?: string | null, fallback = '--') {
  if (!value) {
    return fallback
  }
  return dayjs(value).format('YYYY-MM-DD HH:mm:ss')
}

export function formatPercent(value?: number | null) {
  if (value == null) {
    return '--'
  }
  return `${(value * 100).toFixed(1)}%`
}

export function formatVoltage(value?: number | null) {
  if (value == null) {
    return '--'
  }
  return `${value.toFixed(2)} V`
}

export function formatBattery(value?: number | null) {
  if (value == null) {
    return '--'
  }
  return `${value}%`
}
