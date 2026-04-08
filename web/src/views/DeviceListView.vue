<template>
  <div class="page-shell">
    <div class="page-title">
      <div>
        <h1>{{ t('devices.title') }}</h1>
        <p>{{ t('devices.description') }}</p>
      </div>
      <div class="toolbar__actions">
        <el-button v-if="canManageDevices" type="primary" :icon="Plus" @click="openCreateDialog">
          {{ t('devices.createDevice') }}
        </el-button>
        <el-button v-if="!isAdmin" :icon="Link" @click="bindDialogVisible = true">
          {{ t('devices.bindDevice') }}
        </el-button>
        <el-button type="primary" plain :icon="RefreshRight" @click="fetchDevices">{{ t('common.refresh') }}</el-button>
      </div>
    </div>

    <PanelCard>
      <div class="toolbar">
        <div class="toolbar__filters">
          <el-input v-model="keyword" clearable :placeholder="t('devices.searchPlaceholder')" style="width: 260px" />
        </div>
      </div>
    </PanelCard>

    <PanelCard :title="t('devices.title')" :description="t('devices.description')">
      <DataState
        :loading="loading"
        :error="error"
        :empty="!filteredDevices.length"
        :empty-text="t('common.noData')"
        @retry="fetchDevices"
      >
        <div class="data-table">
          <el-table :data="filteredDevices">
            <el-table-column prop="device_name" :label="t('devices.table.device')" min-width="180" />
            <el-table-column prop="serial_number" :label="t('devices.table.serial')" min-width="160">
              <template #default="{ row }">
                <span class="mono">{{ row.serial_number }}</span>
              </template>
            </el-table-column>
            <el-table-column :label="t('common.status')" min-width="110">
              <template #default="{ row }">
                <StatusPill :value="row.device_status" :mapping="deviceStatusMeta" />
              </template>
            </el-table-column>
            <el-table-column :label="t('devices.table.online')" min-width="120">
              <template #default="{ row }">{{ row.online_module_count > 0 ? '在线' : '离线' }}</template>
            </el-table-column>
            <el-table-column v-if="isAdmin" :label="t('devices.owner')" min-width="140">
              <template #default="{ row }">{{ resolveOwnerName(row.owner_id) }}</template>
            </el-table-column>
            <el-table-column :label="t('devices.table.latestAlarm')" min-width="140">
              <template #default="{ row }">{{ resolveAlarmTypeLabel(row.latest_alarm_type, t) }}</template>
            </el-table-column>
            <el-table-column :label="t('devices.table.latestAlarmTime')" min-width="180">
              <template #default="{ row }">{{ formatDateTime(row.latest_alarm_time) }}</template>
            </el-table-column>
            <el-table-column :label="t('common.actions')" min-width="320">
              <template #default="{ row }">
                <el-button type="primary" link :icon="View" @click="router.push(`/devices/${row.device_id}`)">
                  {{ t('common.details') }}
                </el-button>
                <el-button v-if="canManageDevices" link :icon="Connection" @click="showMqttConfig(row.device_id)">
                  配置
                </el-button>
                <el-button v-if="canManageDevices" link :icon="EditPen" @click="openEditDialog(row)">
                  {{ t('common.edit') }}
                </el-button>
                <el-button v-if="canManageDevices" link type="danger" :icon="Delete" @click="handleDeleteDevice(row)">
                  {{ t('common.delete') }}
                </el-button>
                <el-button v-if="isAdmin" link type="warning" :icon="User" @click="openOwnerDialog(row)">
                  {{ t('devices.assignOwner') }}
                </el-button>
                <el-button v-if="!isAdmin" link type="danger" :icon="CloseBold" @click="handleUnbind(row.device_id)">
                  {{ t('devices.unbind') }}
                </el-button>
              </template>
            </el-table-column>
          </el-table>
        </div>
      </DataState>
    </PanelCard>

    <el-dialog v-model="deviceDialogVisible" :title="deviceDialogTitle" width="460px">
      <el-form ref="deviceFormRef" :model="deviceForm" :rules="deviceRules" label-position="top">
        <el-form-item :label="t('devices.nameLabel')" prop="name">
          <el-input v-model="deviceForm.name" :placeholder="t('devices.namePlaceholder')" />
        </el-form-item>
        <el-form-item :label="t('devices.serialLabel')" prop="serial_number">
          <el-input
            v-model="deviceForm.serial_number"
            :placeholder="t('devices.serialPlaceholder')"
            :disabled="deviceDialogMode === 'edit'"
          />
        </el-form-item>
        <el-form-item v-if="deviceDialogMode === 'edit'" :label="t('devices.statusLabel')" prop="status">
          <el-select v-model="deviceForm.status" style="width: 100%">
            <el-option :label="t('status.device.active')" value="active" />
            <el-option :label="t('status.device.inactive')" value="inactive" />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="deviceDialogVisible = false">{{ t('common.cancel') }}</el-button>
        <el-button type="primary" :loading="submitting" @click="submitDevice">
          {{ t('common.save') }}
        </el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="bindDialogVisible" :title="t('devices.bindDialogTitle')" width="460px">
      <el-form label-position="top">
        <el-alert
          :title="t('devices.bindDescription')"
          type="info"
          :closable="false"
          show-icon
          style="margin-bottom: 16px"
        />
        <el-form-item :label="t('devices.bindBySerial')" required>
          <el-input v-model="bindForm.serial_number" :placeholder="t('devices.bindSerialPlaceholder')" />
        </el-form-item>
        <el-form-item :label="`${t('devices.bindName')} (${t('common.optional')})`">
          <el-input v-model="bindForm.name" :placeholder="t('devices.bindNamePlaceholder')" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="bindDialogVisible = false">{{ t('common.cancel') }}</el-button>
        <el-button type="primary" :loading="submitting" @click="submitBind">{{ t('common.confirm') }}</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="mqttConfigVisible" title="MQTT 接入配置" width="560px">
      <el-alert
        title="请将以下配置信息提供给客户，用于 4G CAT1 setup 软件中配置设备的 MQTT 连接参数。"
        type="success"
        :closable="false"
        show-icon
        style="margin-bottom: 16px"
      />
      <div v-if="lastCreatedMqttConfig" class="mqtt-config-card">
        <el-descriptions :column="1" border>
          <el-descriptions-item label="MQTT 服务器">{{ lastCreatedMqttConfig.broker_host }}</el-descriptions-item>
          <el-descriptions-item label="端口">{{ lastCreatedMqttConfig.broker_port }}</el-descriptions-item>
          <el-descriptions-item label="TLS 加密">{{ lastCreatedMqttConfig.tls_enabled ? '是' : '否' }}</el-descriptions-item>
          <el-descriptions-item label="用户名">
            <span class="mono">{{ lastCreatedMqttConfig.mqtt_username }}</span>
          </el-descriptions-item>
          <el-descriptions-item label="密码">
            <span class="mono">{{ lastCreatedMqttConfig.mqtt_password }}</span>
          </el-descriptions-item>
          <el-descriptions-item label="客户端 ID">
            <span class="mono">{{ lastCreatedMqttConfig.mqtt_client_id }}</span>
          </el-descriptions-item>
          <el-descriptions-item label="发布 Topic（设备上行）">
            <span class="mono">{{ lastCreatedMqttConfig.mqtt_pub_topic }}</span>
          </el-descriptions-item>
          <el-descriptions-item label="订阅 Topic（设备下行）">
            <span class="mono">{{ lastCreatedMqttConfig.mqtt_sub_topic }}</span>
          </el-descriptions-item>
        </el-descriptions>
      </div>
      <template #footer>
        <el-button @click="copyMqttConfig">复制配置</el-button>
        <el-button type="primary" @click="mqttConfigVisible = false">确定</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="ownerDialogVisible" :title="t('devices.assignOwner')" width="420px">
      <el-form label-position="top">
        <el-form-item :label="t('devices.owner')">
          <el-select v-model="ownerForm.owner_id" clearable style="width: 100%">
            <el-option v-for="user in users" :key="user.id" :label="user.username" :value="user.id" />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="ownerDialogVisible = false">{{ t('common.cancel') }}</el-button>
        <el-button type="primary" :loading="submitting" @click="submitOwner">{{ t('common.save') }}</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { CloseBold, Connection, Delete, EditPen, Link, Plus, RefreshRight, User, View } from '@element-plus/icons-vue'
import type { FormInstance, FormRules } from 'element-plus'
import { ElMessage, ElMessageBox } from 'element-plus'
import { computed, onBeforeUnmount, onMounted, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'

import {
  assignDeviceOwnerApi,
  bindDeviceApi,
  createDeviceApi,
  deleteDeviceApi,
  getDeviceMqttConfigApi,
  getDeviceMonitoringApi,
  getDevicesApi,
  unbindDeviceApi,
  updateDeviceApi,
} from '@/api/devices'
import { getUsersApi } from '@/api/users'
import DataState from '@/components/DataState.vue'
import PanelCard from '@/components/PanelCard.vue'
import StatusPill from '@/components/StatusPill.vue'
import { useI18n } from '@/composables/useI18n'
import { useRealtime } from '@/composables/useRealtime'
import { useAuthStore } from '@/stores/auth'
import type { DeviceMonitoringItem, DeviceMqttConfig, DeviceRead, RealtimeEventMessage, UserRead } from '@/types/domain'
import { formatDateTime } from '@/utils/format'
import { resolveAlarmTypeLabel } from '@/utils/labels'
import { deviceStatusMeta } from '@/utils/status'

type DeviceRow = DeviceMonitoringItem & {
  owner_id: number | null
  status: string
}

const { t } = useI18n()
const authStore = useAuthStore()
const router = useRouter()
const loading = ref(true)
const error = ref('')
const keyword = ref('')
const devices = ref<DeviceRow[]>([])
const users = ref<UserRead[]>([])
const currentDeviceId = ref<number | null>(null)
const ownerDialogVisible = ref(false)
const bindDialogVisible = ref(false)
const deviceDialogVisible = ref(false)
const mqttConfigVisible = ref(false)
const lastCreatedMqttConfig = ref<DeviceMqttConfig | null>(null)
const deviceDialogMode = ref<'create' | 'edit'>('create')
const deviceFormRef = ref<FormInstance>()
const submitting = ref(false)

const bindForm = reactive({
  serial_number: '',
  name: '',
})

const deviceForm = reactive({
  name: '',
  serial_number: '',
  status: 'inactive',
})

const ownerForm = reactive({
  owner_id: undefined as number | undefined,
})

const isAdmin = computed(() => authStore.profile?.role === 'super_admin')
const canManageDevices = computed(
  () => Boolean(authStore.profile) && authStore.profile?.role !== 'device_user',
)
const deviceDialogTitle = computed(() =>
  t(deviceDialogMode.value === 'create' ? 'devices.createDialogTitle' : 'devices.editDialogTitle'),
)
const realtimeRefreshEvents = new Set([
  'module.status_updated',
  'alarm.created',
  'alarm.recovered',
  'relay_command.created',
  'relay_command.updated',
])

let realtimeRefreshTimer: number | null = null

function scheduleRealtimeRefresh() {
  if (realtimeRefreshTimer !== null) {
    window.clearTimeout(realtimeRefreshTimer)
  }
  realtimeRefreshTimer = window.setTimeout(() => {
    realtimeRefreshTimer = null
    void fetchDevices()
  }, 180)
}

function handleRealtimeEvent(message: RealtimeEventMessage) {
  if (!realtimeRefreshEvents.has(message.event)) {
    return
  }
  scheduleRealtimeRefresh()
}

const deviceRules: FormRules<typeof deviceForm> = {
  name: [{ required: true, message: t('devices.validations.nameRequired'), trigger: 'blur' }],
  serial_number: [
    {
      validator: (_rule, value, callback) => {
        if (deviceDialogMode.value === 'create' && !String(value || '').trim()) {
          callback(new Error(t('devices.validations.serialRequired')))
          return
        }
        callback()
      },
      trigger: 'blur',
    },
  ],
}

const filteredDevices = computed(() => {
  const search = keyword.value.trim().toLowerCase()
  if (!search) return devices.value
  return devices.value.filter(
    (item) =>
      item.device_name.toLowerCase().includes(search) ||
      item.serial_number.toLowerCase().includes(search),
  )
})

function resetDeviceForm() {
  deviceForm.name = ''
  deviceForm.serial_number = ''
  deviceForm.status = 'inactive'
}

function openCreateDialog() {
  currentDeviceId.value = null
  deviceDialogMode.value = 'create'
  resetDeviceForm()
  deviceDialogVisible.value = true
}

function openEditDialog(row: DeviceRow) {
  currentDeviceId.value = row.device_id
  deviceDialogMode.value = 'edit'
  deviceForm.name = row.device_name
  deviceForm.serial_number = row.serial_number
  deviceForm.status = row.status || 'inactive'
  deviceDialogVisible.value = true
}

function resolveOwnerName(ownerId: number | null) {
  if (!ownerId) return '--'
  return users.value.find((item) => item.id === ownerId)?.username || `#${ownerId}`
}

async function fetchDevices() {
  loading.value = true
  error.value = ''
  try {
    const requests: Promise<unknown>[] = [getDeviceMonitoringApi(), getDevicesApi()]
    if (isAdmin.value) {
      requests.push(getUsersApi())
    }
    const [monitoring, rawDevices, userData] = await Promise.all(requests)
    const deviceMap = new Map<number, DeviceRead>((rawDevices as DeviceRead[]).map((item) => [item.id, item]))
    devices.value = (monitoring as DeviceMonitoringItem[]).map((item) => ({
      ...item,
      owner_id: deviceMap.get(item.device_id)?.owner_id ?? null,
      status: deviceMap.get(item.device_id)?.status ?? 'inactive',
    }))
    users.value = ((userData as UserRead[]) || []).filter((item) => item.role !== 'super_admin')
  } catch (err: any) {
    error.value = err.response?.data?.detail || t('devices.loadError')
  } finally {
    loading.value = false
  }
}

function openOwnerDialog(row: DeviceRow) {
  currentDeviceId.value = row.device_id
  ownerForm.owner_id = row.owner_id || undefined
  ownerDialogVisible.value = true
}

async function submitDevice() {
  const valid = await deviceFormRef.value?.validate().catch(() => false)
  if (!valid) return

  submitting.value = true
  try {
    if (deviceDialogMode.value === 'create') {
      const createdDevice = await createDeviceApi({
        name: deviceForm.name.trim(),
        serial_number: deviceForm.serial_number.trim(),
      })
      ElMessage.success(t('devices.createSuccess'))
      // 创建成功后拉取 MQTT 配置并展示给管理员
      try {
        lastCreatedMqttConfig.value = await getDeviceMqttConfigApi(createdDevice.id)
        mqttConfigVisible.value = true
      } catch { /* 不影响主流程 */ }
    } else if (currentDeviceId.value) {
      await updateDeviceApi(currentDeviceId.value, {
        name: deviceForm.name.trim(),
        status: deviceForm.status,
      })
      ElMessage.success(t('devices.updateSuccess'))
    }
    deviceDialogVisible.value = false
    await fetchDevices()
  } catch (err: any) {
    ElMessage.error(err.response?.data?.detail || t('devices.saveFailed'))
  } finally {
    submitting.value = false
  }
}

async function submitOwner() {
  if (!currentDeviceId.value) return
  submitting.value = true
  try {
    if (ownerForm.owner_id == null) {
      await unbindDeviceApi(currentDeviceId.value)
    } else {
      await assignDeviceOwnerApi(currentDeviceId.value, ownerForm.owner_id)
    }
    ElMessage.success(t('devices.ownerUpdated'))
    ownerDialogVisible.value = false
    await fetchDevices()
  } catch (err: any) {
    ElMessage.error(err.response?.data?.detail || t('devices.ownerUpdateFailed'))
  } finally {
    submitting.value = false
  }
}

async function submitBind() {
  const serial = bindForm.serial_number.trim()
  if (!serial) {
    ElMessage.error(t('devices.validations.serialRequired'))
    return
  }

  submitting.value = true
  try {
    await bindDeviceApi({
      serial_number: serial,
      name: bindForm.name.trim() || undefined,
    })
    ElMessage.success(t('devices.bindSuccess'))
    bindDialogVisible.value = false
    bindForm.serial_number = ''
    bindForm.name = ''
    await fetchDevices()
  } catch (err: any) {
    ElMessage.error(err.response?.data?.detail || t('devices.bindError'))
  } finally {
    submitting.value = false
  }
}

async function showMqttConfig(deviceId: number) {
  try {
    lastCreatedMqttConfig.value = await getDeviceMqttConfigApi(deviceId)
    mqttConfigVisible.value = true
  } catch (err: any) {
    ElMessage.error(err.response?.data?.detail || 'MQTT 配置获取失败')
  }
}

async function handleDeleteDevice(row: DeviceRow) {
  try {
    await ElMessageBox.confirm(t('devices.deleteConfirm'), t('devices.deleteTitle'), {
      type: 'warning',
    })
    await deleteDeviceApi(row.device_id)
    ElMessage.success(t('devices.deleteSuccess'))
    await fetchDevices()
  } catch (err: any) {
    if (err === 'cancel' || err?.message === 'cancel') return
    ElMessage.error(err.response?.data?.detail || t('devices.deleteFailed'))
  }
}

async function handleUnbind(deviceId: number) {
  try {
    await ElMessageBox.confirm(t('devices.unbindConfirm'), t('devices.unbind'), {
      type: 'warning',
    })
    await unbindDeviceApi(deviceId)
    ElMessage.success(t('devices.unbindSuccess'))
    await fetchDevices()
  } catch (err: any) {
    if (err === 'cancel' || err?.message === 'cancel') return
    ElMessage.error(err.response?.data?.detail || t('devices.unbindError'))
  }
}

function copyMqttConfig() {
  if (!lastCreatedMqttConfig.value) return
  const c = lastCreatedMqttConfig.value
  const text = [
    `MQTT 服务器: ${c.broker_host}`,
    `端口: ${c.broker_port}`,
    `TLS: ${c.tls_enabled ? '是' : '否'}`,
    `用户名: ${c.mqtt_username}`,
    `密码: ${c.mqtt_password}`,
    `客户端ID: ${c.mqtt_client_id}`,
    `发布Topic: ${c.mqtt_pub_topic}`,
    `订阅Topic: ${c.mqtt_sub_topic}`,
  ].join('\n')
  navigator.clipboard.writeText(text).then(() => {
    ElMessage.success('已复制到剪贴板')
  }).catch(() => {
    ElMessage.warning('复制失败，请手动复制')
  })
}

useRealtime('devices', handleRealtimeEvent)

onMounted(() => {
  void fetchDevices()
})

onBeforeUnmount(() => {
  if (realtimeRefreshTimer !== null) {
    window.clearTimeout(realtimeRefreshTimer)
    realtimeRefreshTimer = null
  }
})
</script>
