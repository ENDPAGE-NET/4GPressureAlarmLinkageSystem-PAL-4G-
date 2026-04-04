<template>
  <div class="page-shell">
    <div class="page-title">
      <div>
        <h1>{{ t('profile.title') }}</h1>
        <p>{{ t('profile.description') }}</p>
      </div>
    </div>

    <div class="page-grid profile-grid">
      <PanelCard :title="t('profile.accountTitle')" :description="t('profile.accountDesc')">
        <div class="kv-list">
          <div class="kv-item">
            <div class="kv-item__label">{{ t('auth.username') }}</div>
            <div class="kv-item__value">{{ authStore.profile?.username }}</div>
          </div>
          <div class="kv-item">
            <div class="kv-item__label">{{ t('users.role') }}</div>
            <div class="kv-item__value">{{ authStore.profile?.role ? t(`roles.${authStore.profile.role}`) : '--' }}</div>
          </div>
          <div class="kv-item">
            <div class="kv-item__label">{{ t('profile.accountStatus') }}</div>
            <div class="kv-item__value">
              <el-tag :type="authStore.profile?.is_active ? 'success' : 'danger'" effect="dark" round>
                {{ authStore.profile?.is_active ? t('profile.active') : t('profile.inactive') }}
              </el-tag>
            </div>
          </div>
        </div>
      </PanelCard>

      <PanelCard :title="t('profile.changePassword')" :description="t('profile.changePasswordDesc')">
        <el-form ref="formRef" :model="form" :rules="rules" label-position="top">
          <el-form-item :label="t('profile.currentPassword')" prop="currentPassword">
            <el-input
              v-model="form.currentPassword"
              show-password
              type="password"
              :placeholder="t('profile.currentPasswordPlaceholder')"
            />
          </el-form-item>
          <el-form-item :label="t('profile.newPassword')" prop="newPassword">
            <el-input
              v-model="form.newPassword"
              show-password
              type="password"
              :placeholder="t('profile.newPasswordPlaceholder')"
            />
          </el-form-item>
          <el-form-item :label="t('profile.confirmPassword')" prop="confirmPassword">
            <el-input
              v-model="form.confirmPassword"
              show-password
              type="password"
              :placeholder="t('profile.confirmPasswordPlaceholder')"
              @keyup.enter="handleSubmit"
            />
          </el-form-item>

          <el-alert
            v-if="errorMessage"
            :closable="false"
            :title="errorMessage"
            type="error"
            show-icon
            style="margin-bottom: 16px"
          />

          <el-button type="primary" :loading="submitting" @click="handleSubmit">{{ t('common.confirm') }}</el-button>
        </el-form>
      </PanelCard>
    </div>
  </div>
</template>

<script setup lang="ts">
import type { FormInstance, FormRules } from 'element-plus'
import { ElMessage } from 'element-plus'
import { reactive, ref } from 'vue'
import { useRouter } from 'vue-router'

import { changePasswordApi } from '@/api/users'
import PanelCard from '@/components/PanelCard.vue'
import { useI18n } from '@/composables/useI18n'
import { useAuthStore } from '@/stores/auth'

const authStore = useAuthStore()
const { t } = useI18n()
const router = useRouter()
const formRef = ref<FormInstance>()
const submitting = ref(false)
const errorMessage = ref('')

const form = reactive({
  currentPassword: '',
  newPassword: '',
  confirmPassword: '',
})

const rules: FormRules<typeof form> = {
  currentPassword: [{ required: true, message: t('profile.currentPasswordRequired'), trigger: 'blur' }],
  newPassword: [
    { required: true, message: t('profile.newPasswordRequired'), trigger: 'blur' },
    { min: 8, message: t('profile.newPasswordMin'), trigger: 'blur' },
  ],
  confirmPassword: [
    { required: true, message: t('profile.confirmPasswordRequired'), trigger: 'blur' },
    {
      validator: (_rule, value, callback) => {
        if (value !== form.newPassword) {
          callback(new Error(t('profile.confirmPasswordMismatch')))
          return
        }
        callback()
      },
      trigger: 'blur',
    },
  ],
}

async function handleSubmit() {
  const valid = await formRef.value?.validate().catch(() => false)
  if (!valid) {
    return
  }

  errorMessage.value = ''
  submitting.value = true

  try {
    await changePasswordApi({
      current_password: form.currentPassword,
      new_password: form.newPassword,
    })
    ElMessage.success(t('profile.reLogin'))
    authStore.logout()
    await router.push('/login')
  } catch (err: any) {
    errorMessage.value = err.response?.data?.detail || t('profile.changePasswordFailed')
  } finally {
    submitting.value = false
  }
}
</script>

<style scoped>
.profile-grid {
  grid-template-columns: 0.9fr 1.1fr;
}

@media (max-width: 960px) {
  .profile-grid {
    grid-template-columns: 1fr;
  }
}
</style>
