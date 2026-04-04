import { http } from './http'
import type {
  DeviceBindPayload,
  DeviceGroupCreatePayload,
  DeviceGroupRead,
  DeviceGroupUpdatePayload,
  DeviceMonitoringItem,
  DeviceRead,
  RelayCommandCreatePayload,
} from '@/types/domain'

export async function getDeviceMonitoringApi() {
  const { data } = await http.get<DeviceMonitoringItem[]>('/devices/monitoring')
  return data
}

export async function bindDeviceApi(payload: DeviceBindPayload) {
  const { data } = await http.post<DeviceRead>('/devices/bind', payload)
  return data
}

export async function getDevicesApi() {
  const { data } = await http.get<DeviceRead[]>('/devices')
  return data
}

export async function getDeviceApi(deviceId: number) {
  const { data } = await http.get<DeviceRead>(`/devices/${deviceId}`)
  return data
}

export async function createRelayCommandApi(payload: RelayCommandCreatePayload) {
  const { data } = await http.post('/relay-commands', payload)
  return data
}

export async function getDeviceGroupsApi() {
  const { data } = await http.get<DeviceGroupRead[]>('/devices/groups')
  return data
}

export async function createDeviceGroupApi(payload: DeviceGroupCreatePayload) {
  const { data } = await http.post<DeviceGroupRead>('/devices/groups', payload)
  return data
}

export async function updateDeviceGroupApi(groupId: number, payload: DeviceGroupUpdatePayload) {
  const { data } = await http.patch<DeviceGroupRead>(`/devices/groups/${groupId}`, payload)
  return data
}

export async function deleteDeviceGroupApi(groupId: number) {
  const { data } = await http.delete(`/devices/groups/${groupId}`)
  return data
}

export async function assignDeviceOwnerApi(deviceId: number, ownerId: number | null) {
  const { data } = await http.post<DeviceRead>(`/devices/${deviceId}/assign-owner`, {
    owner_id: ownerId,
  })
  return data
}

export async function assignDeviceGroupApi(deviceId: number, linkageGroupId: number | null) {
  const { data } = await http.post<DeviceRead>(`/devices/${deviceId}/assign-group`, {
    linkage_group_id: linkageGroupId,
  })
  return data
}

export async function unbindDeviceApi(deviceId: number) {
  const { data } = await http.post<DeviceRead>(`/devices/${deviceId}/unbind`)
  return data
}
