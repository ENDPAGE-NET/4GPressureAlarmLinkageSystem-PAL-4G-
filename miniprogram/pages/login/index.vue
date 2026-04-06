<template>
  <view class="app-page login-page">
    <view class="hero-panel login-hero">
      <text class="login-hero__eyebrow">PAL_4G 移动控制台</text>
      <text class="login-hero__title">4G 压力报警联动系统</text>
      <text class="login-hero__desc">
        使用设备账号直接登录，快速查看设备状态、接收报警并进行远程控制。
      </text>
    </view>

    <view class="panel-card login-form">
      <view v-if="wechatBindMode" class="login-bind-notice">
        <text class="login-bind-notice__title">当前微信尚未绑定账号</text>
        <text class="login-bind-notice__desc">
          请输入已有设备账号和密码，登录成功后系统会自动把当前微信绑定到该账号。
        </text>
        <button class="secondary-button login-bind-cancel" @click="cancelWechatBindMode">取消本次绑定</button>
      </view>

      <view class="form-field">
        <text class="form-label">账号</text>
        <input
          v-model.trim="form.username"
          class="form-input"
          placeholder="请输入账号"
          confirm-type="next"
        />
      </view>

      <view class="form-field">
        <text class="form-label">密码</text>
        <input
          v-model="form.password"
          class="form-input"
          password
          placeholder="请输入密码"
          confirm-type="done"
          @confirm="handleLogin"
        />
      </view>

      <button class="primary-button login-submit" :loading="authStore.state.loading" @click="handleLogin">
        {{ wechatBindMode ? '登录并绑定微信' : '登录并进入控制中心' }}
      </button>

      <button class="secondary-button login-wechat" :loading="wechatLoading" @click="handleWechatLogin">
        {{ wechatBindMode ? '重新获取微信授权' : '微信授权登录' }}
      </button>

      <view class="login-tips">
        <text class="login-tips__title">当前版本说明</text>
        <text class="login-tips__item">1. 账号密码登录已可直接联调后端。</text>
        <text class="login-tips__item">2. 微信授权登录已接通，未绑定账号时可在本页直接完成绑定。</text>
        <text class="login-tips__item">3. 订阅模板会优先读取后端配置，前端本地配置仅作为开发兜底。</text>
      </view>
    </view>
  </view>
</template>

<script setup>
import { reactive, ref } from 'vue'
import { onShow } from '@dcloudio/uni-app'

import { wechatBindApi } from '@/api/auth'
import { useAuthStore } from '@/stores/auth'
import { showRequestError } from '@/utils/errors'
import { requestWechatLoginCode } from '@/utils/wechat'

const authStore = useAuthStore()
const form = reactive({
  username: '',
  password: '',
})
const wechatBindMode = ref(false)
const wechatLoading = ref(false)

async function redirectIfLoggedIn() {
  await authStore.initialize()
  if (authStore.isAuthenticated.value) {
    uni.reLaunch({
      url: '/pages/home/index',
    })
  }
}

async function bindCurrentWechatAfterLogin() {
  const code = await requestWechatLoginCode()
  await wechatBindApi({ code })
  await authStore.fetchProfile()
}

async function handleLogin() {
  if (!form.username || !form.password) {
    uni.showToast({
      title: '请输入账号和密码',
      icon: 'none',
    })
    return
  }

  try {
    await authStore.login(form.username, form.password)
    if (wechatBindMode.value) {
      try {
        await bindCurrentWechatAfterLogin()
        wechatBindMode.value = false
        uni.showToast({
          title: '微信绑定成功，已完成登录',
          icon: 'success',
        })
      } catch (error) {
        showRequestError(error, '账号已登录，但微信绑定失败，请稍后在设置页重新绑定')
      }
    } else {
      uni.showToast({
        title: '登录成功',
        icon: 'success',
      })
    }

    uni.reLaunch({
      url: '/pages/home/index',
    })
  } catch (error) {
    showRequestError(error, '登录失败，请检查账号密码')
  }
}

async function handleWechatLogin() {
  wechatLoading.value = true
  try {
    const code = await requestWechatLoginCode()
    await authStore.loginWithWechat({ code })
    wechatBindMode.value = false
    uni.showToast({
      title: '微信登录成功',
      icon: 'success',
    })
    uni.reLaunch({
      url: '/pages/home/index',
    })
  } catch (error) {
    if (Number(error?.statusCode || 0) === 404) {
      wechatBindMode.value = true
      uni.showModal({
        title: '微信未绑定账号',
        content: '请继续输入已有设备账号和密码，登录成功后会自动完成微信绑定。',
        showCancel: false,
      })
      return
    }

    showRequestError(error, '微信登录失败，请稍后重试')
  } finally {
    wechatLoading.value = false
  }
}

function cancelWechatBindMode() {
  wechatBindMode.value = false
}

onShow(() => {
  void redirectIfLoggedIn()
})
</script>

<style scoped>
.login-page {
  display: flex;
  flex-direction: column;
  justify-content: center;
  gap: 28rpx;
  padding-top: 64rpx;
}

.login-hero__eyebrow {
  display: block;
  font-size: 24rpx;
  letter-spacing: 3rpx;
  opacity: 0.82;
}

.login-hero__title {
  display: block;
  margin-top: 14rpx;
  font-size: 46rpx;
  font-weight: 700;
  line-height: 1.3;
}

.login-hero__desc {
  display: block;
  margin-top: 18rpx;
  font-size: 24rpx;
  line-height: 1.7;
  opacity: 0.92;
}

.login-bind-notice {
  margin-bottom: 24rpx;
  padding: 24rpx;
  border-radius: 22rpx;
  background: rgba(22, 93, 255, 0.08);
}

.login-bind-notice__title,
.login-bind-notice__desc {
  display: block;
}

.login-bind-notice__title {
  font-size: 26rpx;
  font-weight: 700;
  color: #1c467a;
}

.login-bind-notice__desc {
  margin-top: 12rpx;
  font-size: 22rpx;
  line-height: 1.7;
  color: #587596;
}

.login-bind-cancel {
  margin-top: 16rpx;
}

.login-submit {
  margin-top: 8rpx;
}

.login-wechat {
  margin-top: 18rpx;
}

.login-tips {
  margin-top: 26rpx;
  padding: 24rpx;
  border-radius: 22rpx;
  background: rgba(17, 77, 141, 0.05);
}

.login-tips__title {
  display: block;
  font-size: 24rpx;
  font-weight: 700;
  color: #1e4065;
}

.login-tips__item {
  display: block;
  margin-top: 12rpx;
  font-size: 22rpx;
  line-height: 1.6;
  color: #69809b;
}
</style>
