<template>
  <div class="page-shell">
    <div class="page-title">
      <div>
        <h1>{{ t('users.title') }}</h1>
        <p>{{ t('users.description') }}</p>
      </div>
      <el-button type="primary" @click="openCreateDialog">{{ t('users.createUser') }}</el-button>
    </div>

    <PanelCard>
      <div class="toolbar">
        <div class="toolbar__filters">
          <el-input v-model="keyword" clearable :placeholder="t('common.search')" style="width: 260px" />
        </div>
        <div class="toolbar__actions">
          <el-button plain @click="fetchUsers">{{ t('common.refresh') }}</el-button>
        </div>
      </div>
    </PanelCard>

    <PanelCard :title="t('users.title')" :description="t('users.description')">
      <DataState :loading="loading" :error="error" :empty="!filteredUsers.length" @retry="fetchUsers">
        <div class="data-table">
          <el-table :data="filteredUsers">
            <el-table-column prop="username" :label="t('auth.username')" min-width="160" />
            <el-table-column prop="role" :label="t('users.role')" min-width="130" />
            <el-table-column :label="t('users.active')" min-width="110">
              <template #default="{ row }">
                <el-tag :type="row.is_active ? 'success' : 'danger'" effect="dark" round>
                  {{ row.is_active ? t('common.enabled') : t('common.disabled') }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column :label="t('users.createdAt')" min-width="180">
              <template #default="{ row }">{{ formatDateTime(row.created_at) }}</template>
            </el-table-column>
            <el-table-column :label="t('users.updatedAt')" min-width="180">
              <template #default="{ row }">{{ formatDateTime(row.updated_at) }}</template>
            </el-table-column>
            <el-table-column :label="t('common.actions')" min-width="220" fixed="right">
              <template #default="{ row }">
                <el-button link type="primary" @click="openEditDialog(row)">{{ t('common.edit') }}</el-button>
                <el-button link type="warning" @click="openResetDialog(row)">{{ t('users.resetPassword') }}</el-button>
                <el-button
                  link
                  :type="row.is_active ? 'danger' : 'success'"
                  @click="toggleUserStatus(row)"
                >
                  {{ row.is_active ? t('status.device.inactive') : t('status.device.active') }}
                </el-button>
              </template>
            </el-table-column>
          </el-table>
        </div>
      </DataState>
    </PanelCard>

    <el-dialog v-model="editDialogVisible" :title="dialogMode === 'create' ? t('users.createUser') : t('users.editUser')" width="460px">
      <el-form ref="editFormRef" :model="editForm" :rules="editRules" label-position="top">
        <el-form-item :label="t('auth.username')" prop="username">
          <el-input v-model="editForm.username" :disabled="dialogMode === 'edit'" />
        </el-form-item>
        <el-form-item :label="t('users.role')" prop="role">
          <el-select v-model="editForm.role" style="width: 100%">
            <el-option :label="t('roles.super_admin')" value="super_admin" />
            <el-option :label="t('roles.manager')" value="manager" />
          </el-select>
        </el-form-item>
        <el-form-item v-if="dialogMode === 'create'" :label="t('auth.password')" prop="password">
          <el-input v-model="editForm.password" show-password type="password" />
        </el-form-item>
          <el-form-item v-else :label="t('auth.password')" prop="password">
            <el-input v-model="editForm.password" show-password type="password" :placeholder="t('users.passwordPlaceholder')" />
          </el-form-item>
        <el-form-item v-if="dialogMode === 'edit'" :label="t('users.active')" prop="is_active">
          <el-switch v-model="editForm.is_active" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="editDialogVisible = false">{{ t('common.cancel') }}</el-button>
        <el-button type="primary" :loading="submitting" @click="submitEdit">{{ t('common.save') }}</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="resetDialogVisible" :title="t('users.resetPassword')" width="420px">
      <el-form ref="resetFormRef" :model="resetForm" :rules="resetRules" label-position="top">
        <el-form-item :label="t('users.newPassword')" prop="new_password">
          <el-input v-model="resetForm.new_password" show-password type="password" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="resetDialogVisible = false">{{ t('common.cancel') }}</el-button>
        <el-button type="primary" :loading="submitting" @click="submitReset">{{ t('common.confirm') }}</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import type { FormInstance, FormRules } from 'element-plus'
import { ElMessage } from 'element-plus'
import { computed, reactive, ref } from 'vue'

import { useI18n } from '@/composables/useI18n'
import DataState from '@/components/DataState.vue'
import PanelCard from '@/components/PanelCard.vue'
import { createUserApi, getUsersApi, resetUserPasswordApi, updateUserApi } from '@/api/users'
import type { UserCreatePayload, UserRead } from '@/types/domain'
import { formatDateTime } from '@/utils/format'

const { t } = useI18n()
const loading = ref(true)
const error = ref('')
const users = ref<UserRead[]>([])
const keyword = ref('')
const dialogMode = ref<'create' | 'edit'>('create')
const editDialogVisible = ref(false)
const resetDialogVisible = ref(false)
const submitting = ref(false)
const currentUser = ref<UserRead | null>(null)
const editFormRef = ref<FormInstance>()
const resetFormRef = ref<FormInstance>()

const editForm = reactive({
  username: '',
  role: 'manager' as UserCreatePayload['role'],
  password: '',
  is_active: true,
})

const resetForm = reactive({
  new_password: '',
})

const editRules: FormRules<typeof editForm> = {
  username: [{ required: true, message: t('users.validations.usernameRequired'), trigger: 'blur' }],
  role: [{ required: true, message: t('users.validations.roleRequired'), trigger: 'change' }],
  password: [
    {
      validator: (_rule, value, callback) => {
        if (dialogMode.value === 'create' && (!value || value.length < 8)) {
          callback(new Error(t('users.validations.passwordMin')))
          return
        }
        if (dialogMode.value === 'edit' && value && value.length < 8) {
          callback(new Error(t('users.validations.passwordMin')))
          return
        }
        callback()
      },
      trigger: 'blur',
    },
  ],
}

const resetRules: FormRules<typeof resetForm> = {
  new_password: [{ required: true, min: 8, message: t('users.validations.passwordMin'), trigger: 'blur' }],
}

const filteredUsers = computed(() => {
  const search = keyword.value.trim().toLowerCase()
  if (!search) return users.value
  return users.value.filter((item) => item.username.toLowerCase().includes(search))
})

async function fetchUsers() {
  loading.value = true
  error.value = ''
  try {
    users.value = await getUsersApi()
  } catch (err: any) {
    error.value = err.response?.data?.detail || t('users.loadError')
  } finally {
    loading.value = false
  }
}

function openCreateDialog() {
  dialogMode.value = 'create'
  currentUser.value = null
  editForm.username = ''
  editForm.role = 'manager'
  editForm.password = ''
  editForm.is_active = true
  editDialogVisible.value = true
}

function openEditDialog(user: UserRead) {
  dialogMode.value = 'edit'
  currentUser.value = user
  editForm.username = user.username
  editForm.role = normalizeManagedRole(user.role)
  editForm.password = ''
  editForm.is_active = user.is_active
  editDialogVisible.value = true
}

function normalizeManagedRole(role: string): UserCreatePayload['role'] {
  return role === 'super_admin' ? 'super_admin' : 'manager'
}

function openResetDialog(user: UserRead) {
  currentUser.value = user
  resetForm.new_password = ''
  resetDialogVisible.value = true
}

async function submitEdit() {
  const valid = await editFormRef.value?.validate().catch(() => false)
  if (!valid) return

  submitting.value = true
  try {
    if (dialogMode.value === 'create') {
      await createUserApi({
        username: editForm.username,
        password: editForm.password,
        role: editForm.role,
      })
      ElMessage.success(t('users.createSuccess'))
    } else if (currentUser.value) {
      await updateUserApi(currentUser.value.id, {
        role: editForm.role,
        password: editForm.password || undefined,
        is_active: editForm.is_active,
      })
      ElMessage.success(t('users.updateSuccess'))
    }
    editDialogVisible.value = false
    await fetchUsers()
  } catch (err: any) {
    ElMessage.error(err.response?.data?.detail || t('users.saveFailed'))
  } finally {
    submitting.value = false
  }
}

async function submitReset() {
  const valid = await resetFormRef.value?.validate().catch(() => false)
  if (!valid || !currentUser.value) return

  submitting.value = true
  try {
    await resetUserPasswordApi(currentUser.value.id, resetForm)
    ElMessage.success(t('users.resetSuccess'))
    resetDialogVisible.value = false
    await fetchUsers()
  } catch (err: any) {
    ElMessage.error(err.response?.data?.detail || t('users.resetFailed'))
  } finally {
    submitting.value = false
  }
}

async function toggleUserStatus(user: UserRead) {
  try {
    await updateUserApi(user.id, {
      is_active: !user.is_active,
    })
    ElMessage.success(t('users.statusSuccess'))
    await fetchUsers()
  } catch (err: any) {
    ElMessage.error(err.response?.data?.detail || t('users.statusFailed'))
  }
}

void fetchUsers()
</script>
