<template>
  <div class="page-shell">
    <div class="page-title">
      <div>
        <h1>{{ t('operations.title') }}</h1>
        <p>{{ t('operations.description') }}</p>
      </div>
      <el-button type="primary" plain @click="refreshAll">{{ t('common.refresh') }}</el-button>
    </div>

    <DataState :loading="loading" :error="error" :empty="!scheduler && !mqtt && !logsOverview && !history.length && !backups.length" @retry="refreshAll">
      <div class="stats-grid">
        <MetricCard :title="t('operations.scheduler')" :value="scheduler?.jobs.length ?? 0" :tag-label="scheduler?.running ? t('operations.running') : t('operations.stopped')" :tag-type="scheduler?.running ? 'success' : 'danger'" />
        <MetricCard :title="t('operations.mqtt')" :value="mqtt?.received_message_count ?? 0" tag-label="inbound" />
        <MetricCard :title="t('logs.overview')" :value="logsOverview?.operation_total ?? 0" tag-label="audit" />
        <MetricCard :title="t('operations.backups')" :value="backups.length" :tag-label="t('operations.files')" />
      </div>

      <div class="page-grid" style="grid-template-columns: 1fr 1fr">
        <PanelCard :title="t('operations.scheduler')" :description="t('operations.sections.schedulerDesc')">
          <div class="kv-list">
            <div class="kv-item">
              <div class="kv-item__label">{{ t('operations.running') }}</div>
              <div class="kv-item__value">
                <el-tag :type="scheduler?.running ? 'success' : 'danger'" effect="dark" round>
                  {{ scheduler?.running ? t('operations.running') : t('operations.stopped') }}
                </el-tag>
              </div>
            </div>
            <div class="kv-item">
              <div class="kv-item__label">{{ t('scheduler.jobs') }}</div>
              <div class="kv-item__value">{{ scheduler?.jobs.length ?? 0 }}</div>
            </div>
          </div>
        </PanelCard>

        <PanelCard :title="t('operations.mqtt')" :description="t('operations.sections.mqttDesc')">
          <div class="kv-list">
            <div class="kv-item">
              <div class="kv-item__label">{{ t('mqtt.connected') }}</div>
              <div class="kv-item__value">
                <el-tag :type="mqtt?.connected ? 'success' : 'danger'" effect="dark" round>
                  {{ mqtt?.connected ? t('operations.running') : t('operations.stopped') }}
                </el-tag>
              </div>
            </div>
            <div class="kv-item">
              <div class="kv-item__label">{{ t('operations.messages') }}</div>
              <div class="kv-item__value">{{ mqtt?.received_message_count ?? 0 }} / {{ mqtt?.published_message_count ?? 0 }}</div>
            </div>
          </div>
        </PanelCard>
      </div>

      <div class="page-grid" style="grid-template-columns: 1fr 1fr">
        <PanelCard :title="t('operations.history')" :description="t('operations.sections.historyDesc')">
          <div class="data-table">
            <el-table :data="history">
              <el-table-column prop="job_name" :label="t('operations.table.job')" min-width="180" />
              <el-table-column prop="status" :label="t('common.status')" min-width="110" />
              <el-table-column prop="trigger_type" :label="t('operations.table.trigger')" min-width="110" />
              <el-table-column :label="t('common.columns.startedAt')" min-width="180">
                <template #default="{ row }">{{ formatDateTime(row.started_at) }}</template>
              </el-table-column>
            </el-table>
          </div>
        </PanelCard>

        <PanelCard :title="t('operations.backups')" :description="t('operations.sections.backupsDesc')">
          <div class="data-table">
            <el-table :data="backups">
              <el-table-column prop="backup_file" :label="t('operations.table.file')" min-width="220" show-overflow-tooltip />
              <el-table-column prop="file_size" :label="t('operations.table.size')" min-width="100" />
              <el-table-column :label="t('common.columns.createdAt')" min-width="180">
                <template #default="{ row }">{{ formatDateTime(row.created_at) }}</template>
              </el-table-column>
            </el-table>
          </div>
        </PanelCard>
      </div>
    </DataState>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'

import { getSchedulerStatusApi, getJobHistoryApi, getBackupsApi } from '@/api/jobs'
import { getLogsOverviewApi } from '@/api/logs'
import { getMqttStatusApi } from '@/api/mqtt'
import DataState from '@/components/DataState.vue'
import MetricCard from '@/components/MetricCard.vue'
import PanelCard from '@/components/PanelCard.vue'
import { useI18n } from '@/composables/useI18n'
import type { DatabaseBackupFileRead, JobExecutionLogRead, LogsOverview, MqttClientStatus, SchedulerStatus } from '@/types/domain'
import { formatDateTime } from '@/utils/format'

const { t } = useI18n()
const loading = ref(true)
const error = ref('')
const scheduler = ref<SchedulerStatus | null>(null)
const mqtt = ref<MqttClientStatus | null>(null)
const logsOverview = ref<LogsOverview | null>(null)
const history = ref<JobExecutionLogRead[]>([])
const backups = ref<DatabaseBackupFileRead[]>([])

async function refreshAll() {
  loading.value = true
  error.value = ''
  try {
    const [schedulerData, mqttData, overviewData, historyData, backupData] = await Promise.all([
      getSchedulerStatusApi(),
      getMqttStatusApi(),
      getLogsOverviewApi(),
      getJobHistoryApi({ limit: 5 }),
      getBackupsApi(5),
    ])
    scheduler.value = schedulerData
    mqtt.value = mqttData
    logsOverview.value = overviewData
    history.value = historyData
    backups.value = backupData
  } catch (err: any) {
    error.value = err.response?.data?.detail || t('operations.loadError')
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  void refreshAll()
})
</script>
