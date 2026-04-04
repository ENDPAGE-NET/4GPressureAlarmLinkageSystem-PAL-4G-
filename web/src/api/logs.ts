import { http } from './http'
import type {
  CommunicationLogPage,
  LogsOverview,
  OperationLogPage,
  RuntimeLogPage,
} from '@/types/domain'

export async function getLogsOverviewApi() {
  const { data } = await http.get<LogsOverview>('/logs/overview')
  return data
}

export async function getRuntimeLogsPageApi(params: {
  level?: string
  event?: string
  created_from?: string
  created_to?: string
  limit: number
  offset: number
}) {
  const { data } = await http.get<RuntimeLogPage>('/logs/runtime/page', { params })
  return data
}

export async function getOperationLogsPageApi(params: {
  action?: string
  target_type?: string
  status?: string
  limit: number
  offset: number
}) {
  const { data } = await http.get<OperationLogPage>('/logs/operations/page', { params })
  return data
}

export async function getCommunicationLogsPageApi(params: {
  channel?: string
  direction?: string
  device_serial?: string
  status?: string
  limit: number
  offset: number
}) {
  const { data } = await http.get<CommunicationLogPage>('/logs/communication/page', { params })
  return data
}
