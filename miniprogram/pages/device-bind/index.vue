<template>
  <view class="app-page">
    <view class="hero-panel">
      <text class="section-title">绑定新设备</text>
      <text class="section-subtitle">
        输入设备序列号即可将新设备纳入当前账号的监控和控制范围。
      </text>
    </view>

    <view class="panel-card bind-form">
      <view class="form-field">
        <text class="form-label">设备序列号 SN</text>
        <input v-model.trim="form.serialNumber" class="form-input" placeholder="请输入设备序列号" />
      </view>

      <view class="form-field">
        <text class="form-label">设备显示名称（可选）</text>
        <input v-model.trim="form.name" class="form-input" placeholder="例如：泵房 A 组" />
      </view>

      <view class="bind-actions">
        <button class="secondary-button" @click="handleScan">扫码填充</button>
        <button class="primary-button" :loading="submitting" @click="handleSubmit">确认绑定</button>
      </view>
    </view>

    <!-- 绑定成功后显示 MQTT 配置信息 -->
    <view v-if="mqttConfig" class="panel-card">
      <text class="section-title">MQTT 接入配置</text>
      <text class="section-subtitle" style="margin-bottom: 16rpx">请将以下信息配置到设备的 4G 模块中</text>
      <view class="config-item">
        <text class="config-label">服务器</text>
        <text class="config-value">{{ mqttConfig.broker_host }}</text>
      </view>
      <view class="config-item">
        <text class="config-label">端口</text>
        <text class="config-value">{{ mqttConfig.broker_port }}</text>
      </view>
      <view class="config-item">
        <text class="config-label">用户名</text>
        <text class="config-value">{{ mqttConfig.mqtt_username }}</text>
      </view>
      <view class="config-item">
        <text class="config-label">密码</text>
        <text class="config-value">{{ mqttConfig.mqtt_password }}</text>
      </view>
      <view class="config-item">
        <text class="config-label">客户端 ID</text>
        <text class="config-value">{{ mqttConfig.mqtt_client_id }}</text>
      </view>
      <view class="bind-actions" style="margin-top: 20rpx">
        <button class="primary-button" @click="goToDevice">查看设备详情</button>
      </view>
    </view>
  </view>
</template>

<script setup>
import { reactive, ref } from 'vue'
import { onShow } from '@dcloudio/uni-app'

import { bindDeviceApi } from '@/api/devices'
import { request } from '@/api/http'
import { showRequestError } from '@/utils/errors'
import { ensureAuthenticated } from '@/utils/guards'

const form = reactive({
  serialNumber: '',
  name: '',
})
const submitting = ref(false)
const mqttConfig = ref(null)
const boundDeviceId = ref(null)

onShow(() => {
  void ensureAuthenticated()
})

function handleScan() {
  uni.scanCode({
    onlyFromCamera: false,
    success: (result) => {
      form.serialNumber = result.result || ''
    },
    fail: () => {
      uni.showToast({
        title: '扫码未完成',
        icon: 'none',
      })
    },
  })
}

async function handleSubmit() {
  if (!(await ensureAuthenticated())) {
    return
  }

  if (!form.serialNumber) {
    uni.showToast({
      title: '请输入设备序列号',
      icon: 'none',
    })
    return
  }

  submitting.value = true
  try {
    const device = await bindDeviceApi({
      serial_number: form.serialNumber,
      name: form.name || undefined,
    })
    boundDeviceId.value = device.id
    uni.showToast({
      title: '绑定成功',
      icon: 'success',
    })
    // 拉取 MQTT 配置展示给用户
    try {
      const config = await request({ url: `/devices/${device.id}/mqtt-config` })
      mqttConfig.value = config
    } catch {
      // 配置获取失败不影响主流程，直接跳转
      uni.redirectTo({
        url: `/pages/device-detail/index?deviceId=${device.id}`,
      })
    }
  } catch (error) {
    showRequestError(error, '设备绑定失败')
  } finally {
    submitting.value = false
  }
}

function goToDevice() {
  if (boundDeviceId.value) {
    uni.redirectTo({
      url: `/pages/device-detail/index?deviceId=${boundDeviceId.value}`,
    })
  }
}
</script>

<style scoped>
.bind-actions {
  display: grid;
  gap: 16rpx;
  margin-top: 10rpx;
}

.bind-actions button {
  width: 100%;
}

.config-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12rpx 0;
  border-bottom: 1rpx solid #f0f0f0;
}

.config-label {
  font-size: 28rpx;
  color: #666;
  flex-shrink: 0;
}

.config-value {
  font-size: 26rpx;
  color: #333;
  font-family: monospace;
  word-break: break-all;
  text-align: right;
  margin-left: 20rpx;
}
</style>
