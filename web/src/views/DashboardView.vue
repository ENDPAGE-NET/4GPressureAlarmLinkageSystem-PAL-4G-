<template>
  <div class="page-shell">
    <div class="page-title">
      <div>
        <h1>{{ t('dashboard.title') }}</h1>
        <p>{{ t('dashboard.description') }}</p>
      </div>
      <el-button type="primary" plain @click="refreshAll">{{ t('common.refresh') }}</el-button>
    </div>

    <DataState :loading="loading" :error="error" @retry="refreshAll">
      <div class="dashboard-grid dashboard-grid--metrics">
        <MetricCard :title="t('dashboard.metrics.devices')" :value="home?.overview.total_devices ?? 0" :tag-label="t('dashboard.metrics.deviceTag')" />
        <MetricCard :title="t('dashboard.metrics.modules')" :value="home?.overview.total_modules ?? 0" :tag-label="t('dashboard.metrics.moduleTag')" />
        <MetricCard
          :title="t('dashboard.metrics.onlineModules')"
          :value="home?.overview.online_modules ?? 0"
          :tag-label="t('dashboard.metrics.onlineTag')"
          tag-type="success"
        />
        <MetricCard
          :title="t('dashboard.metrics.currentAlarms')"
          :value="home?.recent_alarm_count ?? 0"
          :tag-label="t('dashboard.metrics.alarmTag')"
          tag-type="danger"
        />
      </div>

      <template v-if="isManagerDashboard">
        <PanelCard :title="t('dashboard.modulePanels.title')" :description="t('dashboard.modulePanels.description')">
          <template #header>
            <span class="dashboard-polling-hint">{{ t('dashboard.modulePanels.autoRefresh') }}</span>
          </template>

          <DataState :empty="!modulePanels.length" :empty-text="t('dashboard.modulePanels.empty')">
            <div class="module-panel-grid">
              <ModuleOverviewCard v-for="item in modulePanels" :key="item.module_id" :item="item" />
            </div>
          </DataState>
        </PanelCard>
      </template>

      <template v-else>
        <div class="dashboard-grid dashboard-grid--charts">
          <PanelCard :title="t('dashboard.charts.alarmTitle')" :description="t('dashboard.charts.alarmDesc')">
            <DistributionChart
              :data="charts?.alarm_type_distribution ?? []"
              :color="['#ff6c6c', '#f3b24f', '#33c6d8', '#5fd0a5']"
              :series-name="t('dashboard.charts.alarmSeries')"
            />
          </PanelCard>

          <PanelCard :title="t('dashboard.charts.commandTitle')" :description="t('dashboard.charts.commandDesc')">
            <DistributionChart
              :data="charts?.command_status_distribution ?? []"
              :color="['#f3b24f', '#33c6d8', '#5fd0a5', '#ff6c6c']"
              :series-name="t('dashboard.charts.commandSeries')"
            />
          </PanelCard>

          <PanelCard :title="t('dashboard.charts.deviceTitle')" :description="t('dashboard.charts.deviceDesc')">
            <DistributionChart
              :data="charts?.device_status_distribution ?? []"
              :color="['#5fd0a5', '#607d8b', '#e7b04a']"
              :series-name="t('dashboard.charts.deviceSeries')"
            />
          </PanelCard>
        </div>

        <div class="dashboard-grid dashboard-grid--content">
          <PanelCard :title="t('dashboard.monitoring.title')" :description="t('dashboard.monitoring.description')">
            <DataState :empty="!home?.monitoring.length" :empty-text="t('dashboard.monitoring.empty')">
              <div class="data-table">
                <el-table :data="home?.monitoring ?? []">
                  <el-table-column prop="device_name" :label="t('common.columns.deviceName')" min-width="180" />
                  <el-table-column prop="serial_number" :label="t('dashboard.monitoring.serial')" min-width="160" />
                  <el-table-column :label="t('common.status')" min-width="110">
                    <template #default="{ row }">
                      <StatusPill :value="row.device_status" :mapping="deviceStatusMeta" />
                    </template>
                  </el-table-column>
                  <el-table-column :label="t('dashboard.monitoring.onlineModules')" min-width="120">
                    <template #default="{ row }">
                      {{ row.online_module_count }}/{{ row.module_count }}
                    </template>
                  </el-table-column>
                  <el-table-column :label="t('dashboard.monitoring.latestAlarm')" min-width="140">
                    <template #default="{ row }">
                      {{ row.latest_alarm_type || '--' }}
                    </template>
                  </el-table-column>
                  <el-table-column :label="t('dashboard.monitoring.alarmTime')" min-width="180">
                    <template #default="{ row }">
                      {{ formatDateTime(row.latest_alarm_time) }}
                    </template>
                  </el-table-column>
                </el-table>
              </div>
            </DataState>
          </PanelCard>

          <PanelCard :title="t('dashboard.recentAlarms.title')" :description="t('dashboard.recentAlarms.description')">
            <DataState :empty="!recentAlarms.length" :empty-text="t('dashboard.recentAlarms.empty')">
              <div class="dashboard-stream">
                <article v-for="item in recentAlarms" :key="item.id" class="dashboard-stream__item">
                  <div class="dashboard-stream__main">
                    <strong>{{ item.device_name }} / {{ item.module_code }}</strong>
                    <p>{{ item.message || item.alarm_type }}</p>
                  </div>
                  <div class="dashboard-stream__meta">
                    <StatusPill :value="item.alarm_status" :mapping="alarmStatusMeta" />
                    <span>{{ formatDateTime(item.triggered_at) }}</span>
                  </div>
                </article>
              </div>
            </DataState>
          </PanelCard>

          <PanelCard :title="t('dashboard.recentCommands.title')" :description="t('dashboard.recentCommands.description')">
            <DataState :empty="!recentCommands.length" :empty-text="t('dashboard.recentCommands.empty')">
              <div class="dashboard-stream">
                <article v-for="item in recentCommands" :key="item.id" class="dashboard-stream__item">
                  <div class="dashboard-stream__main">
                    <strong>{{ item.device_name }} / {{ item.module_code }}</strong>
                    <p>{{ item.feedback_message || item.target_state }}</p>
                  </div>
                  <div class="dashboard-stream__meta">
                    <StatusPill :value="item.execution_status" :mapping="commandStatusMeta" />
                    <span>{{ formatDateTime(item.created_at) }}</span>
                  </div>
                </article>
              </div>
            </DataState>
          </PanelCard>
        </div>
      </template>
    </DataState>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'

import {
  getDashboardChartsApi,
  getDashboardHomeApi,
  getRecentAlarmsApi,
  getRecentCommandsApi,
} from '@/api/dashboard'
import DataState from '@/components/DataState.vue'
import DistributionChart from '@/components/DistributionChart.vue'
import MetricCard from '@/components/MetricCard.vue'
import ModuleOverviewCard from '@/components/ModuleOverviewCard.vue'
import PanelCard from '@/components/PanelCard.vue'
import StatusPill from '@/components/StatusPill.vue'
import { useI18n } from '@/composables/useI18n'
import { usePolling } from '@/composables/usePolling'
import { useAuthStore } from '@/stores/auth'
import type {
  DashboardAlarmItem,
  DashboardCharts,
  DashboardHome,
  DashboardRelayCommandItem,
} from '@/types/domain'
import { formatDateTime } from '@/utils/format'
import { alarmStatusMeta, commandStatusMeta, deviceStatusMeta } from '@/utils/status'

const { t } = useI18n()
const authStore = useAuthStore()
const loading = ref(true)
const error = ref('')
const home = ref<DashboardHome | null>(null)
const charts = ref<DashboardCharts | null>(null)
const recentAlarms = ref<DashboardAlarmItem[]>([])
const recentCommands = ref<DashboardRelayCommandItem[]>([])

const isManagerDashboard = computed(() => authStore.profile?.role === 'manager')
const modulePanels = computed(() => home.value?.module_panels ?? [])

async function refreshAll() {
  try {
    error.value = ''

    if (isManagerDashboard.value) {
      home.value = await getDashboardHomeApi()
      charts.value = null
      recentAlarms.value = []
      recentCommands.value = []
      return
    }

    const [homeData, chartData, alarmsData, commandsData] = await Promise.all([
      getDashboardHomeApi(),
      getDashboardChartsApi(),
      getRecentAlarmsApi(8),
      getRecentCommandsApi(8),
    ])
    home.value = homeData
    charts.value = chartData
    recentAlarms.value = alarmsData
    recentCommands.value = commandsData
  } catch (err: any) {
    error.value = err.response?.data?.detail || t('dashboard.loadError')
  } finally {
    loading.value = false
  }
}

const { start } = usePolling(refreshAll, 30000)

onMounted(async () => {
  await refreshAll()
  start()
})
</script>

<style scoped>
.dashboard-grid {
  display: grid;
  gap: 20px;
}

.dashboard-grid--metrics {
  grid-template-columns: repeat(4, minmax(0, 1fr));
}

.dashboard-grid--charts {
  grid-template-columns: repeat(3, minmax(0, 1fr));
}

.dashboard-grid--content {
  grid-template-columns: minmax(0, 1.3fr) minmax(320px, 0.7fr);
  align-items: start;
}

.module-panel-grid {
  display: grid;
  gap: 18px;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
}

.dashboard-polling-hint {
  color: var(--pal-text-muted);
  font-size: 0.84rem;
}

.dashboard-stream {
  display: grid;
  gap: 12px;
}

.dashboard-stream__item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 14px;
  padding: 14px 16px;
  border: 1px solid var(--pal-line);
  border-radius: var(--pal-radius-md);
  background: rgba(255, 255, 255, 0.02);
}

.dashboard-stream__main strong {
  display: block;
}

.dashboard-stream__main p {
  margin: 6px 0 0;
  color: var(--pal-text-muted);
}

.dashboard-stream__meta {
  display: grid;
  gap: 8px;
  justify-items: end;
  color: var(--pal-text-muted);
  font-size: 0.85rem;
}

@media (max-width: 1200px) {
  .dashboard-grid--charts,
  .dashboard-grid--metrics,
  .dashboard-grid--content {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (max-width: 768px) {
  .dashboard-grid--charts,
  .dashboard-grid--metrics,
  .dashboard-grid--content {
    grid-template-columns: 1fr;
  }

  .module-panel-grid {
    grid-template-columns: 1fr;
  }

  .dashboard-stream__item {
    flex-direction: column;
    align-items: flex-start;
  }

  .dashboard-stream__meta {
    justify-items: start;
  }
}
</style>
