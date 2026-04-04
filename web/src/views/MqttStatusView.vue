<template>
  <div class="page-shell">
    <div class="page-title">
      <div>
        <h1>{{ t('mqtt.title') }}</h1>
        <p>{{ t('mqtt.description') }}</p>
      </div>
      <el-button type="primary" plain @click="fetchStatus">{{ t('common.refresh') }}</el-button>
    </div>

    <PanelCard :title="t('mqtt.title')" :description="t('mqtt.description')">
      <DataState :loading="loading" :error="error" @retry="fetchStatus">
        <div class="kv-list">
          <div class="kv-item">
            <div class="kv-item__label">{{ t('mqtt.connected') }}</div>
            <div class="kv-item__value">
              <el-tag :type="status?.connected ? 'success' : 'danger'" effect="dark" round>
                {{ status?.connected ? t('operations.running') : t('operations.stopped') }}
              </el-tag>
            </div>
          </div>
          <div class="kv-item">
            <div class="kv-item__label">{{ t('mqtt.broker') }}</div>
            <div class="kv-item__value mono">{{ status?.broker_host }}:{{ status?.broker_port }}</div>
          </div>
          <div class="kv-item">
            <div class="kv-item__label">{{ t('mqtt.statusTopic') }}</div>
            <div class="kv-item__value mono">{{ status?.status_topic }}</div>
          </div>
          <div class="kv-item">
            <div class="kv-item__label">{{ t('mqtt.subscribedTopics') }}</div>
            <div class="kv-item__value">{{ status?.subscribed_topics.join(', ') || '--' }}</div>
          </div>
          <div class="kv-item">
            <div class="kv-item__label">{{ t('mqtt.inbound') }}</div>
            <div class="kv-item__value mono">{{ status?.last_inbound_topic || '--' }}</div>
          </div>
          <div class="kv-item">
            <div class="kv-item__label">{{ t('mqtt.outbound') }}</div>
            <div class="kv-item__value mono">{{ status?.last_outbound_topic || '--' }}</div>
          </div>
        </div>
      </DataState>
    </PanelCard>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'

import { getMqttStatusApi } from '@/api/mqtt'
import DataState from '@/components/DataState.vue'
import PanelCard from '@/components/PanelCard.vue'
import { useI18n } from '@/composables/useI18n'
import type { MqttClientStatus } from '@/types/domain'

const { t } = useI18n()
const loading = ref(true)
const error = ref('')
const status = ref<MqttClientStatus | null>(null)

async function fetchStatus() {
  loading.value = true
  error.value = ''
  try {
    status.value = await getMqttStatusApi()
  } catch (err: any) {
    error.value = err.response?.data?.detail || t('mqtt.loadError')
  } finally {
    loading.value = false
  }
}

void fetchStatus()
</script>
