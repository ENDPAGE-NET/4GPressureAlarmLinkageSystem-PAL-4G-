<template>
  <div class="page-shell">
    <div class="page-title">
      <div>
        <h1>{{ t('exports.title') }}</h1>
        <p>{{ t('exports.description') }}</p>
      </div>
    </div>

    <div class="page-grid" style="grid-template-columns: repeat(2, minmax(0, 1fr))">
      <PanelCard :title="t('exports.alarms')" :description="t('exports.alarmDesc')">
        <el-button type="primary" :loading="downloading === 'alarms'" @click="download('alarms')">
          {{ t('exports.alarms') }}
        </el-button>
      </PanelCard>

      <PanelCard :title="t('exports.commands')" :description="t('exports.commandDesc')">
        <el-button type="primary" :loading="downloading === 'commands'" @click="download('commands')">
          {{ t('exports.commands') }}
        </el-button>
      </PanelCard>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ElMessage } from 'element-plus'
import { ref } from 'vue'

import { exportAlarmsApi, exportCommandsApi } from '@/api/exports'
import PanelCard from '@/components/PanelCard.vue'
import { useI18n } from '@/composables/useI18n'

const { t } = useI18n()
const downloading = ref<'alarms' | 'commands' | ''>('')

async function download(kind: 'alarms' | 'commands') {
  downloading.value = kind
  try {
    if (kind === 'alarms') {
      await exportAlarmsApi()
    } else {
      await exportCommandsApi()
    }
    ElMessage.success(t('exports.success'))
  } catch {
    ElMessage.error(t('exports.failed'))
  } finally {
    downloading.value = ''
  }
}
</script>
