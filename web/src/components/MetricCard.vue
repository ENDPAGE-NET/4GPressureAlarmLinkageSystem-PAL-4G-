<template>
  <PanelCard :description="description">
    <div class="metric-card">
      <div class="metric-card__eyebrow">{{ title }}</div>
      <div class="metric-card__value">{{ value }}</div>
      <div class="metric-card__footer">
        <el-tag :type="tagType" effect="dark" round>{{ tagLabel || t('common.realtime') }}</el-tag>
      </div>
    </div>
  </PanelCard>
</template>

<script setup lang="ts">
import PanelCard from './PanelCard.vue'
import { useI18n } from '@/composables/useI18n'

const { t } = useI18n()

withDefaults(
  defineProps<{
    title: string
    value: string | number
    description?: string
    tagLabel?: string
    tagType?: 'success' | 'warning' | 'danger' | 'info' | 'primary'
  }>(),
  {
    description: '',
    tagLabel: '',
    tagType: 'primary',
  },
)
</script>

<style scoped>
.metric-card {
  display: grid;
  gap: 12px;
  min-height: 140px;
}

.metric-card__eyebrow {
  color: var(--pal-text-muted);
  font-size: 0.9rem;
}

.metric-card__value {
  font-family:
    'DIN Alternate',
    'Bahnschrift',
    'Noto Sans SC',
    sans-serif;
  font-size: clamp(2rem, 2vw, 2.8rem);
  font-weight: 700;
  letter-spacing: 0.05em;
}

.metric-card__footer {
  display: flex;
  justify-content: flex-start;
}
</style>
