<template>
  <div class="page-shell">
    <div class="page-title">
      <div>
        <h1>{{ detail?.device_name || t('deviceDetail.title') }}</h1>
        <p>{{ t('deviceDetail.description') }}</p>
      </div>
      <div class="toolbar__actions">
        <el-button plain @click="router.push('/devices')">{{ t('common.back') }}</el-button>
        <el-button type="primary" plain @click="refreshAll">{{ t('common.refresh') }}</el-button>
      </div>
    </div>

    <DataState :loading="loading" :error="error" @retry="refreshAll">
      <div class="page-grid detail-grid">
        <PanelCard :title="t('deviceDetail.overviewTitle')" :description="t('deviceDetail.overviewDesc')">
          <div class="kv-list">
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
              <div class="kv-item__value">{{ detail?.latest_alarm_type || '--' }}</div>
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
        <PanelCard :title="t('deviceDetail.recentAlarmsTitle')" :description="t('deviceDetail.recentAlarmsDesc')">
          <DataState :empty="!detail?.recent_alarms.length" :empty-text="t('deviceDetail.noAlarms')">
            <div class="data-table">
              <el-table :data="detail?.recent_alarms ?? []">
                <el-table-column prop="module_code" :label="t('common.columns.moduleCode')" min-width="100" />
                <el-table-column prop="alarm_type" :label="t('alarms.table.alarmType')" min-width="120" />
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
                <el-table-column prop="target_state" :label="t('deviceDetail.fields.targetState')" min-width="110" />
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
  </div>
</template>

<script setup lang="ts">
import { ElMessage } from 'element-plus'
import { onMounted, reactive, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'

import { getDashboardDeviceDetailApi } from '@/api/dashboard'
import { createRelayCommandApi, getDeviceApi } from '@/api/devices'
import DataState from '@/components/DataState.vue'
import ModuleControlCard from '@/components/ModuleControlCard.vue'
import PanelCard from '@/components/PanelCard.vue'
import StatusPill from '@/components/StatusPill.vue'
import { useI18n } from '@/composables/useI18n'
import { usePolling } from '@/composables/usePolling'
import type { DashboardDeviceDetail, DeviceRead } from '@/types/domain'
import { formatDateTime } from '@/utils/format'
import { alarmStatusMeta, commandStatusMeta, deviceStatusMeta } from '@/utils/status'

const route = useRoute()
const router = useRouter()
const { t } = useI18n()
const loading = ref(true)
const error = ref('')
const detail = ref<DashboardDeviceDetail | null>(null)
const device = ref<DeviceRead | null>(null)
const pendingControls = reactive<Record<number, '' | 'open' | 'closed'>>({})

const deviceId = Number(route.params.id)

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
  } catch (err: any) {
    error.value = err.response?.data?.detail || t('deviceDetail.loadError')
  } finally {
    loading.value = false
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

onMounted(async () => {
  await refreshAll()
  start()
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
