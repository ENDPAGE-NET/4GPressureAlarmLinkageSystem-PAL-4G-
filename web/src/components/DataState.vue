<template>
  <div v-if="loading" class="state-block">
    <el-skeleton :rows="4" animated style="width: 100%" />
  </div>

  <div v-else-if="error" class="state-block">
    <el-result class="state-block__error" icon="error" :title="t('common.loadingFailed')" :sub-title="error">
      <template #extra>
        <el-button type="primary" @click="$emit('retry')">{{ t('common.reload') }}</el-button>
      </template>
    </el-result>
  </div>

  <div v-else-if="empty" class="state-block">
    <el-empty :description="emptyText || t('common.noData')" />
  </div>

  <slot v-else />
</template>

<script setup lang="ts">
import { useI18n } from '@/composables/useI18n'

const { t } = useI18n()

withDefaults(
  defineProps<{
    loading?: boolean
    error?: string
    empty?: boolean
    emptyText?: string
  }>(),
  {
    loading: false,
    error: '',
    empty: false,
    emptyText: '',
  },
)

defineEmits<{
  retry: []
}>()
</script>
