import { http } from './http'
import type {
  DashboardAlarmItem,
  DashboardAlarmPage,
  DashboardCharts,
  DashboardDeviceDetail,
  DashboardHome,
  DashboardRelayCommandItem,
} from '@/types/domain'

export async function getDashboardHomeApi() {
  const { data } = await http.get<DashboardHome>('/dashboard/home')
  return data
}

export async function getDashboardChartsApi() {
  const { data } = await http.get<DashboardCharts>('/dashboard/charts')
  return data
}

export async function getRecentAlarmsApi(limit = 10) {
  const { data } = await http.get<DashboardAlarmItem[]>('/dashboard/recent-alarms', {
    params: { limit },
  })
  return data
}

export async function getRecentCommandsApi(limit = 10) {
  const { data } = await http.get<DashboardRelayCommandItem[]>('/dashboard/recent-commands', {
    params: { limit },
  })
  return data
}

export async function getDashboardAlarmPageApi(
  limit: number,
  offset: number,
  filters?: {
    keyword?: string
    alarm_type?: string
    alarm_status?: string
    linkage_status?: string
    triggered_from?: string
    triggered_to?: string
  },
) {
  const { data } = await http.get<DashboardAlarmPage>('/dashboard/alarms/page', {
    params: {
      limit,
      offset,
      ...filters,
    },
  })
  return data
}

export async function getDashboardDeviceDetailApi(deviceId: number) {
  const { data } = await http.get<DashboardDeviceDetail>(`/dashboard/devices/${deviceId}`)
  return data
}
