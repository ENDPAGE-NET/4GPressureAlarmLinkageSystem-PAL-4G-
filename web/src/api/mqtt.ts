import { http } from './http'
import type { MqttClientStatus } from '@/types/domain'

export async function getMqttStatusApi() {
  const { data } = await http.get<MqttClientStatus>('/mqtt/status')
  return data
}
