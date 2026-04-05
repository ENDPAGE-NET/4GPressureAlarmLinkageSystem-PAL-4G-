const alarmTypeLabelKeys: Record<string, string> = {
  low_battery: 'alarms.types.low_battery',
  low_voltage: 'alarms.types.low_voltage',
  high_voltage: 'alarms.types.high_voltage',
  disconnect: 'alarms.types.disconnect',
  pressure_abnormal: 'alarms.types.pressure_abnormal',
}

const relayTargetLabelKeys: Record<string, string> = {
  open: 'status.relay.open',
  closed: 'status.relay.closed',
}

const deviceBusinessStatusLabelKeys: Record<string, string> = {
  active: 'status.device.active',
  inactive: 'status.device.inactive',
}

function resolveTranslatedValue(
  value: string | null | undefined,
  labelKeys: Record<string, string>,
  t: (path: string) => string,
) {
  if (!value) {
    return '--'
  }

  const labelKey = labelKeys[value]
  if (!labelKey) {
    return value
  }

  const translated = t(labelKey)
  return translated === labelKey ? value : translated
}

export function resolveAlarmTypeLabel(value: string | null | undefined, t: (path: string) => string) {
  return resolveTranslatedValue(value, alarmTypeLabelKeys, t)
}

export function resolveRelayTargetLabel(value: string | null | undefined, t: (path: string) => string) {
  return resolveTranslatedValue(value, relayTargetLabelKeys, t)
}

export function resolveDeviceBusinessStatusLabel(
  value: string | null | undefined,
  t: (path: string) => string,
) {
  return resolveTranslatedValue(value, deviceBusinessStatusLabelKeys, t)
}
