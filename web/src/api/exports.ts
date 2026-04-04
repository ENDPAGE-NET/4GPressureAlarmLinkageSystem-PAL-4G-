import { http } from './http'

function triggerDownload(blob: Blob, filename: string) {
  const url = window.URL.createObjectURL(blob)
  const anchor = document.createElement('a')
  anchor.href = url
  anchor.download = filename
  document.body.appendChild(anchor)
  anchor.click()
  anchor.remove()
  window.URL.revokeObjectURL(url)
}

export async function exportAlarmsApi() {
  const response = await http.get('/dashboard/alarms/export', {
    responseType: 'blob',
  })
  triggerDownload(response.data, 'dashboard-alarms.csv')
}

export async function exportCommandsApi() {
  const response = await http.get('/dashboard/commands/export', {
    responseType: 'blob',
  })
  triggerDownload(response.data, 'dashboard-commands.csv')
}
