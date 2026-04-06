<template>
  <view class="app-page app-page--docked">
    <view class="hero-panel">
      <text class="home-hero__eyebrow">PAL 4G 移动工作台</text>
      <text class="home-hero__title">你好，{{ profileName }}</text>
      <text class="home-hero__desc">
        首页现在只保留总览和重点提醒，设备、报警、账号管理分别放到独立页面里处理。
      </text>
      <view class="home-hero__meta">
        <text class="status-tag" :class="realtimeStatusClass">{{ realtimeStatusLabel }}</text>
        <text class="home-hero__meta-text">最近刷新：{{ lastRefreshText }}</text>
      </view>
    </view>

    <view v-if="loading" class="panel-card">
      <text class="text-muted">正在加载首页数据...</text>
    </view>

    <template v-else>
      <view class="summary-grid">
        <SummaryStatCard label="设备总数" :value="summary.device_count" hint="当前账号可见设备" accent="blue" />
        <SummaryStatCard label="在线设备" :value="summary.online_device_count" hint="实时在线设备数" accent="green" />
        <SummaryStatCard label="当前报警" :value="summary.triggered_alarm_count" hint="需要关注的报警事件" accent="red" />
        <SummaryStatCard label="待处理指令" :value="summary.pending_command_count" hint="排队或执行中的命令" accent="orange" />
      </view>

      <SectionCard title="今日关注" subtitle="把当前最重要的状态放在首页，其余信息进入各自页面查看。">
        <view class="focus-list">
          <view class="focus-item">
            <view>
              <text class="focus-item__label">实时链路</text>
              <text class="focus-item__desc">设备详情会优先走实时更新，异常时自动回退到轮询刷新。</text>
            </view>
            <text class="status-tag" :class="realtimeStatusClass">{{ realtimeStatusLabel }}</text>
          </view>

          <view class="focus-item">
            <view>
              <text class="focus-item__label">报警消息</text>
              <text class="focus-item__desc">{{ subscriptionDescription }}</text>
            </view>
            <text class="status-tag" :class="subscriptionStatusClass">{{ subscriptionTitle }}</text>
          </view>
        </view>
      </SectionCard>

      <SectionCard title="最近报警" subtitle="首页只预览最近两条，完整列表到报警页查看。">
        <template v-if="recentAlarms.length">
          <view v-for="item in recentAlarmPreview" :key="item.id" class="alarm-item">
            <view class="alarm-item__head">
              <text class="alarm-item__device">{{ item.device_name }}</text>
              <text class="status-tag status-alarm">{{ getAlarmTypeLabel(item.alarm_type) }}</text>
            </view>
            <text class="alarm-item__message">{{ item.message || '设备上报了新的报警事件。' }}</text>
            <text class="alarm-item__time">{{ formatDateTime(item.triggered_at) }}</text>
          </view>
          <button class="secondary-button recent-action" @click="goPrimary('/pages/alarms/index')">查看全部报警</button>
        </template>
        <EmptyState
          v-else
          title="暂时没有报警"
          description="当设备触发低电量、电压异常或其他报警时，这里会优先显示。"
          action-text="查看全部报警"
          @action="goPrimary('/pages/alarms/index')"
        />
      </SectionCard>
    </template>

    <PrimaryDock active="home" />
  </view>
</template>

<script setup>
import { computed, onUnmounted, ref } from 'vue'
import { onHide, onPullDownRefresh, onShow } from '@dcloudio/uni-app'

import EmptyState from '@/components/EmptyState.vue'
import PrimaryDock from '@/components/PrimaryDock.vue'
import SectionCard from '@/components/SectionCard.vue'
import SummaryStatCard from '@/components/SummaryStatCard.vue'
import { getMiniHomeApi, getMyRecentAlarmsApi } from '@/api/dashboard'
import { useRealtime } from '@/composables/useRealtime'
import { useAuthStore } from '@/stores/auth'
import { APP_CONFIG } from '@/utils/config'
import { showRequestError } from '@/utils/errors'
import { formatDateTime } from '@/utils/format'
import { ensureAuthenticated } from '@/utils/guards'
import { getAlarmTypeLabel } from '@/utils/status'
import { useSubscriptionStore } from '@/utils/subscription'

const authStore = useAuthStore()
const subscriptionStore = useSubscriptionStore()
const realtime = useRealtime()

const loading = ref(false)
const summary = ref({
  device_count: 0,
  online_device_count: 0,
  triggered_alarm_count: 0,
  pending_command_count: 0,
})
const recentAlarms = ref([])
const lastRefreshAt = ref('')

let stopRealtime = null
let pollingTimer = null

const profileName = computed(() => authStore.state.profile?.username || '设备账号')
const lastRefreshText = computed(() => formatDateTime(lastRefreshAt.value, '等待同步'))

const realtimeStatusLabel = computed(() => {
  switch (realtime.state.status) {
    case 'connected':
      return '实时已连接'
    case 'connecting':
      return '实时连接中'
    case 'error':
      return '实时异常'
    default:
      return '轮询模式'
  }
})

const realtimeStatusClass = computed(() => {
  switch (realtime.state.status) {
    case 'connected':
      return 'status-online'
    case 'connecting':
      return 'status-pending'
    case 'error':
      return 'status-alarm'
    default:
      return 'status-info'
  }
})

const subscriptionTitle = computed(() =>
  subscriptionStore.state.enabled ? '已授权' : '待授权',
)

const subscriptionDescription = computed(() => {
  const availableTemplateIds = subscriptionStore.state.availableTemplateIds?.length
    ? subscriptionStore.state.availableTemplateIds
    : APP_CONFIG.SUBSCRIPTION_TEMPLATE_IDS

  return subscriptionStore.state.enabled
    ? `最近授权时间：${formatDateTime(subscriptionStore.state.updatedAt, '刚刚')}`
    : availableTemplateIds.length
      ? '完成授权后，报警推送会按后端模板配置自动派发到当前微信。'
      : '当前小程序尚未配置订阅模板，请联系管理员补充模板编号后再授权。'
})

const subscriptionStatusClass = computed(() =>
  subscriptionStore.state.enabled ? 'status-online' : 'status-pending',
)

const recentAlarmPreview = computed(() => recentAlarms.value.slice(0, 2))

async function loadData(showLoading = true) {
  if (!(await ensureAuthenticated())) {
    return
  }

  if (showLoading) {
    loading.value = true
  }

  try {
    const [homeData, alarmData] = await Promise.all([
      getMiniHomeApi(),
      getMyRecentAlarmsApi(5),
    ])
    summary.value = homeData
    recentAlarms.value = alarmData
    lastRefreshAt.value = new Date().toISOString()
  } catch (error) {
    showRequestError(error, '首页数据加载失败')
  } finally {
    loading.value = false
    uni.stopPullDownRefresh()
  }
}

function goPrimary(url) {
  uni.switchTab?.({
    url,
    fail: () => {
      uni.reLaunch({ url })
    },
  })
}

function startPolling() {
  stopPolling()
  pollingTimer = setInterval(() => {
    void loadData(false)
  }, APP_CONFIG.POLLING_INTERVAL)
}

function stopPolling() {
  if (pollingTimer) {
    clearInterval(pollingTimer)
    pollingTimer = null
  }
}

onShow(() => {
  void loadData()
  void subscriptionStore.syncStatus().catch(() => {})
  if (!stopRealtime) {
    stopRealtime = realtime.subscribe((message) => {
      if (
        ['alarm.created', 'alarm.recovered', 'module.status_updated', 'relay_command.created', 'relay_command.updated'].includes(
          message?.event,
        )
      ) {
        void loadData(false)
      }
    })
  }
  startPolling()
})

onPullDownRefresh(() => {
  void loadData(false)
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
.home-hero__eyebrow,
.home-hero__desc,
.home-hero__meta-text,
.focus-item__label,
.focus-item__desc,
.quick-tile__title,
.quick-tile__desc {
  display: block;
}

.home-hero__eyebrow {
  font-size: 24rpx;
  letter-spacing: 3rpx;
  opacity: 0.82;
}

.home-hero__title {
  display: block;
  margin-top: 12rpx;
  font-size: 42rpx;
  font-weight: 700;
}

.home-hero__desc {
  margin-top: 18rpx;
  font-size: 24rpx;
  line-height: 1.7;
  opacity: 0.92;
}

.home-hero__meta {
  display: flex;
  align-items: center;
  gap: 16rpx;
  margin-top: 24rpx;
  flex-wrap: wrap;
}

.home-hero__meta-text {
  font-size: 22rpx;
  opacity: 0.88;
}

.summary-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 18rpx;
}

.focus-list {
  display: grid;
  gap: 18rpx;
}

.focus-item {
  display: grid;
  gap: 16rpx;
  padding: 22rpx;
  border-radius: 24rpx;
  background: rgba(18, 83, 143, 0.04);
}

.focus-item__label {
  font-size: 28rpx;
  font-weight: 700;
  color: #17324d;
}

.focus-item__desc {
  margin-top: 10rpx;
  font-size: 22rpx;
  line-height: 1.7;
  color: #6e84a2;
}

.alarm-item {
  padding: 20rpx 0;
  border-top: 1rpx solid rgba(25, 82, 144, 0.08);
}

.alarm-item:first-child {
  padding-top: 0;
  border-top: 0;
}

.alarm-item__head {
  display: flex;
  flex-direction: column;
  gap: 18rpx;
}

.alarm-item__device {
  font-size: 26rpx;
  font-weight: 700;
  line-height: 1.5;
  color: #17324d;
}

.alarm-item__message {
  display: block;
  margin-top: 12rpx;
  font-size: 22rpx;
  line-height: 1.6;
  color: #6c84a2;
}

.alarm-item__time {
  display: block;
  margin-top: 10rpx;
  font-size: 22rpx;
  color: #8aa0b8;
}

.recent-action {
  margin-top: 18rpx;
}
</style>
