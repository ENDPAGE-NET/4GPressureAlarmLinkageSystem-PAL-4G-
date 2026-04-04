<template>
  <article class="module-card">
    <header class="module-card__head">
      <div class="module-card__identity">
        <p>{{ item.device_name }}</p>
        <strong>{{ item.module_code }}</strong>
        <span>{{ item.serial_number }}</span>
      </div>
      <StatusPill :value="item.is_online ? 'online' : 'offline'" :mapping="onlineStatusMeta" />
    </header>

    <div class="module-card__grid">
      <div class="module-card__metric">
        <span>{{ t('dashboard.modulePanels.battery') }}</span>
        <strong>{{ formatBattery(item.battery_level) }}</strong>
      </div>
      <div class="module-card__metric">
        <span>{{ t('dashboard.modulePanels.voltage') }}</span>
        <strong>{{ formatVoltage(item.voltage_value) }}</strong>
      </div>
      <div class="module-card__metric">
        <span>{{ t('dashboard.modulePanels.relay') }}</span>
        <strong>{{ item.relay_state ? t('status.relay.closed') : t('status.relay.open') }}</strong>
      </div>
      <div class="module-card__metric">
        <span>{{ t('dashboard.modulePanels.lastSeen') }}</span>
        <strong>{{ formatDateTime(item.last_seen_at) }}</strong>
      </div>
      <div class="module-card__metric">
        <span>{{ t('dashboard.modulePanels.latestAlarmType') }}</span>
        <strong>{{ resolveAlarmType(item.latest_alarm_type) }}</strong>
      </div>
      <div class="module-card__metric">
        <span>{{ t('dashboard.modulePanels.latestAlarmTime') }}</span>
        <strong>{{ formatDateTime(item.latest_alarm_time) }}</strong>
      </div>
    </div>
  </article>
</template>

<script setup lang="ts">
import StatusPill from '@/components/StatusPill.vue'
import { useI18n } from '@/composables/useI18n'
import type { DashboardModulePanelItem } from '@/types/domain'
import { formatBattery, formatDateTime, formatVoltage } from '@/utils/format'

defineProps<{
  item: DashboardModulePanelItem
}>()

const { t } = useI18n()

const onlineStatusMeta = {
  online: { type: 'success', labelKey: 'dashboard.modulePanels.status.online' },
  offline: { type: 'danger', labelKey: 'dashboard.modulePanels.status.offline' },
}

function resolveAlarmType(alarmType: string | null) {
  if (!alarmType) {
    return '--'
  }
  const translated = t(`alarms.types.${alarmType}`)
  return translated === `alarms.types.${alarmType}` ? alarmType : translated
}
</script>

<style scoped>
.module-card {
  display: grid;
  gap: 18px;
  padding: 18px;
  border: 1px solid var(--pal-line);
  border-radius: var(--pal-radius-lg);
  background:
    linear-gradient(180deg, rgba(255, 255, 255, 0.04), rgba(255, 255, 255, 0.01)),
    rgba(6, 18, 25, 0.72);
  box-shadow: 0 14px 30px rgba(0, 0, 0, 0.12);
}

.module-card__head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
}

.module-card__identity p,
.module-card__identity span {
  margin: 0;
  color: var(--pal-text-muted);
}

.module-card__identity strong {
  display: block;
  margin: 4px 0;
  font-size: 1.1rem;
}

.module-card__grid {
  display: grid;
  gap: 12px;
  grid-template-columns: repeat(2, minmax(0, 1fr));
}

.module-card__metric {
  display: grid;
  gap: 4px;
  padding: 12px 14px;
  border: 1px solid rgba(255, 255, 255, 0.06);
  border-radius: var(--pal-radius-md);
  background: rgba(255, 255, 255, 0.02);
}

.module-card__metric span {
  color: var(--pal-text-muted);
  font-size: 0.82rem;
}

.module-card__metric strong {
  font-size: 0.98rem;
  line-height: 1.4;
}

@media (max-width: 640px) {
  .module-card__head {
    flex-direction: column;
    align-items: flex-start;
  }

  .module-card__grid {
    grid-template-columns: 1fr;
  }
}
</style>
