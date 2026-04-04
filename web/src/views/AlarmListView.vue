<template>
  <div class="page-shell">
    <div class="page-title">
      <div>
        <h1>{{ t('alarms.title') }}</h1>
        <p>{{ t('alarms.description') }}</p>
      </div>
    </div>

    <PanelCard>
      <div class="toolbar">
        <div class="toolbar__filters">
          <el-input
            v-model="filters.keyword"
            clearable
            :placeholder="t('alarms.keywordPlaceholder')"
            style="width: 220px"
          />
          <el-select v-model="filters.alarmType" clearable :placeholder="t('alarms.alarmType')" style="width: 160px">
            <el-option :label="t('alarms.types.low_battery')" value="low_battery" />
            <el-option :label="t('alarms.types.low_voltage')" value="low_voltage" />
            <el-option :label="t('alarms.types.high_voltage')" value="high_voltage" />
          </el-select>
          <el-select v-model="filters.alarmStatus" clearable :placeholder="t('alarms.alarmStatus')" style="width: 160px">
            <el-option :label="t('status.alarm.triggered')" value="triggered" />
            <el-option :label="t('status.alarm.recovered')" value="recovered" />
          </el-select>
          <el-select v-model="filters.linkageStatus" clearable :placeholder="t('alarms.linkageStatus')" style="width: 160px">
            <el-option :label="t('status.linkage.pending')" value="pending" />
            <el-option :label="t('status.linkage.success')" value="success" />
            <el-option :label="t('status.linkage.failed')" value="failed" />
            <el-option :label="t('status.linkage.partial')" value="partial" />
          </el-select>
          <el-date-picker
            v-model="filters.timeRange"
            type="datetimerange"
            :start-placeholder="t('alarms.timeStart')"
            :end-placeholder="t('alarms.timeEnd')"
            value-format="YYYY-MM-DDTHH:mm:ss"
            style="width: 360px"
          />
        </div>

        <div class="toolbar__actions">
          <el-button type="primary" @click="fetchPage(1)">{{ t('common.applyFilters') }}</el-button>
          <el-button plain @click="resetFilters">{{ t('common.reset') }}</el-button>
          <el-button type="primary" plain @click="fetchPage(currentPage)">{{ t('common.refresh') }}</el-button>
        </div>
      </div>
    </PanelCard>

    <PanelCard :title="t('alarms.title')" :description="t('alarms.description')">
      <DataState
        :loading="loading"
        :error="error"
        :empty="!filteredItems.length"
        :empty-text="t('alarms.noData')"
        @retry="fetchPage(currentPage)"
      >
        <div class="data-table">
          <el-table :data="filteredItems">
            <el-table-column prop="device_name" :label="t('alarms.table.deviceName')" min-width="180" />
            <el-table-column prop="module_code" :label="t('alarms.table.moduleCode')" min-width="100" />
            <el-table-column prop="alarm_type" :label="t('alarms.table.alarmType')" min-width="120" />
            <el-table-column :label="t('alarms.table.alarmStatus')" min-width="110">
              <template #default="{ row }">
                <StatusPill :value="row.alarm_status" :mapping="alarmStatusMeta" />
              </template>
            </el-table-column>
            <el-table-column :label="t('alarms.table.linkageStatus')" min-width="120">
              <template #default="{ row }">
                <StatusPill :value="row.linkage_status" :mapping="linkageStatusMeta" />
              </template>
            </el-table-column>
            <el-table-column prop="source" :label="t('alarms.table.source')" min-width="110" />
            <el-table-column prop="message" :label="t('alarms.table.message')" min-width="220" show-overflow-tooltip />
            <el-table-column :label="t('alarms.table.triggeredAt')" min-width="180">
              <template #default="{ row }">
                {{ formatDateTime(row.triggered_at) }}
              </template>
            </el-table-column>
          </el-table>
        </div>

        <div class="table-pagination">
          <el-pagination
            v-model:current-page="currentPage"
            :page-size="pageSize"
            :total="paginationTotal"
            background
            layout="total, prev, pager, next"
            @current-change="fetchPage"
          />
        </div>
      </DataState>
    </PanelCard>
  </div>
</template>

<script setup lang="ts">
import { reactive, ref } from 'vue'

import { getDashboardAlarmPageApi } from '@/api/dashboard'
import DataState from '@/components/DataState.vue'
import PanelCard from '@/components/PanelCard.vue'
import StatusPill from '@/components/StatusPill.vue'
import { useI18n } from '@/composables/useI18n'
import type { DashboardAlarmItem } from '@/types/domain'
import { formatDateTime } from '@/utils/format'
import { alarmStatusMeta, linkageStatusMeta } from '@/utils/status'

const { t } = useI18n()
const loading = ref(true)
const error = ref('')
const currentPage = ref(1)
const pageSize = 10
const paginationTotal = ref(0)
const items = ref<DashboardAlarmItem[]>([])

const filters = reactive({
  keyword: '',
  alarmType: '',
  alarmStatus: '',
  linkageStatus: '',
  timeRange: [] as string[],
})

const filteredItems = items

async function fetchPage(page = 1) {
  loading.value = true
  error.value = ''
  currentPage.value = page
  try {
    const offset = (page - 1) * pageSize
    const data = await getDashboardAlarmPageApi(pageSize, offset, {
      keyword: filters.keyword || undefined,
      alarm_type: filters.alarmType || undefined,
      alarm_status: filters.alarmStatus || undefined,
      linkage_status: filters.linkageStatus || undefined,
      triggered_from: filters.timeRange[0] || undefined,
      triggered_to: filters.timeRange[1] || undefined,
    })
    items.value = data.items
    paginationTotal.value = data.pagination.total
  } catch (err: any) {
    error.value = err.response?.data?.detail || t('alarms.loadError')
  } finally {
    loading.value = false
  }
}

function resetFilters() {
  filters.keyword = ''
  filters.alarmType = ''
  filters.alarmStatus = ''
  filters.linkageStatus = ''
  filters.timeRange = []
  void fetchPage(1)
}

void fetchPage()
</script>
