<template>
  <view
    class="settings-menu-item"
    :class="[
      clickable ? 'settings-menu-item--clickable' : '',
      danger ? 'settings-menu-item--danger' : '',
    ]"
    @click="handleClick"
  >
    <view class="settings-menu-item__content">
      <view class="settings-menu-item__main">
        <text class="settings-menu-item__title">{{ title }}</text>
        <text v-if="description" class="settings-menu-item__description">{{ description }}</text>
      </view>

      <view class="settings-menu-item__meta">
        <text v-if="value" class="settings-menu-item__value">{{ value }}</text>
        <text v-if="arrow" class="settings-menu-item__arrow">›</text>
      </view>
    </view>
  </view>
</template>

<script setup>
const props = defineProps({
  title: {
    type: String,
    required: true,
  },
  description: {
    type: String,
    default: '',
  },
  value: {
    type: String,
    default: '',
  },
  clickable: {
    type: Boolean,
    default: false,
  },
  arrow: {
    type: Boolean,
    default: false,
  },
  danger: {
    type: Boolean,
    default: false,
  },
})

const emit = defineEmits(['click'])

function handleClick() {
  if (!props.clickable) {
    return
  }

  emit('click')
}
</script>

<style scoped>
.settings-menu-item + .settings-menu-item {
  border-top: 1rpx solid rgba(22, 83, 143, 0.08);
}

.settings-menu-item__content {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 20rpx;
  padding: 24rpx 0;
}

.settings-menu-item__main {
  min-width: 0;
  flex: 1;
}

.settings-menu-item__title,
.settings-menu-item__description,
.settings-menu-item__value,
.settings-menu-item__arrow {
  display: block;
}

.settings-menu-item__title {
  font-size: 28rpx;
  font-weight: 600;
  line-height: 1.5;
  color: #17324d;
}

.settings-menu-item__description {
  margin-top: 8rpx;
  font-size: 22rpx;
  line-height: 1.6;
  color: #7188a3;
}

.settings-menu-item__meta {
  display: flex;
  align-items: center;
  gap: 12rpx;
  flex: 0 0 auto;
}

.settings-menu-item__value {
  max-width: 280rpx;
  font-size: 24rpx;
  line-height: 1.5;
  text-align: right;
  color: #5f7895;
}

.settings-menu-item__arrow {
  font-size: 34rpx;
  line-height: 1;
  color: #9db0c4;
}

.settings-menu-item--clickable:active {
  opacity: 0.72;
}

.settings-menu-item--danger .settings-menu-item__title,
.settings-menu-item--danger .settings-menu-item__value,
.settings-menu-item--danger .settings-menu-item__arrow {
  color: #d54d3b;
}
</style>
