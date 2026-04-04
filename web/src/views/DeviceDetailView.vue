<template>
  <div class="page-shell">
    <div class="page-title">
      <div>
        <h1>{{ detail?.device_name || t('deviceDetail.title') }}</h1>
        <p>{{ t('deviceDetail.description') }}</p>
      </div>
      <div class="toolbar__actions">
        <el-button plain @click="router.push('/devices')">{{ t('common.back') }}</el-button>
        <el-button v-if="canManageDevice" @click="openDeviceDialog">{{ t('deviceDetail.editDevice') }}</el-button>
        <el-button v-if="canManageDevice" type="primary" @click="moduleDialogVisible = true">
          {{ t('deviceDetail.addModule') }}
        </el-button>
        <el-button v-if="isAdmin" type="danger" plain @click="handleDeleteDevice">
          {{ t('deviceDetail.deleteDevice') }}
        </el-button>
        <el-button type="primary" plain @click="refreshAll">{{ t('common.refresh') }}</el-button>
      </div>
    </div>

    <DataState :loading="loading" :error="error" @retry="refreshAll">
      <div class="page-grid detail-grid">
        <PanelCard :title="t('deviceDetail.overviewTitle')" :description="t('deviceDetail.overviewDesc')">
          <div class="kv-list">
            <div class="kv-item">
              <div class="kv-item__label">{{ t('deviceDetail.fields.deviceName') }}</div>
              <div class="kv-item__value">{{ detail?.device_name || '--' }}</div>
            </div>
            <div class="kv-item">
              <div class="kv-item__label">{{ t('deviceDetail.fields.serial') }}</div>
              <div class="kv-item__value mono">{{ detail?.serial_number }}</div>
            </div>
            <div class="kv-item">
              <div class="kv-item__label">{{ t('deviceDetail.fields.status') }}</div>
              <div class="kv-item__value">
                <StatusPill :value="detail?.device_status" :mapping="deviceStatusMeta" />
              </div>
            </div>
            <div class="kv-item">
              <div class="kv-item__label">{{ t('deviceDetail.fields.moduleCount') }}</div>
              <div class="kv-item__value">{{ detail?.module_count ?? 0 }}</div>
            </div>
            <div class="kv-item">
              <div class="kv-item__label">{{ t('deviceDetail.fields.onlineCount') }}</div>
              <div class="kv-item__value">{{ detail?.online_module_count ?? 0 }}</div>
            </div>
            <div class="kv-item">
              <div class="kv-item__label">{{ t('deviceDetail.fields.latestAlarm') }}</div>
              <div class="kv-item__value">{{ resolveAlarmTypeLabel(detail?.latest_alarm_type, t) }}</div>
            </div>
            <div class="kv-item">
              <div class="kv-item__label">{{ t('deviceDetail.fields.latestAlarmTime') }}</div>
              <div class="kv-item__value">{{ formatDateTime(detail?.latest_alarm_time) }}</div>
            </div>
          </div>
        </PanelCard>

        <PanelCard :title="t('deviceDetail.controlTitle')" :description="t('deviceDetail.controlDesc')">
          <DataState :empty="!device?.modules.length" :empty-text="t('deviceDetail.controlEmpty')">
            <div class="page-grid module-grid">
              <ModuleControlCard
                v-for="module in device?.modules ?? []"
                :key="module.id"
                :module="module"
                :loading-state="pendingControls[module.id] || ''"
                @control="handleControl"
              />
            </div>
          </DataState>
        </PanelCard>
      </div>

      <div class="page-grid detail-grid">
        <PanelCard :title="t('deviceDetail.manageTitle')" :description="t('deviceDetail.manageDesc')">
          <div class="kv-list">
            <div class="kv-item">
              <div class="kv-item__label">{{ t('devices.nameLabel') }}</div>
              <div class="kv-item__value">{{ device?.name || '--' }}</div>
            </div>
            <div class="kv-item">
              <div class="kv-item__label">{{ t('devices.serialLabel') }}</div>
              <div class="kv-item__value mono">{{ device?.serial_number || '--' }}</div>
            </div>
            <div class="kv-item">
              <div class="kv-item__label">{{ t('devices.statusLabel') }}</div>
              <div class="kv-item__value">{{ resolveDeviceBusinessStatusLabel(device?.status, t) }}</div>
            </div>
            <div class="kv-item">
              <div class="kv-item__label">{{ t('devices.owner') }}</div>
              <div class="kv-item__value">{{ detail?.owner_id ?? '--' }}</div>
            </div>
          </div>
        </PanelCard>

        <PanelCard :title="t('deviceDetail.modulesTitle')" :description="t('deviceDetail.modulesDesc')">
          <DataState :empty="!device?.modules.length" :empty-text="t('deviceDetail.controlEmpty')">
            <div class="data-table">
              <el-table :data="device?.modules ?? []">
                <el-table-column prop="module_code" :label="t('common.columns.moduleCode')" min-width="120" />
                <el-table-column :label="t('common.status')" min-width="100">
                  <template #default="{ row }">
                    <el-tag :type="row.is_online ? 'success' : 'info'" effect="dark" round>
                      {{ row.is_online ? t('dashboard.modulePanels.status.online') : t('dashboard.modulePanels.status.offline') }}
                    </el-tag>
                  </template>
                </el-table-column>
                <el-table-column :label="t('moduleControl.battery')" min-width="100">
                  <template #default="{ row }">{{ row.battery_level ?? '--' }}</template>
                </el-table-column>
                <el-table-column :label="t('moduleControl.voltage')" min-width="100">
                  <template #default="{ row }">{{ row.voltage_value ?? '--' }}</template>
                </el-table-column>
                <el-table-column :label="t('moduleControl.lastSeen')" min-width="180">
                  <template #default="{ row }">{{ formatDateTime(row.last_seen_at) }}</template>
                </el-table-column>
                <el-table-column v-if="canManageDevice" :label="t('common.actions')" min-width="120">
                  <template #default="{ row }">
                    <el-button link type="danger" @click="handleDeleteModule(row.id)">
                      {{ t('common.delete') }}
                    </el-button>
                  </template>
                </el-table-column>
              </el-table>
            </div>
          </DataState>
        </PanelCard>
      </div>

      <div class="page-grid detail-grid">
        <PanelCard :title="t('deviceDetail.recentAlarmsTitle')" :description="t('deviceDetail.recentAlarmsDesc')">
          <DataState :empty="!detail?.recent_alarms.length" :empty-text="t('deviceDetail.noAlarms')">
            <div class="data-table">
              <el-table :data="detail?.recent_alarms ?? []">
                <el-table-column prop="module_code" :label="t('common.columns.moduleCode')" min-width="100" />
                <el-table-column :label="t('alarms.table.alarmType')" min-width="120">
                  <template #default="{ row }">
                    {{ resolveAlarmTypeLabel(row.alarm_type, t) }}
                  </template>
                </el-table-column>
                <el-table-column :label="t('alarms.table.alarmStatus')" min-width="110">
                  <template #default="{ row }">
                    <StatusPill :value="row.alarm_status" :mapping="alarmStatusMeta" />
                  </template>
                </el-table-column>
                <el-table-column prop="message" :label="t('alarms.table.message')" min-width="220" show-overflow-tooltip />
                <el-table-column :label="t('alarms.table.triggeredAt')" min-width="180">
                  <template #default="{ row }">
                    {{ formatDateTime(row.triggered_at) }}
                  </template>
                </el-table-column>
              </el-table>
            </div>
          </DataState>
        </PanelCard>

        <PanelCard :title="t('deviceDetail.recentCommandsTitle')" :description="t('deviceDetail.recentCommandsDesc')">
          <DataState :empty="!detail?.recent_commands.length" :empty-text="t('deviceDetail.noCommands')">
            <div class="data-table">
              <el-table :data="detail?.recent_commands ?? []">
                <el-table-column prop="module_code" :label="t('common.columns.moduleCode')" min-width="100" />
                <el-table-column :label="t('deviceDetail.fields.targetState')" min-width="110">
                  <template #default="{ row }">
                    {{ resolveRelayTargetLabel(row.target_state, t) }}
                  </template>
                </el-table-column>
                <el-table-column :label="t('common.status')" min-width="110">
                  <template #default="{ row }">
                    <StatusPill :value="row.execution_status" :mapping="commandStatusMeta" />
                  </template>
                </el-table-column>
                <el-table-column prop="feedback_message" :label="t('deviceDetail.fields.feedbackMessage')" min-width="220" show-overflow-tooltip />
                <el-table-column :label="t('common.columns.createdAt')" min-width="180">
                  <template #default="{ row }">
                    {{ formatDateTime(row.created_at) }}
                  </template>
                </el-table-column>
              </el-table>
            </div>
          </DataState>
        </PanelCard>
      </div>
    </DataState>

    <el-dialog v-model="deviceDialogVisible" :title="t('deviceDetail.editDevice')" width="460px">
      <el-form ref="deviceFormRef" :model="deviceForm" :rules="deviceRules" label-position="top">
        <el-form-item :label="t('devices.nameLabel')" prop="name">
          <el-input v-model="deviceForm.name" :placeholder="t('devices.namePlaceholder')" />
        </el-form-item>
        <el-form-item :label="t('devices.serialLabel')">
          <el-input :model-value="device?.serial_number || ''" disabled />
        </el-form-item>
        <el-form-item :label="t('devices.statusLabel')" prop="status">
          <el-select v-model="deviceForm.status" style="width: 100%">
            <el-option :label="t('status.device.active')" value="active" />
            <el-option :label="t('status.device.inactive')" value="inactive" />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="deviceDialogVisible = false">{{ t('common.cancel') }}</el-button>
        <el-button type="primary" :loading="submittingDevice" @click="submitDeviceUpdate">
          {{ t('common.save') }}
        </el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="moduleDialogVisible" :title="t('deviceDetail.addModuleDialogTitle')" width="420px">
      <el-form ref="moduleFormRef" :model="moduleForm" :rules="moduleRules" label-position="top">
        <el-form-item :label="t('deviceDetail.moduleCodeLabel')" prop="module_code">
          <el-input v-model="moduleForm.module_code" :placeholder="t('deviceDetail.moduleCodePlaceholder')" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="moduleDialogVisible = false">{{ t('common.cancel') }}</el-button>
        <el-button type="primary" :loading="submittingModule" @click="submitModule">
          {{ t('common.confirm') }}
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import type { FormInstance, FormRules } from 'element-plus'
import { ElMessage, ElMessageBox } from 'element-plus'
import { computed, onBeforeUnmount, onMounted, reactive, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'

import { getDashboardDeviceDetailApi } from '@/api/dashboard'
import {
  createDeviceModuleApi,
  createRelayCommandApi,
  deleteDeviceApi,
  deleteDeviceModuleApi,
  getDeviceApi,
  updateDeviceApi,
} from '@/api/devices'
import DataState from '@/components/DataState.vue'
import ModuleControlCard from '@/components/ModuleControlCard.vue'
import PanelCard from '@/components/PanelCard.vue'
import StatusPill from '@/components/StatusPill.vue'
import { useI18n } from '@/composables/useI18n'
import { usePolling } from '@/composables/usePolling'
import { useRealtime } from '@/composables/useRealtime'
import { useAuthStore } from '@/stores/auth'
import type { DashboardDeviceDetail, DeviceRead, RealtimeEventMessage } from '@/types/domain'
import { formatDateTime } from '@/utils/format'
import {
  resolveAlarmTypeLabel,
  resolveDeviceBusinessStatusLabel,
  resolveRelayTargetLabel,
} from '@/utils/labels'
import { alarmStatusMeta, commandStatusMeta, deviceStatusMeta } from '@/utils/status'

const route = useRoute()
const router = useRouter()
const { t } = useI18n()
const authStore = useAuthStore()
const loading = ref(true)
const error = ref('')
const detail = ref<DashboardDeviceDetail | null>(null)
const device = ref<DeviceRead | null>(null)
const pendingControls = reactive<Record<number, '' | 'open' | 'closed'>>({})
const deviceDialogVisible = ref(false)
const moduleDialogVisible = ref(false)
const deviceFormRef = ref<FormInstance>()
const moduleFormRef = ref<FormInstance>()
const submittingDevice = ref(false)
const submittingModule = ref(false)

const deviceForm = reactive({
  name: '',
  status: 'inactive',
})

const moduleForm = reactive({
  module_code: '',
})

const deviceRules: FormRules<typeof deviceForm> = {
  name: [{ required: true, message: t('devices.validations.nameRequired'), trigger: 'blur' }],
}

const moduleRules: FormRules<typeof moduleForm> = {
  module_code: [{ required: true, message: t('deviceDetail.moduleCodePlaceholder'), trigger: 'blur' }],
}

const deviceId = Number(route.params.id)
const isAdmin = computed(() => authStore.profile?.role === 'super_admin')
const canManageDevice = computed(() => Boolean(authStore.profile))
const moduleIds = computed(() => new Set((device.value?.modules ?? []).map((item) => item.id)))
const realtimeRefreshEvents = new Set([
  'module.status_updated',
  'alarm.created',
  'alarm.recovered',
  'relay_command.created',
  'relay_command.updated',
])

let realtimeRefreshTimer: number | null = null

function resolveNumericField(value: unknown) {
  if (typeof value === 'number' && Number.isFinite(value)) {
    return value
  }
  if (typeof value === 'string' && value.trim()) {
    const parsed = Number(value)
    return Number.isFinite(parsed) ? parsed : null
  }
  return null
}

function isRealtimeEventForCurrentDevice(message: RealtimeEventMessage) {
  if (!realtimeRefreshEvents.has(message.event)) {
    return false
  }

  const eventDeviceId = resolveNumericField(message.data.device_id)
  if (eventDeviceId === deviceId) {
    return true
  }

  const eventModuleId = resolveNumericField(message.data.module_id)
  return eventModuleId !== null && moduleIds.value.has(eventModuleId)
}

function scheduleRealtimeRefresh() {
  if (realtimeRefreshTimer !== null) {
    window.clearTimeout(realtimeRefreshTimer)
  }
  realtimeRefreshTimer = window.setTimeout(() => {
    realtimeRefreshTimer = null
    void refreshAll()
  }, 180)
}

function handleRealtimeEvent(message: RealtimeEventMessage) {
  if (!isRealtimeEventForCurrentDevice(message)) {
    return
  }
  scheduleRealtimeRefresh()
}

async function refreshAll() {
  loading.value = detail.value === null
  error.value = ''
  try {
    const [detailData, deviceData] = await Promise.all([
      getDashboardDeviceDetailApi(deviceId),
      getDeviceApi(deviceId),
    ])
    detail.value = detailData
    device.value = deviceData
    deviceForm.name = deviceData.name
    deviceForm.status = deviceData.status || 'inactive'
  } catch (err: any) {
    error.value = err.response?.data?.detail || t('deviceDetail.loadError')
  } finally {
    loading.value = false
  }
}

function openDeviceDialog() {
  deviceForm.name = device.value?.name || ''
  deviceForm.status = device.value?.status || 'inactive'
  deviceDialogVisible.value = true
}

async function submitDeviceUpdate() {
  const valid = await deviceFormRef.value?.validate().catch(() => false)
  if (!valid) return

  submittingDevice.value = true
  try {
    await updateDeviceApi(deviceId, {
      name: deviceForm.name.trim(),
      status: deviceForm.status,
    })
    ElMessage.success(t('deviceDetail.updateSuccess'))
    deviceDialogVisible.value = false
    await refreshAll()
  } catch (err: any) {
    ElMessage.error(err.response?.data?.detail || t('deviceDetail.updateFailed'))
  } finally {
    submittingDevice.value = false
  }
}

async function submitModule() {
  const valid = await moduleFormRef.value?.validate().catch(() => false)
  if (!valid) return

  submittingModule.value = true
  try {
    await createDeviceModuleApi(deviceId, {
      module_code: moduleForm.module_code.trim(),
    })
    ElMessage.success(t('deviceDetail.moduleAddSuccess'))
    moduleDialogVisible.value = false
    moduleForm.module_code = ''
    await refreshAll()
  } catch (err: any) {
    ElMessage.error(err.response?.data?.detail || t('deviceDetail.moduleAddFailed'))
  } finally {
    submittingModule.value = false
  }
}

async function handleDeleteModule(moduleId: number) {
  try {
    await ElMessageBox.confirm(t('deviceDetail.moduleDeleteConfirm'), t('deviceDetail.moduleDeleteTitle'), {
      type: 'warning',
    })
    await deleteDeviceModuleApi(moduleId)
    ElMessage.success(t('deviceDetail.moduleDeleteSuccess'))
    await refreshAll()
  } catch (err: any) {
    if (err === 'cancel' || err?.message === 'cancel') return
    ElMessage.error(err.response?.data?.detail || t('deviceDetail.moduleDeleteFailed'))
  }
}

async function handleDeleteDevice() {
  if (!isAdmin.value) {
    ElMessage.error(t('auth.forbidden'))
    return
  }
  try {
    await ElMessageBox.confirm(t('deviceDetail.deleteDeviceConfirm'), t('deviceDetail.deleteDeviceTitle'), {
      type: 'warning',
    })
    await deleteDeviceApi(deviceId)
    ElMessage.success(t('deviceDetail.deleteSuccess'))
    await router.push('/devices')
  } catch (err: any) {
    if (err === 'cancel' || err?.message === 'cancel') return
    ElMessage.error(err.response?.data?.detail || t('deviceDetail.deleteFailed'))
  }
}

async function handleControl(moduleId: number, targetState: 'open' | 'closed') {
  pendingControls[moduleId] = targetState
  try {
    await createRelayCommandApi({
      module_id: moduleId,
      target_state: targetState,
      command_source: 'manual_control',
    })
    ElMessage.success(t('deviceDetail.commandCreated'))
    await refreshAll()
  } catch (err: any) {
    ElMessage.error(err.response?.data?.detail || t('deviceDetail.commandCreateFailed'))
  } finally {
    pendingControls[moduleId] = ''
  }
}

const { start } = usePolling(refreshAll, 30000)
useRealtime('device-detail', handleRealtimeEvent)

onMounted(async () => {
  await refreshAll()
  start()
})

onBeforeUnmount(() => {
  if (realtimeRefreshTimer !== null) {
    window.clearTimeout(realtimeRefreshTimer)
    realtimeRefreshTimer = null
  }
})
</script>

<style scoped>
.detail-grid {
  grid-template-columns: repeat(2, minmax(0, 1fr));
}

.module-grid {
  grid-template-columns: repeat(2, minmax(0, 1fr));
}

@media (max-width: 1200px) {
  .detail-grid,
  .module-grid {
    grid-template-columns: 1fr;
  }
}
</style>
