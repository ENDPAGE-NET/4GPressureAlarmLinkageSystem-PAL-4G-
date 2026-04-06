<template>
  <view class="app-page">
    <view class="hero-panel">
      <text class="settings-title">设置</text>
      <text class="settings-desc">按照小程序常见方式，把安全、通知和会话管理集中到一个独立页面。</text>
    </view>

    <SectionCard title="账号与安全" subtitle="账号绑定和密码管理放在同一组，后续扩展也更稳。">
      <SettingsMenuItem
        title="微信账号绑定"
        :description="authStore.state.profile?.wechat_bound ? '当前微信已与账号绑定，可直接登录。' : '绑定后可直接用当前微信登录小程序。'"
        :value="bindingWechat ? '处理中' : authStore.state.profile?.wechat_bound ? '已绑定' : '未绑定'"
        clickable
        arrow
        @click="handleBindWechat"
      />
      <SettingsMenuItem
        title="修改密码"
        description="修改成功后会自动退出当前登录状态。"
        value="编辑"
        clickable
        arrow
        @click="togglePasswordEditor"
      />
    </SectionCard>

    <SectionCard title="消息通知" subtitle="通知能力独立归组，和账号安全分开维护。">
      <SettingsMenuItem
        title="报警消息订阅"
        :description="subscriptionDescription"
        :value="subscriptionStore.state.enabled ? '已授权' : '未授权'"
        clickable
        arrow
        @click="handleSubscriptionEntry"
      />
    </SectionCard>

    <SectionCard v-if="passwordEditorVisible" title="修改密码" subtitle="修改完成后会自动退出，需要重新登录。">
      <view class="form-field">
        <text class="form-label">当前密码</text>
        <input v-model="passwordForm.currentPassword" class="form-input" password placeholder="请输入当前密码" />
      </view>
      <view class="form-field">
        <text class="form-label">新密码</text>
        <input v-model="passwordForm.newPassword" class="form-input" password placeholder="请输入新密码" />
      </view>
      <view class="form-field">
        <text class="form-label">确认新密码</text>
        <input v-model="passwordForm.confirmPassword" class="form-input" password placeholder="请再次输入新密码" />
      </view>
      <button class="primary-button settings-action" :loading="submittingPassword" @click="handleChangePassword">
        确认修改密码
      </button>
    </SectionCard>

    <SectionCard title="会话管理" subtitle="敏感会话操作单独放在底部，降低误触概率。">
      <SettingsMenuItem
        title="安全退出"
        description="退出后需要重新输入账号密码或重新使用微信登录。"
        value="退出"
        clickable
        arrow
        danger
        @click="handleLogout"
      />
    </SectionCard>
  </view>
</template>

<script setup>
import { computed, reactive, ref } from 'vue'
import { onShow } from '@dcloudio/uni-app'

import SectionCard from '@/components/SectionCard.vue'
import SettingsMenuItem from '@/components/SettingsMenuItem.vue'
import { wechatBindApi } from '@/api/auth'
import { changePasswordApi } from '@/api/users'
import { useAuthStore } from '@/stores/auth'
import { showRequestError } from '@/utils/errors'
import { formatDateTime } from '@/utils/format'
import { ensureAuthenticated } from '@/utils/guards'
import { useSubscriptionStore } from '@/utils/subscription'
import { requestWechatLoginCode } from '@/utils/wechat'

const authStore = useAuthStore()
const subscriptionStore = useSubscriptionStore()

const bindingWechat = ref(false)
const submittingPassword = ref(false)
const passwordEditorVisible = ref(false)
const passwordForm = reactive({
  currentPassword: '',
  newPassword: '',
  confirmPassword: '',
})

const templateIdText = computed(() => {
  const templateIds = subscriptionStore.state.availableTemplateIds?.length
    ? subscriptionStore.state.availableTemplateIds
    : subscriptionStore.state.templateIds

  if (!templateIds?.length) {
    return '尚未同步到模板编号'
  }
  return templateIds.join('、')
})

const subscriptionDescription = computed(() => {
  if (subscriptionStore.state.enabled) {
    return `已授权，最近更新时间 ${formatDateTime(subscriptionStore.state.updatedAt, '刚刚')}`
  }

  if (templateIdText.value === '尚未同步到模板编号') {
    return '当前没有可用模板编号，请先由后端或管理员补充配置。'
  }

  return `当前可用模板：${templateIdText.value}`
})

onShow(() => {
  void initSettings()
})

async function initSettings() {
  if (!(await ensureAuthenticated())) {
    return
  }

  try {
    await subscriptionStore.syncStatus()
  } catch (error) {
    showRequestError(error, '订阅状态同步失败')
  }
}

async function handleBindWechat() {
  if (!(await ensureAuthenticated())) {
    return
  }

  if (bindingWechat.value) {
    return
  }

  bindingWechat.value = true
  try {
    const code = await requestWechatLoginCode()
    await wechatBindApi({ code })
    await authStore.fetchProfile()
    uni.showToast({
      title: '微信绑定成功',
      icon: 'success',
    })
  } catch (error) {
    showRequestError(error, '微信绑定失败')
  } finally {
    bindingWechat.value = false
  }
}

function togglePasswordEditor() {
  passwordEditorVisible.value = !passwordEditorVisible.value
}

async function handleSubscriptionEntry() {
  if (subscriptionStore.state.enabled) {
    uni.showActionSheet({
      itemList: ['重新申请授权', '停止订阅'],
      success: async (result) => {
        if (result.tapIndex === 0) {
          await handleSubscribe()
          return
        }

        if (result.tapIndex === 1) {
          await handleUnsubscribe()
        }
      },
    })
    return
  }

  await handleSubscribe()
}

async function handleSubscribe() {
  try {
    const granted = await subscriptionStore.requestAlarmSubscription()
    uni.showToast({
      title: granted ? '授权成功' : '你已拒绝授权',
      icon: 'none',
    })
  } catch (error) {
    showRequestError(error, '订阅授权失败')
  }
}

async function handleUnsubscribe() {
  try {
    await subscriptionStore.disableAlarmSubscription()
    uni.showToast({
      title: '已关闭报警订阅',
      icon: 'none',
    })
  } catch (error) {
    showRequestError(error, '关闭订阅失败')
  }
}

async function handleChangePassword() {
  if (!(await ensureAuthenticated())) {
    return
  }

  if (!passwordForm.currentPassword || !passwordForm.newPassword || !passwordForm.confirmPassword) {
    uni.showToast({
      title: '请完整填写密码信息',
      icon: 'none',
    })
    return
  }

  if (passwordForm.newPassword.length < 8) {
    uni.showToast({
      title: '新密码至少 8 位',
      icon: 'none',
    })
    return
  }

  if (passwordForm.newPassword !== passwordForm.confirmPassword) {
    uni.showToast({
      title: '两次输入的新密码不一致',
      icon: 'none',
    })
    return
  }

  submittingPassword.value = true
  try {
    await changePasswordApi({
      current_password: passwordForm.currentPassword,
      new_password: passwordForm.newPassword,
    })
    uni.showToast({
      title: '密码已更新，请重新登录',
      icon: 'none',
    })
    authStore.logout(false)
    uni.reLaunch({
      url: '/pages/login/index',
    })
  } catch (error) {
    showRequestError(error, '修改密码失败')
  } finally {
    submittingPassword.value = false
  }
}

function handleLogout() {
  uni.showModal({
    title: '确认退出登录',
    content: '退出后需要重新登录，是否继续？',
    success: (result) => {
      if (!result.confirm) {
        return
      }

      authStore.logout(false)
      uni.reLaunch({
        url: '/pages/login/index',
      })
    },
  })
}
</script>

<style scoped>
.settings-title {
  display: block;
  font-size: 42rpx;
  font-weight: 700;
}

.settings-desc {
  display: block;
  margin-top: 18rpx;
  font-size: 24rpx;
  line-height: 1.7;
  opacity: 0.92;
}

.settings-action {
  margin-top: 12rpx;
}
</style>
