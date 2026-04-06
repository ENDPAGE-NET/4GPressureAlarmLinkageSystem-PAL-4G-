<template>
  <view class="app-page app-page--docked">
    <view class="hero-panel">
      <text class="profile-name">{{ authStore.state.profile?.username || '--' }}</text>
      <text class="profile-role">{{ formatRole(authStore.state.profile?.role) }}</text>
      <text class="profile-desc">账号状态和消息授权保留在这里，安全设置进入独立设置页统一管理。</text>
    </view>

    <SectionCard title="账号信息" subtitle="当前小程序仅面向普通设备账号提供业务能力。">
      <view class="profile-info">
        <view class="profile-info__row">
          <text class="profile-info__label">用户 ID</text>
          <text class="profile-info__value">{{ authStore.state.profile?.id || '--' }}</text>
        </view>
        <view class="profile-info__row">
          <text class="profile-info__label">账号角色</text>
          <text class="profile-info__value">{{ formatRole(authStore.state.profile?.role) }}</text>
        </view>
        <view class="profile-info__row">
          <text class="profile-info__label">登录状态</text>
          <text class="profile-info__value">{{ authStore.state.profile?.is_active ? '正常' : '已停用' }}</text>
        </view>
        <view class="profile-info__row">
          <text class="profile-info__label">微信绑定</text>
          <text class="profile-info__value">{{ authStore.state.profile?.wechat_bound ? '已绑定' : '未绑定' }}</text>
        </view>
        <view class="profile-info__row">
          <text class="profile-info__label">实时连接</text>
          <text class="profile-info__value">{{ realtimeLabel }}</text>
        </view>
      </view>
    </SectionCard>

    <SectionCard title="设置" subtitle="微信绑定、消息订阅、修改密码和退出登录已收纳到设置页，避免“我的”页过长。">
      <button class="primary-button profile-action" @click="openSettings">进入设置</button>
    </SectionCard>

    <PrimaryDock active="profile" />
  </view>
</template>

<script setup>
import { computed } from 'vue'
import { onShow } from '@dcloudio/uni-app'

import PrimaryDock from '@/components/PrimaryDock.vue'
import SectionCard from '@/components/SectionCard.vue'
import { useRealtime } from '@/composables/useRealtime'
import { useAuthStore } from '@/stores/auth'
import { formatRole } from '@/utils/format'
import { ensureAuthenticated } from '@/utils/guards'

const authStore = useAuthStore()
const realtime = useRealtime()

const realtimeLabel = computed(() => {
  switch (realtime.state.status) {
    case 'connected':
      return '已连接'
    case 'connecting':
      return '连接中'
    case 'error':
      return '异常'
    default:
      return '轮询模式'
  }
})

onShow(() => {
  void ensureAuthenticated()
})

function openSettings() {
  uni.navigateTo({
    url: '/pages/settings/index',
  })
}
</script>

<style scoped>
.profile-name {
  display: block;
  font-size: 42rpx;
  font-weight: 700;
}

.profile-role,
.profile-desc {
  display: block;
}

.profile-role {
  margin-top: 12rpx;
  font-size: 24rpx;
  opacity: 0.92;
}

.profile-desc {
  margin-top: 18rpx;
  font-size: 24rpx;
  line-height: 1.7;
  opacity: 0.92;
}

.profile-info {
  display: grid;
  gap: 18rpx;
}

.profile-info__row {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: 20rpx;
  padding: 18rpx 0;
  border-top: 1rpx solid rgba(22, 83, 143, 0.08);
}

.profile-info__row:first-child {
  padding-top: 0;
  border-top: 0;
}

.profile-info__row--compact {
  gap: 12rpx;
}

.profile-info__label {
  font-size: 24rpx;
  color: #6f87a4;
}

.profile-info__value {
  font-size: 24rpx;
  line-height: 1.5;
  color: #17324d;
  font-weight: 600;
}

.profile-action {
  margin-top: 12rpx;
}
</style>
