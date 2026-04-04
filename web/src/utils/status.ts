export interface StatusMeta {
  type: string
  label?: string
  labelKey?: string
}

export const deviceStatusMeta: Record<string, StatusMeta> = {
  all_online: { type: 'success', labelKey: 'status.device.all_online' },
  part_online: { type: 'warning', labelKey: 'status.device.part_online' },
  all_offline: { type: 'danger', labelKey: 'status.device.all_offline' },
  no_modules: { type: 'info', labelKey: 'status.device.no_modules' },
  active: { type: 'success', labelKey: 'status.device.active' },
  inactive: { type: 'info', labelKey: 'status.device.inactive' },
  other: { type: 'info', labelKey: 'status.device.other' },
}

export const alarmStatusMeta: Record<string, StatusMeta> = {
  triggered: { type: 'danger', labelKey: 'status.alarm.triggered' },
  recovered: { type: 'success', labelKey: 'status.alarm.recovered' },
}

export const linkageStatusMeta: Record<string, StatusMeta> = {
  pending: { type: 'warning', labelKey: 'status.linkage.pending' },
  partial: { type: 'warning', labelKey: 'status.linkage.partial' },
  success: { type: 'success', labelKey: 'status.linkage.success' },
  skipped: { type: 'info', labelKey: 'status.linkage.skipped' },
  failed: { type: 'danger', labelKey: 'status.linkage.failed' },
}

export const commandStatusMeta: Record<string, StatusMeta> = {
  queued: { type: 'warning', labelKey: 'status.command.queued' },
  pending: { type: 'warning', labelKey: 'status.command.pending' },
  dispatched: { type: 'primary', labelKey: 'status.command.dispatched' },
  success: { type: 'success', labelKey: 'status.command.success' },
  failed: { type: 'danger', labelKey: 'status.command.failed' },
}

export function resolveStatusMeta(
  table: Record<string, StatusMeta>,
  value: string | null | undefined,
) {
  if (!value) {
    return { type: 'info', label: '--' }
  }
  return table[value] ?? { type: 'info', label: value }
}
