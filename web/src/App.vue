<template>
  <el-config-provider :locale="elementLocale">
    <router-view />
  </el-config-provider>
</template>

<script setup lang="ts">
import en from 'element-plus/es/locale/lang/en'
import zhCn from 'element-plus/es/locale/lang/zh-cn'
import { computed, watchEffect } from 'vue'

import { useSettingsStore } from '@/stores/settings'

const settingsStore = useSettingsStore()

const elementLocale = computed(() =>
  settingsStore.localeCode === 'en-US' ? en : zhCn,
)

watchEffect(() => {
  document.documentElement.dataset.theme = settingsStore.themeMode
  document.documentElement.lang = settingsStore.localeCode
})
</script>
