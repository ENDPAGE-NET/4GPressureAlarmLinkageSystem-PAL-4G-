<template>
  <div class="page-shell">
    <div class="page-title">
      <div>
        <h1>{{ t('logs.title') }}</h1>
        <p>{{ t('logs.description') }}</p>
      </div>
      <div class="toolbar__actions">
        <el-button plain @click="download('alarms')">{{ t('exports.alarms') }}</el-button>
        <el-button type="primary" plain @click="download('commands')">{{ t('exports.commands') }}</el-button>
      </div>
    </div>

    <div class="stats-grid">
      <MetricCard :title="t('logs.overview')" :value="overview?.runtime_total ?? 0" tag-label="runtime" />
      <MetricCard :title="t('logs.runtimeErrors')" :value="overview?.runtime_error_count ?? 0" tag-label="error" tag-type="danger" />
      <MetricCard :title="t('logs.operationFailures')" :value="overview?.operation_failed_count ?? 0" tag-label="audit" tag-type="warning" />
      <MetricCard :title="t('logs.communicationFailures')" :value="overview?.communication_failed_count ?? 0" tag-label="comm" tag-type="info" />
    </div>

    <PanelCard :title="t('logs.title')" :description="t('logs.description')">
      <el-tabs v-model="activeTab" @tab-change="handleTabChange">
        <el-tab-pane :label="t('logs.runtime')" name="runtime" />
        <el-tab-pane :label="t('logs.operations')" name="operations" />
        <el-tab-pane :label="t('logs.communication')" name="communication" />
      </el-tabs>

      <div class="toolbar" style="margin-bottom: 16px">
        <div class="toolbar__filters">
          <el-input v-model="filters.keyword" clearable :placeholder="t('common.search')" style="width: 260px" />
          <el-input v-if="activeTab === 'runtime'" v-model="filters.secondary" clearable :placeholder="t('logs.filters.runtime')" style="width: 180px" />
          <el-input v-if="activeTab === 'operations'" v-model="filters.secondary" clearable :placeholder="t('logs.filters.operations')" style="width: 180px" />
          <el-input v-if="activeTab === 'communication'" v-model="filters.secondary" clearable :placeholder="t('logs.filters.communication')" style="width: 180px" />
        </div>
        <div class="toolbar__actions">
          <el-button type="primary" @click="fetchActive(1)">{{ t('common.applyFilters') }}</el-button>
          <el-button plain @click="resetFilters">{{ t('common.reset') }}</el-button>
        </div>
      </div>

      <DataState :loading="loading" :error="error" :empty="!currentRows.length" @retry="fetchActive(page.current)">
        <div class="data-table">
          <el-table v-if="activeTab === 'runtime'" :data="currentRows">
            <el-table-column prop="level" :label="t('logs.table.level')" min-width="100" />
            <el-table-column prop="event" :label="t('logs.table.event')" min-width="160" />
            <el-table-column prop="message" :label="t('common.columns.message')" min-width="260" show-overflow-tooltip />
            <el-table-column prop="context" :label="t('logs.table.context')" min-width="220" show-overflow-tooltip />
            <el-table-column :label="t('common.columns.createdAt')" min-width="180">
              <template #default="{ row }">{{ formatDateTime(row.created_at) }}</template>
            </el-table-column>
          </el-table>

          <el-table v-else-if="activeTab === 'operations'" :data="currentRows">
            <el-table-column prop="action" :label="t('logs.table.action')" min-width="160" />
            <el-table-column prop="target_type" :label="t('logs.table.target')" min-width="120" />
            <el-table-column prop="target_id" :label="t('logs.table.targetId')" min-width="90" />
            <el-table-column prop="status" :label="t('common.status')" min-width="100" />
            <el-table-column prop="detail" :label="t('common.columns.detail')" min-width="260" show-overflow-tooltip />
            <el-table-column :label="t('common.columns.createdAt')" min-width="180">
              <template #default="{ row }">{{ formatDateTime(row.created_at) }}</template>
            </el-table-column>
          </el-table>

          <el-table v-else :data="currentRows">
            <el-table-column prop="channel" :label="t('logs.table.channel')" min-width="120" />
            <el-table-column prop="direction" :label="t('logs.table.direction')" min-width="100" />
            <el-table-column prop="device_serial" :label="t('logs.table.serial')" min-width="150" />
            <el-table-column prop="module_code" :label="t('logs.table.module')" min-width="90" />
            <el-table-column prop="status" :label="t('common.status')" min-width="100" />
            <el-table-column prop="message" :label="t('common.columns.message')" min-width="220" show-overflow-tooltip />
            <el-table-column prop="payload" :label="t('logs.table.payload')" min-width="220" show-overflow-tooltip />
            <el-table-column :label="t('common.columns.createdAt')" min-width="180">
              <template #default="{ row }">{{ formatDateTime(row.created_at) }}</template>
            </el-table-column>
          </el-table>
        </div>

        <div class="table-pagination">
          <el-pagination
            v-model:current-page="page.current"
            :page-size="page.size"
            :total="page.total"
            background
            layout="total, prev, pager, next"
            @current-change="fetchActive"
          />
        </div>
      </DataState>
    </PanelCard>
  </div>
</template>

<script setup lang="ts">
import { ElMessage } from 'element-plus'
import { onMounted, reactive, ref } from 'vue'

import { exportAlarmsApi, exportCommandsApi } from '@/api/exports'
import { getCommunicationLogsPageApi, getLogsOverviewApi, getOperationLogsPageApi, getRuntimeLogsPageApi } from '@/api/logs'
import DataState from '@/components/DataState.vue'
import MetricCard from '@/components/MetricCard.vue'
import PanelCard from '@/components/PanelCard.vue'
import { useI18n } from '@/composables/useI18n'
import type { CommunicationLogRead, LogsOverview, OperationLogRead, RuntimeLogRead } from '@/types/domain'
import { formatDateTime } from '@/utils/format'

const { t } = useI18n()
const activeTab = ref<'runtime' | 'operations' | 'communication'>('runtime')
const loading = ref(true)
const error = ref('')
const overview = ref<LogsOverview | null>(null)
const runtimeRows = ref<RuntimeLogRead[]>([])
const operationRows = ref<OperationLogRead[]>([])
const communicationRows = ref<CommunicationLogRead[]>([])
const page = reactive({
  current: 1,
  size: 20,
  total: 0,
})
const filters = reactive({
  keyword: '',
  secondary: '',
})

const currentRows = ref<any[]>([])

async function fetchOverview() {
  overview.value = await getLogsOverviewApi()
}

async function refreshAll(nextPage = 1) {
  loading.value = true
  error.value = ''
  try {
    await fetchOverview()
    await fetchActive(nextPage)
  } catch (err: any) {
    error.value = err.response?.data?.detail || t('logs.loadError')
    loading.value = false
  }
}

async function fetchActive(nextPage = 1) {
  loading.value = true
  error.value = ''
  page.current = nextPage
  const offset = (nextPage - 1) * page.size

  try {
    if (activeTab.value === 'runtime') {
      const data = await getRuntimeLogsPageApi({
        level: filters.keyword || undefined,
        event: filters.secondary || undefined,
        limit: page.size,
        offset,
      })
      runtimeRows.value = data.items
      currentRows.value = data.items
      page.total = data.total
    } else if (activeTab.value === 'operations') {
      const data = await getOperationLogsPageApi({
        status: filters.keyword || undefined,
        action: filters.secondary || undefined,
        limit: page.size,
        offset,
      })
      operationRows.value = data.items
      currentRows.value = data.items
      page.total = data.total
    } else {
      const data = await getCommunicationLogsPageApi({
        status: filters.keyword || undefined,
        channel: filters.secondary || undefined,
        device_serial: filters.secondary || undefined,
        limit: page.size,
        offset,
      })
      communicationRows.value = data.items
      currentRows.value = data.items
      page.total = data.total
    }
  } catch (err: any) {
    error.value = err.response?.data?.detail || t('logs.loadError')
  } finally {
    loading.value = false
  }
}

function handleTabChange() {
  resetFilters(false)
  void fetchActive(1)
}

function resetFilters(withFetch = true) {
  filters.keyword = ''
  filters.secondary = ''
  if (withFetch) void fetchActive(1)
}

async function download(kind: 'alarms' | 'commands') {
  try {
    if (kind === 'alarms') {
      await exportAlarmsApi()
    } else {
      await exportCommandsApi()
    }
    ElMessage.success(t('exports.success'))
  } catch {
    ElMessage.error(t('logs.downloadError'))
  }
}

onMounted(async () => {
  await refreshAll(1)
})
</script>
