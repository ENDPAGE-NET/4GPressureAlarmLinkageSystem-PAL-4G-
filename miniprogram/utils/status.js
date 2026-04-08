export function getOnlineStatusLabel(value) {
  return value ? '在线' : '离线'
}

export function getOnlineStatusClass(value) {
  return value ? 'status-online' : 'status-offline'
}

export function getRelayStateLabel(relayState) {
  return relayState ? '闭合' : '断开'
}

export function getRelayTargetLabel(targetState) {
  return targetState === 'closed' ? '闭合' : '断开'
}

export function getCommandStatusLabel(status) {
  switch (status) {
    case 'queued':
      return '排队中'
    case 'dispatched':
      return '已下发'
    case 'success':
      return '已执行'
    case 'failed':
      return '失败'
    default:
      return status || '--'
  }
}

export function getCommandStatusClass(status) {
  switch (status) {
    case 'success':
      return 'status-online'
    case 'failed':
      return 'status-alarm'
    case 'queued':
    case 'dispatched':
      return 'status-pending'
    default:
      return 'status-info'
  }
}

export function getAlarmTypeLabel(type) {
  switch (type) {
    case 'low_battery':
      return '低电量报警'
    case 'low_voltage':
      return '低压报警'
    case 'high_voltage':
      return '高压报警'
    case 'disconnect':
      return '离线报警'
    case 'pressure_abnormal':
      return '压力异常'
    default:
      return type || '--'
  }
}

export function getDeviceStatusLabel(status) {
  switch (status) {
    case 'active':
      return '正常'
    case 'inactive':
      return '停用'
    default:
      return status || '--'
  }
}
