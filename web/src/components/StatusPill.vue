<template>
  <el-tag :type="meta.type as never" effect="dark" round>{{ meta.label }}</el-tag>
</template>

<script setup lang="ts">
import { computed } from 'vue'

import { useI18n } from '@/composables/useI18n'
import { resolveStatusMeta } from '@/utils/status'
import type { StatusMeta } from '@/utils/status'

const props = defineProps<{
  value?: string | null
  mapping: Record<string, StatusMeta>
}>()

const { t } = useI18n()
const meta = computed(() => {
  const resolved = resolveStatusMeta(props.mapping, props.value)
  return {
    ...resolved,
    label: resolved.labelKey ? t(resolved.labelKey) : resolved.label,
  }
})
</script>
