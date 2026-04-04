<template>
  <div class="page-shell">
    <div class="page-title">
      <div>
        <h1>{{ t('scheduler.title') }}</h1>
        <p>{{ t('scheduler.description') }}</p>
      </div>
      <el-button type="primary" plain @click="refreshAll">{{ t('common.refresh') }}</el-button>
    </div>

    <DataState :loading="loading" :error="error" :empty="!scheduler && !history.length && !backups.length" @retry="refreshAll">
      <PanelCard :title="t('scheduler.title')" :description="t('scheduler.description')">
      <div class="toolbar" style="margin-bottom: 16px">
        <div class="toolbar__actions" style="flex-wrap: wrap">
          <el-button :loading="runningJob === 'offline'" @click="runJob('offline')">{{ t('scheduler.offlineCheck') }}</el-button>
          <el-button :loading="runningJob === 'retry'" @click="runJob('retry')">{{ t('scheduler.retryPending') }}</el-button>
          <el-button :loading="runningJob === 'recovery'" @click="runJob('recovery')">{{ t('scheduler.recoveryCheck') }}</el-button>
          <el-button :loading="runningJob === 'cleanup'" @click="runJob('cleanup')">{{ t('scheduler.cleanupFiles') }}</el-button>
          <el-button type="primary" :loading="runningJob === 'backup'" @click="runJob('backup')">{{ t('scheduler.backupDatabase') }}</el-button>
        </div>
      </div>

      <div class="page-grid" style="grid-template-columns: 1fr 1fr">
        <PanelCard :title="t('scheduler.jobs')" :description="t('scheduler.sections.jobsDesc')">
          <div class="data-table">
            <el-table :data="scheduler?.jobs ?? []">
              <el-table-column prop="id" :label="t('scheduler.table.id')" min-width="200" />
              <el-table-column prop="trigger" :label="t('scheduler.table.trigger')" min-width="220" show-overflow-tooltip />
              <el-table-column :label="t('scheduler.table.nextRun')" min-width="180">
                <template #default="{ row }">{{ formatDateTime(row.next_run_time) }}</template>
              </el-table-column>
            </el-table>
          </div>
        </PanelCard>

        <PanelCard :title="t('scheduler.backups')" :description="t('scheduler.sections.backupsDesc')">
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

      <PanelCard :title="t('scheduler.history')" :description="t('scheduler.sections.historyDesc')">
        <div class="data-table">
          <el-table :data="history">
            <el-table-column prop="job_name" :label="t('scheduler.table.job')" min-width="180" />
            <el-table-column prop="trigger_type" :label="t('scheduler.table.trigger')" min-width="110" />
            <el-table-column prop="status" :label="t('common.status')" min-width="110" />
            <el-table-column prop="message" :label="t('common.columns.message')" min-width="240" show-overflow-tooltip />
            <el-table-column :label="t('common.columns.startedAt')" min-width="180">
              <template #default="{ row }">{{ formatDateTime(row.started_at) }}</template>
            </el-table-column>
            <el-table-column :label="t('common.columns.finishedAt')" min-width="180">
              <template #default="{ row }">{{ formatDateTime(row.finished_at) }}</template>
            </el-table-column>
          </el-table>
        </div>
      </PanelCard>
      </PanelCard>
    </DataState>
  </div>
</template>

<script setup lang="ts">
import { ElMessage } from 'element-plus'
import { onMounted, ref } from 'vue'

import {
  getBackupsApi,
  getJobHistoryApi,
  getSchedulerStatusApi,
  runAlarmRecoveryCheckApi,
  runBackupDatabaseApi,
  runCleanupFilesApi,
  runOfflineCheckApi,
  runRetryPendingApi,
} from '@/api/jobs'
import DataState from '@/components/DataState.vue'
import PanelCard from '@/components/PanelCard.vue'
import { useI18n } from '@/composables/useI18n'
import type { DatabaseBackupFileRead, JobExecutionLogRead, SchedulerStatus } from '@/types/domain'
import { formatDateTime } from '@/utils/format'

const { t } = useI18n()
const loading = ref(true)
const error = ref('')
const scheduler = ref<SchedulerStatus | null>(null)
const history = ref<JobExecutionLogRead[]>([])
const backups = ref<DatabaseBackupFileRead[]>([])
const runningJob = ref<'offline' | 'retry' | 'recovery' | 'cleanup' | 'backup' | ''>('')

async function refreshAll() {
  loading.value = true
  error.value = ''
  try {
    const [schedulerData, historyData, backupData] = await Promise.all([
      getSchedulerStatusApi(),
      getJobHistoryApi({ limit: 20 }),
      getBackupsApi(20),
    ])
    scheduler.value = schedulerData
    history.value = historyData
    backups.value = backupData
  } catch (err: any) {
    error.value = err.response?.data?.detail || t('scheduler.loadError')
  } finally {
    loading.value = false
  }
}

async function runJob(kind: typeof runningJob.value) {
  if (!kind) return
  runningJob.value = kind
  try {
    if (kind === 'offline') await runOfflineCheckApi()
    if (kind === 'retry') await runRetryPendingApi()
    if (kind === 'recovery') await runAlarmRecoveryCheckApi()
    if (kind === 'cleanup') await runCleanupFilesApi()
    if (kind === 'backup') await runBackupDatabaseApi()
    ElMessage.success(t('scheduler.runSuccess'))
    await refreshAll()
  } catch (err: any) {
    ElMessage.error(err.response?.data?.detail || t('scheduler.runFailed'))
  } finally {
    runningJob.value = ''
  }
}

onMounted(() => {
  void refreshAll()
})
</script>
