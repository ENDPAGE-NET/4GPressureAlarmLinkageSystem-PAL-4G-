<template>
  <view class="panel-card module-card">
    <view class="module-card__head">
      <view>
        <text class="module-card__title">
          {{ module.module_code ? `模块 ${module.module_code}` : '设备运行状态' }}
        </text>
        <text class="module-card__serial" v-if="module.serial_number || module.imei">
          {{ module.serial_number ? `SN：${module.serial_number}` : `IMEI：${module.imei}` }}
        </text>
      </view>
      <text class="status-tag" :class="getOnlineStatusClass(module.is_online)">
        {{ getOnlineStatusLabel(module.is_online) }}
      </text>
    </view>

    <view class="module-card__grid">
      <view class="module-card__metric">
        <text class="module-card__metric-label">继电器</text>
        <text class="module-card__metric-value">{{ getRelayStateLabel(module.relay_state) }}</text>
      </view>
      <view class="module-card__metric">
        <text class="module-card__metric-label">电量</text>
        <text class="module-card__metric-value">{{ formatBattery(module.battery_level) }}</text>
      </view>
      <view class="module-card__metric">
        <text class="module-card__metric-label">电压</text>
        <text class="module-card__metric-value">{{ formatVoltage(module.voltage_value) }}</text>
      </view>
      <view class="module-card__metric">
        <text class="module-card__metric-label">最后在线</text>
        <text class="module-card__metric-value module-card__metric-value--small">
          {{ formatDateTime(module.last_seen_at) }}
        </text>
      </view>
    </view>

    <view class="module-card__actions">
      <button
        class="secondary-button action-button"
        :loading="loading && targetState === 'open'"
        @click.stop="$emit('toggle', { module, targetState: 'open' })"
      >
        断开继电器
      </button>
      <button
        class="primary-button action-button"
        :loading="loading && targetState === 'closed'"
        @click.stop="$emit('toggle', { module, targetState: 'closed' })"
      >
        闭合继电器
      </button>
    </view>
  </view>
</template>

<script setup>
import { formatBattery, formatDateTime, formatVoltage } from '@/utils/format'
import { getOnlineStatusClass, getOnlineStatusLabel, getRelayStateLabel } from '@/utils/status'

defineProps({
  module: {
    type: Object,
    required: true,
  },
  loading: {
    type: Boolean,
    default: false,
  },
  targetState: {
    type: String,
    default: '',
  },
})

defineEmits(['toggle'])
</script>

<style scoped>
.module-card__head {
  display: flex;
  flex-direction: column;
  gap: 20rpx;
}

.module-card {
  padding: 28rpx;
}

.module-card__title {
  display: block;
  font-size: 28rpx;
  font-weight: 700;
  line-height: 1.4;
}

.module-card__serial {
  display: block;
  margin-top: 8rpx;
  font-size: 22rpx;
  line-height: 1.6;
  color: #6b84a2;
}

.module-card__grid {
  display: grid;
  grid-template-columns: minmax(0, 1fr);
  gap: 14rpx;
  margin-top: 24rpx;
}

.module-card__metric {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 18rpx;
  padding: 20rpx 22rpx;
  border-radius: 22rpx;
  background: rgba(26, 100, 180, 0.05);
}

.module-card__metric-label {
  flex: 0 0 auto;
  font-size: 22rpx;
  line-height: 1.5;
  color: #7188a3;
}

.module-card__metric-value {
  flex: 1;
  min-width: 0;
  text-align: right;
  font-size: 28rpx;
  font-weight: 700;
  line-height: 1.4;
}

.module-card__metric-value--small {
  font-size: 22rpx;
  line-height: 1.5;
}

.module-card__actions {
  display: grid;
  gap: 14rpx;
  margin-top: 26rpx;
}

.action-button {
  width: 100%;
}
</style>
