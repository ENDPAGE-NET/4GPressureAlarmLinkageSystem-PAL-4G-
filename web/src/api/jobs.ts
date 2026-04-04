import { http } from './http'
import type {
  AlarmRecoveryCheckResult,
  CleanupResult,
  DatabaseBackupFileRead,
  DatabaseBackupResult,
  JobExecutionLogRead,
  OfflineCheckResult,
  RelayRetryResult,
  SchedulerStatus,
} from '@/types/domain'

export async function getSchedulerStatusApi() {
  const { data } = await http.get<SchedulerStatus>('/jobs/scheduler')
  return data
}

export async function getJobHistoryApi(params?: {
  job_name?: string
  trigger_type?: string
  status?: string
  limit?: number
}) {
  const { data } = await http.get<JobExecutionLogRead[]>('/jobs/history', { params })
  return data
}

export async function runOfflineCheckApi() {
  const { data } = await http.post<OfflineCheckResult>('/jobs/offline-check')
  return data
}

export async function runRetryPendingApi() {
  const { data } = await http.post<RelayRetryResult>('/jobs/retry-pending')
  return data
}

export async function runAlarmRecoveryCheckApi() {
  const { data } = await http.post<AlarmRecoveryCheckResult>('/jobs/alarm-recovery-check')
  return data
}

export async function runCleanupFilesApi() {
  const { data } = await http.post<CleanupResult>('/jobs/cleanup-files')
  return data
}

export async function runBackupDatabaseApi() {
  const { data } = await http.post<DatabaseBackupResult>('/jobs/backup-database')
  return data
}

export async function getBackupsApi(limit = 20) {
  const { data } = await http.get<DatabaseBackupFileRead[]>('/jobs/backups', {
    params: { limit },
  })
  return data
}
