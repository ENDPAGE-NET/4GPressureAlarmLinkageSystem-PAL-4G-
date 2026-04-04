<template>
  <PanelCard :title="`${t('common.columns.moduleCode')} ${module.module_code}`" :description="t('moduleControl.description')">
    <div class="module-card">
      <div class="module-card__status">
        <StatusPill :value="module.is_online ? 'all_online' : 'all_offline'" :mapping="deviceStatusMeta" />
        <el-tag :type="module.relay_state ? 'danger' : 'success'" effect="dark" round>
          {{ module.relay_state ? t('status.relay.closed') : t('status.relay.open') }}
        </el-tag>
      </div>

      <div class="module-card__meta">
        <div>
          <span>{{ t('moduleControl.battery') }}</span>
          <strong>{{ formatBattery(module.battery_level) }}</strong>
        </div>
        <div>
          <span>{{ t('moduleControl.voltage') }}</span>
          <strong>{{ formatVoltage(module.voltage_value) }}</strong>
        </div>
        <div>
          <span>{{ t('moduleControl.lastSeen') }}</span>
          <strong>{{ formatDateTime(module.last_seen_at) }}</strong>
        </div>
      </div>

      <div class="module-card__actions">
        <el-button
          type="danger"
          :loading="loadingState === 'open'"
          @click="$emit('control', module.id, 'open')"
        >
          {{ t('moduleControl.closeRelay') }}
        </el-button>
        <el-button
          type="success"
          plain
          :loading="loadingState === 'closed'"
          @click="$emit('control', module.id, 'closed')"
        >
          {{ t('moduleControl.openRelay') }}
        </el-button>
      </div>
    </div>
  </PanelCard>
</template>

<script setup lang="ts">
import PanelCard from './PanelCard.vue'
import StatusPill from './StatusPill.vue'
import { useI18n } from '@/composables/useI18n'
import { formatBattery, formatDateTime, formatVoltage } from '@/utils/format'
import { deviceStatusMeta } from '@/utils/status'
import type { ModuleRead } from '@/types/domain'

const { t } = useI18n()

defineProps<{
  module: ModuleRead
  loadingState?: '' | 'open' | 'closed'
}>()

defineEmits<{
  control: [moduleId: number, targetState: 'open' | 'closed']
}>()
</script>

<style scoped>
.module-card {
  display: grid;
  gap: 18px;
}

.module-card__status {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}

.module-card__meta {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 12px;
}

.module-card__meta div {
  display: grid;
  gap: 6px;
  padding: 14px;
  border: 1px solid var(--pal-line);
  border-radius: var(--pal-radius-md);
  background: rgba(255, 255, 255, 0.02);
}

.module-card__meta span {
  color: var(--pal-text-muted);
  font-size: 0.86rem;
}

.module-card__actions {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}

@media (max-width: 768px) {
  .module-card__meta {
    grid-template-columns: 1fr;
  }
}
</style>
