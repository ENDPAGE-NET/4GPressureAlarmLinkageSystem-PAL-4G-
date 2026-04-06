<template>
  <view class="app-page app-page--docked">
    <view class="hero-panel profile-hero">
      <button class="profile-settings-trigger" @click="openSettings">
        <text class="profile-settings-trigger__icon">⚙</text>
      </button>

      <view class="profile-hero__identity">
        <view class="profile-avatar">{{ profileInitials }}</view>
        <view class="profile-hero__copy">
          <text class="profile-name">{{ authStore.state.profile?.username || '--' }}</text>
          <text class="profile-role">{{ formatRole(authStore.state.profile?.role) }}</text>
        </view>
      </view>

      <text class="profile-desc">常用账号信息放在这里，通知、安全和退出登录统一收口到设置页。</text>
    </view>

    <SectionCard title="账号概览" subtitle="保留高频信息，减少“我的”页里的操作噪音。">
      <SettingsMenuItem title="用户 ID" :value="String(authStore.state.profile?.id || '--')" />
      <SettingsMenuItem title="账号角色" :value="formatRole(authStore.state.profile?.role)" />
      <SettingsMenuItem title="登录状态" :value="authStore.state.profile?.is_active ? '正常' : '已停用'" />
      <SettingsMenuItem title="微信绑定" :value="authStore.state.profile?.wechat_bound ? '已绑定' : '未绑定'" />
      <SettingsMenuItem title="实时连接" :value="realtimeLabel" />
    </SectionCard>

    <SectionCard title="快捷入口" subtitle="设置页集中处理账号安全、通知和会话管理。">
      <SettingsMenuItem
        title="打开设置"
        description="进入设置页后可以管理微信绑定、报警订阅、修改密码和安全退出。"
        value="进入"
        clickable
        arrow
        @click="openSettings"
      />
    </SectionCard>

    <PrimaryDock active="profile" />
  </view>
</template>

<script setup>
import { computed } from 'vue'
import { onShow } from '@dcloudio/uni-app'

import PrimaryDock from '@/components/PrimaryDock.vue'
import SectionCard from '@/components/SectionCard.vue'
import SettingsMenuItem from '@/components/SettingsMenuItem.vue'
import { useRealtime } from '@/composables/useRealtime'
import { useAuthStore } from '@/stores/auth'
import { formatRole } from '@/utils/format'
import { ensureAuthenticated } from '@/utils/guards'

const authStore = useAuthStore()
const realtime = useRealtime()

const profileInitials = computed(() => {
  const username = String(authStore.state.profile?.username || '').trim()
  return username ? username.slice(0, 2).toUpperCase() : 'ME'
})

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
.profile-hero {
  position: relative;
}

.profile-settings-trigger {
  position: absolute;
  top: 18rpx;
  right: 18rpx;
  width: 76rpx;
  min-height: 76rpx;
  padding: 0;
  border-radius: 999rpx;
  border: 1rpx solid rgba(255, 255, 255, 0.28);
  background: rgba(255, 255, 255, 0.14);
  display: flex;
  align-items: center;
  justify-content: center;
}

.profile-settings-trigger::after {
  border: 0;
}

.profile-settings-trigger__icon {
  font-size: 34rpx;
  line-height: 1;
  color: #fff;
}

.profile-hero__identity {
  display: flex;
  align-items: center;
  gap: 18rpx;
  padding-right: 88rpx;
}

.profile-avatar {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 88rpx;
  height: 88rpx;
  border-radius: 28rpx;
  background: rgba(255, 255, 255, 0.16);
  font-size: 30rpx;
  font-weight: 700;
  letter-spacing: 2rpx;
}

.profile-hero__copy {
  min-width: 0;
  flex: 1;
}

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
</style>
