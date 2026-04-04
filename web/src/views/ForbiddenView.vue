<template>
  <div class="state-block" style="min-height: 100vh">
    <el-result icon="warning" :title="t('auth.forbidden')" :sub-title="t('auth.forbiddenDesc')">
      <template #extra>
        <el-button type="primary" @click="$router.push('/dashboard')">{{ t('common.backToDashboard') }}</el-button>
      </template>
    </el-result>
  </div>
</template>

<script setup lang="ts">
import { useI18n } from '@/composables/useI18n'

const { t } = useI18n()
</script>
