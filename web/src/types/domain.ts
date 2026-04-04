export interface TokenResponse {
  access_token: string
  token_type: string
}

export interface UserProfile {
  id: number
  username: string
  role: 'super_admin' | 'manager' | 'device_user' | string
  is_active: boolean
}

export type LocaleCode = 'zh-CN' | 'en-US'
export type ThemeMode = 'dark' | 'light'
export type RealtimeStatus = 'connected' | 'connecting' | 'fallback' | 'unsupported' | 'error'

export interface ModuleRead {
  id: number
  module_code: string
  relay_state: boolean
  is_online: boolean
  battery_level: number | null
  voltage_value: number | null
  last_seen_at: string | null
}

export interface DeviceRead {
  id: number
  name: string
  serial_number: string
  status: string
  owner_id: number | null
  linkage_group_id: number | null
  created_at: string
  updated_at: string
  modules: ModuleRead[]
}

export interface DeviceBindPayload {
  serial_number: string
  name?: string | null
}

export interface DeviceOverview {
  total_devices: number
  total_modules: number
  online_modules: number
  offline_modules: number
  triggered_alarm_count: number
}

export interface DeviceStatistics {
  total_devices: number
  owned_devices: number
  total_modules: number
  online_modules: number
  offline_modules: number
  online_rate: number
  triggered_alarm_count: number
  low_battery_alarm_count: number
  low_voltage_alarm_count: number
}

export interface DeviceMonitoringItem {
  device_id: number
  device_name: string
  serial_number: string
  owner_id: number | null
  module_count: number
  online_module_count: number
  offline_module_count: number
  latest_alarm_type: string | null
  latest_alarm_time: string | null
  device_status: string
}

export interface DashboardHome {
  overview: DeviceOverview
  statistics: DeviceStatistics
  monitoring: DeviceMonitoringItem[]
  module_panels: DashboardModulePanelItem[]
  recent_alarm_count: number
  pending_command_count: number
}

export interface DashboardModulePanelItem {
  module_id: number
  device_id: number
  device_name: string
  serial_number: string
  module_code: string
  is_online: boolean
  battery_level: number | null
  voltage_value: number | null
  relay_state: boolean
  last_seen_at: string | null
  latest_alarm_type: string | null
  latest_alarm_time: string | null
}

export interface DashboardTrendPoint {
  label: string
  value: number
}

export interface DashboardCharts {
  alarm_type_distribution: DashboardTrendPoint[]
  command_status_distribution: DashboardTrendPoint[]
  device_status_distribution: DashboardTrendPoint[]
}

export interface DashboardAlarmItem {
  id: number
  module_id: number
  device_id: number
  device_name: string
  module_code: string
  alarm_type: string
  alarm_status: string
  source: string
  linkage_status: string
  message: string | null
  triggered_at: string
}

export interface DashboardRelayCommandItem {
  id: number
  module_id: number
  device_id: number
  device_name: string
  module_code: string
  command_source: string
  target_state: string
  execution_status: string
  feedback_status: string | null
  feedback_message: string | null
  created_at: string
  executed_at: string | null
}

export interface PaginationMeta {
  total: number
  limit: number
  offset: number
}

export interface DashboardAlarmPage {
  items: DashboardAlarmItem[]
  pagination: PaginationMeta
}

export interface DashboardDeviceDetail {
  device_id: number
  device_name: string
  serial_number: string
  status: string
  owner_id: number | null
  linkage_group_id: number | null
  module_count: number
  online_module_count: number
  offline_module_count: number
  latest_alarm_type: string | null
  latest_alarm_time: string | null
  device_status: string
  recent_alarms: DashboardAlarmItem[]
  recent_commands: DashboardRelayCommandItem[]
}

export interface ChangePasswordPayload {
  current_password: string
  new_password: string
}

export interface RelayCommandCreatePayload {
  module_id: number
  target_state: 'open' | 'closed'
  command_source?: string
}

export interface UserRead {
  id: number
  username: string
  role: string
  is_active: boolean
  created_at: string
  updated_at: string
}

export interface UserCreatePayload {
  username: string
  password: string
  role: 'super_admin' | 'manager'
}

export interface UserUpdatePayload {
  password?: string
  role?: 'super_admin' | 'manager'
  is_active?: boolean
}

export interface UserResetPasswordPayload {
  new_password: string
}

export interface DeviceGroupRead {
  id: number
  name: string
  description: string | null
  owner_id: number | null
  created_at: string
  updated_at: string
  device_count: number
  device_ids: number[]
}

export interface DeviceGroupCreatePayload {
  name: string
  description?: string | null
  owner_id?: number | null
}

export interface DeviceGroupUpdatePayload {
  name?: string
  description?: string | null
  owner_id?: number | null
}

export interface RuntimeLogRead {
  id: number
  level: string
  event: string
  message: string
  context: string | null
  created_at: string
}

export interface OperationLogRead {
  id: number
  actor_user_id: number | null
  action: string
  target_type: string
  target_id: number | null
  status: string
  detail: string | null
  created_at: string
}

export interface CommunicationLogRead {
  id: number
  channel: string
  direction: string
  device_serial: string | null
  module_code: string | null
  status: string
  payload: string | null
  message: string | null
  created_at: string
}

export interface RuntimeLogPage {
  total: number
  items: RuntimeLogRead[]
}

export interface OperationLogPage {
  total: number
  items: OperationLogRead[]
}

export interface CommunicationLogPage {
  total: number
  items: CommunicationLogRead[]
}

export interface LogsOverview {
  runtime_total: number
  runtime_error_count: number
  operation_total: number
  operation_failed_count: number
  communication_total: number
  communication_failed_count: number
}

export interface SchedulerJobRead {
  id: string
  next_run_time: string | null
  trigger: string
}

export interface SchedulerStatus {
  running: boolean
  jobs: SchedulerJobRead[]
}

export interface JobExecutionLogRead {
  id: number
  job_name: string
  trigger_type: string
  status: string
  message: string | null
  context: string | null
  started_at: string
  finished_at: string | null
  created_at: string
}

export interface OfflineCheckResult {
  updated_count: number
}

export interface RelayRetryResult {
  total_scanned: number
  dispatched_count: number
  still_queued_count: number
}

export interface AlarmRecoveryCheckResult {
  recovered_count: number
  skipped_count: number
}

export interface CleanupResult {
  removed_log_directories: number
  removed_backup_directories: number
}

export interface DatabaseBackupResult {
  backup_file: string
  file_size: number
}

export interface DatabaseBackupFileRead {
  backup_file: string
  file_size: number
  created_at: string
}

export interface MqttClientStatus {
  enabled: boolean
  connected: boolean
  broker_host: string
  broker_port: number
  status_topic: string
  subscribed_topics: string[]
  received_message_count: number
  published_message_count: number
  last_inbound_topic: string | null
  last_inbound_at: string | null
  last_outbound_topic: string | null
  last_outbound_at: string | null
}
