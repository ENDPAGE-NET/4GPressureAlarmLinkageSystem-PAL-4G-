<template>
  <div class="login-shell">
    <div class="login-shell__panel">
      <div class="login-shell__hero">
        <span class="login-shell__eyebrow">PAL 4G FIRST RELEASE</span>
        <h1>{{ t('auth.loginTitle') }}</h1>
        <p>{{ t('auth.loginDesc') }}</p>

        <div class="login-shell__chips">
          <el-tag type="primary" effect="dark" round>{{ t('auth.hints.jwt') }}</el-tag>
          <el-tag type="success" effect="dark" round>{{ t('auth.hints.dashboard') }}</el-tag>
          <el-tag type="warning" effect="dark" round>{{ t('auth.hints.control') }}</el-tag>
        </div>
      </div>

      <PanelCard :title="t('auth.login')" :description="t('auth.loginPanelDesc')">
        <el-form
          ref="formRef"
          :model="form"
          :rules="rules"
          label-position="top"
          @submit.prevent="handleSubmit"
        >
          <el-form-item :label="t('auth.username')" prop="username">
            <el-input v-model="form.username" :placeholder="t('auth.usernamePlaceholder')" size="large" />
          </el-form-item>

          <el-form-item :label="t('auth.password')" prop="password">
            <el-input
              v-model="form.password"
              :placeholder="t('auth.passwordPlaceholder')"
              size="large"
              show-password
              type="password"
              @keyup.enter="handleSubmit"
            />
          </el-form-item>

          <el-alert
            v-if="errorMessage"
            :closable="false"
            :title="errorMessage"
            type="error"
            show-icon
          />

          <el-button
            class="login-shell__submit"
            type="primary"
            size="large"
            :loading="authStore.loading"
            @click="handleSubmit"
          >
            {{ t('auth.loginButton') }}
          </el-button>
        </el-form>
      </PanelCard>
    </div>
  </div>
</template>

<script setup lang="ts">
import type { FormInstance, FormRules } from 'element-plus'
import { ElMessage } from 'element-plus'
import { reactive, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'

import PanelCard from '@/components/PanelCard.vue'
import { useI18n } from '@/composables/useI18n'
import { useAuthStore } from '@/stores/auth'

const authStore = useAuthStore()
const { t } = useI18n()
const route = useRoute()
const router = useRouter()

const formRef = ref<FormInstance>()
const errorMessage = ref('')
const form = reactive({
  username: 'admin',
  password: 'admin123456',
})

const rules: FormRules<typeof form> = {
  username: [{ required: true, message: t('auth.usernameRequired'), trigger: 'blur' }],
  password: [{ required: true, message: t('auth.passwordRequired'), trigger: 'blur' }],
}

async function handleSubmit() {
  const valid = await formRef.value?.validate().catch(() => false)
  if (!valid) {
    return
  }

  errorMessage.value = ''

  try {
    await authStore.login(form.username, form.password)
    ElMessage.success(t('auth.loginSuccess'))
    const redirect = typeof route.query.redirect === 'string' ? route.query.redirect : '/dashboard'
    await router.push(redirect)
  } catch (error: any) {
    errorMessage.value = error.response?.data?.detail || t('auth.loginError')
  }
}
</script>

<style scoped>
.login-shell {
  min-height: 100vh;
  display: grid;
  place-items: center;
  padding: 28px;
}

.login-shell__panel {
  width: min(1080px, 100%);
  display: grid;
  grid-template-columns: 1.15fr 0.85fr;
  gap: 24px;
  align-items: stretch;
}

.login-shell__hero {
  padding: 42px;
  border: 1px solid rgba(125, 177, 188, 0.16);
  border-radius: 28px;
  background:
    radial-gradient(circle at top left, rgba(51, 198, 216, 0.16), transparent 34%),
    linear-gradient(180deg, rgba(8, 25, 34, 0.92), rgba(6, 18, 25, 0.88));
  box-shadow: 0 32px 80px rgba(2, 10, 15, 0.35);
}

.login-shell__eyebrow {
  color: var(--pal-accent);
  font-size: 0.84rem;
  letter-spacing: 0.18em;
}

.login-shell__hero h1 {
  margin: 18px 0 18px;
  max-width: 10em;
  font-family:
    'DIN Alternate',
    'Bahnschrift',
    'Noto Sans SC',
    sans-serif;
  font-size: clamp(2rem, 4vw, 3.3rem);
  line-height: 1.05;
}

.login-shell__hero p {
  max-width: 38rem;
  color: var(--pal-text-muted);
  font-size: 1rem;
}

.login-shell__chips {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  margin-top: 28px;
}

.login-shell__submit {
  width: 100%;
  margin-top: 8px;
}

@media (max-width: 960px) {
  .login-shell__panel {
    grid-template-columns: 1fr;
  }

  .login-shell__hero {
    padding: 28px;
  }
}
</style>
