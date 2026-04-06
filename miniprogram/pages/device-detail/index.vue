<template>
  <view class="app-page">
    <view class="hero-panel">
      <text class="detail-title">{{ device?.name || dashboard?.device_name || '设备详情' }}</text>
      <text class="detail-serial">SN：{{ device?.serial_number || dashboard?.serial_number || '--' }}</text>
      <view class="detail-meta">
        <text class="status-tag" :class="dashboard?.device_status === 'active' ? 'status-online' : 'status-offline'">
          {{ getDeviceStatusLabel(dashboard?.device_status || device?.status) }}
        </text>
        <text class="detail-meta__text">运行通道 {{ runtimeModules.length ? '已就绪' : '未就绪' }}</text>
        <text class="detail-meta__text">最近在线 {{ formatDateTime(runtimeModules[0]?.last_seen_at, '--') }}</text>
      </view>
    </view>

    <view v-if="loading" class="panel-card">
      <text class="text-muted">正在同步设备详情...</text>
    </view>

    <template v-else-if="device && dashboard">
      <SectionCard title="设备操作" subtitle="支持远程控制，也支持从当前账号中移除该设备。">
        <view class="detail-actions">
          <button class="secondary-button" @click="refreshDetail">刷新状态</button>
          <button class="danger-button" :loading="unbinding" @click="handleUnbind">移除设备</button>
        </view>
      </SectionCard>

      <SectionCard title="设备状态" subtitle="页面会优先使用实时事件更新，异常时自动回退到轮询。">
        <template v-if="runtimeModules.length">
          <view class="module-list">
            <ModuleCard
              v-for="item in runtimeModules"
              :key="item.id"
              :module="item"
              :loading="submittingModuleId === item.id"
              :target-state="targetState"
              @toggle="handleToggleRelay"
            />
          </view>
        </template>
        <EmptyState
          v-else
          title="当前设备暂无可用运行状态"
          description="设备运行通道未就绪时，暂时无法在小程序中查看状态或控制继电器。"
        />
      </SectionCard>

      <SectionCard title="最近报警" subtitle="最近发生的报警会优先显示在这里。">
        <template v-if="dashboard.recent_alarms?.length">
          <view v-for="item in dashboard.recent_alarms" :key="item.id" class="detail-list-item">
            <view class="detail-list-item__head">
              <text class="detail-list-item__title">{{ dashboard.device_name || device.name }}</text>
              <text class="status-tag status-alarm">{{ getAlarmTypeLabel(item.alarm_type) }}</text>
            </view>
            <text class="detail-list-item__desc">{{ item.message || '设备上报了新的报警事件。' }}</text>
            <text class="detail-list-item__time">{{ formatDateTime(item.triggered_at) }}</text>
          </view>
        </template>
        <EmptyState
          v-else
          title="暂无报警记录"
          description="当当前设备触发报警时，这里会展示最近的记录和联动结果。"
        />
      </SectionCard>

      <SectionCard title="最近控制记录" subtitle="手动控制与报警联动指令都会显示在这里。">
        <template v-if="dashboard.recent_commands?.length">
          <view v-for="item in dashboard.recent_commands" :key="item.id" class="detail-list-item">
            <view class="detail-list-item__head">
              <text class="detail-list-item__title">{{ dashboard.device_name || device.name }}</text>
              <text class="status-tag" :class="getCommandStatusClass(item.execution_status)">
                {{ getCommandStatusLabel(item.execution_status) }}
              </text>
            </view>
            <text class="detail-list-item__desc">
              目标状态：{{ getRelayTargetLabel(item.target_state) }} / 来源：{{ item.command_source || '--' }}
            </text>
            <text class="detail-list-item__time">{{ formatDateTime(item.created_at) }}</text>
          </view>
        </template>
        <EmptyState
          v-else
          title="暂无控制记录"
          description="你在小程序中的远程控制，或服务端触发的联动命令，都会在这里展示。"
        />
      </SectionCard>
    </template>
  </view>
</template>

<script setup>
import { onUnmounted, ref } from 'vue'
import { onHide, onLoad, onPullDownRefresh, onShow } from '@dcloudio/uni-app'

import EmptyState from '@/components/EmptyState.vue'
import ModuleCard from '@/components/ModuleCard.vue'
import SectionCard from '@/components/SectionCard.vue'
import { getDeviceDashboardDetailApi } from '@/api/dashboard'
import { getDeviceRuntimeApi, unbindDeviceApi } from '@/api/devices'
import { createRelayCommandApi } from '@/api/relay'
import { useRealtime } from '@/composables/useRealtime'
import { APP_CONFIG } from '@/utils/config'
import { showRequestError } from '@/utils/errors'
import { formatDateTime } from '@/utils/format'
import { ensureAuthenticated } from '@/utils/guards'
import {
  getAlarmTypeLabel,
  getCommandStatusClass,
  getCommandStatusLabel,
  getDeviceStatusLabel,
  getRelayTargetLabel,
} from '@/utils/status'

const realtime = useRealtime()

const deviceId = ref(0)
const loading = ref(false)
const unbinding = ref(false)
const submittingModuleId = ref(0)
const targetState = ref('')
const device = ref(null)
const dashboard = ref(null)
const runtimeModules = ref([])

let stopRealtime = null
let pollingTimer = null

async function loadDetail(showLoading = true) {
  if (!deviceId.value || !(await ensureAuthenticated())) {
    return
  }

  if (showLoading) {
    loading.value = true
  }

  try {
    const [deviceData, dashboardData] = await Promise.all([
      getDeviceRuntimeApi(deviceId.value),
      getDeviceDashboardDetailApi(deviceId.value),
    ])
    device.value = deviceData
    dashboard.value = dashboardData
    runtimeModules.value = Array.isArray(deviceData?.modules) ? deviceData.modules : []
  } catch (error) {
    showRequestError(error, '设备详情加载失败')
  } finally {
    loading.value = false
    uni.stopPullDownRefresh()
  }
}

function refreshDetail() {
  void loadDetail()
}

function startPolling() {
  stopPolling()
  pollingTimer = setInterval(() => {
    void loadDetail(false)
  }, APP_CONFIG.POLLING_INTERVAL)
}

function stopPolling() {
  if (pollingTimer) {
    clearInterval(pollingTimer)
    pollingTimer = null
  }
}

function handleToggleRelay(payload) {
  const runtime = payload.module
  targetState.value = payload.targetState
  uni.showModal({
    title: payload.targetState === 'closed' ? '确认闭合继电器' : '确认断开继电器',
    content: `是否对当前设备执行${payload.targetState === 'closed' ? '闭合' : '断开'}继电器操作？`,
    success: async (result) => {
      if (!result.confirm) {
        return
      }

      submittingModuleId.value = runtime.id
      try {
        await createRelayCommandApi({
          module_id: runtime.id,
          target_state: payload.targetState,
          command_source: 'miniprogram_manual',
        })
        uni.showToast({
          title: '控制指令已提交',
          icon: 'success',
        })
        await loadDetail(false)
      } catch (error) {
        showRequestError(error, '继电器控制失败')
      } finally {
        submittingModuleId.value = 0
        targetState.value = ''
      }
    },
  })
}

function handleUnbind() {
  uni.showModal({
    title: '确认移除设备',
    content: '移除后该设备将不会再出现在当前账号的小程序列表中，是否继续？',
    success: async (result) => {
      if (!result.confirm) {
        return
      }

      unbinding.value = true
      try {
        await unbindDeviceApi(deviceId.value)
        uni.showToast({
          title: '设备已移除',
          icon: 'success',
        })
        uni.reLaunch({
          url: '/pages/devices/index',
        })
      } catch (error) {
        showRequestError(error, '移除设备失败')
      } finally {
        unbinding.value = false
      }
    },
  })
}

onLoad((options) => {
  deviceId.value = Number(options?.deviceId || 0)
})

onShow(() => {
  void loadDetail()
  if (!stopRealtime) {
    stopRealtime = realtime.subscribe((message) => {
      if (
        ['alarm.created', 'alarm.recovered', 'module.status_updated', 'relay_command.created', 'relay_command.updated'].includes(
          message?.event,
        )
      ) {
        const relatedDeviceId = Number(message?.data?.device_id || 0)
        if (!relatedDeviceId || relatedDeviceId === deviceId.value) {
          void loadDetail(false)
        }
      }
    })
  }
  startPolling()
})

onPullDownRefresh(() => {
  void loadDetail(false)
})

onHide(() => {
  stopPolling()
})

onUnmounted(() => {
  if (stopRealtime) {
    stopRealtime()
    stopRealtime = null
  }
  stopPolling()
})
</script>

<style scoped>
.detail-title {
  display: block;
  font-size: 40rpx;
  font-weight: 700;
  line-height: 1.35;
}

.detail-serial {
  display: block;
  margin-top: 12rpx;
  font-size: 24rpx;
  line-height: 1.6;
  opacity: 0.92;
}

.detail-meta {
  display: flex;
  gap: 16rpx;
  flex-wrap: wrap;
  margin-top: 22rpx;
}

.detail-meta__text {
  font-size: 22rpx;
  line-height: 1.5;
  opacity: 0.9;
}

.detail-actions {
  display: grid;
  gap: 16rpx;
}

.detail-actions button {
  width: 100%;
}

.module-list {
  display: grid;
  gap: 18rpx;
}

.detail-list-item {
  padding: 20rpx 0;
  border-top: 1rpx solid rgba(25, 82, 144, 0.08);
}

.detail-list-item:first-child {
  padding-top: 0;
  border-top: 0;
}

.detail-list-item__head {
  display: flex;
  flex-direction: column;
  gap: 16rpx;
}

.detail-list-item__title {
  font-size: 26rpx;
  font-weight: 700;
  line-height: 1.45;
  color: #17324d;
}

.detail-list-item__desc {
  display: block;
  margin-top: 12rpx;
  font-size: 22rpx;
  line-height: 1.6;
  color: #6d84a1;
}

.detail-list-item__time {
  display: block;
  margin-top: 10rpx;
  font-size: 22rpx;
  color: #8da3b8;
}
</style>
