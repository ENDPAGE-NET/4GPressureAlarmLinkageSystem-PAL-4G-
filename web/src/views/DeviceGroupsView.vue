<template>
  <div class="page-shell">
    <div class="page-title">
      <div>
        <h1>{{ t('groups.title') }}</h1>
        <p>{{ t('groups.description') }}</p>
      </div>
      <el-button type="primary" @click="openCreateDialog">{{ t('groups.createGroup') }}</el-button>
    </div>

    <PanelCard :title="t('groups.title')" :description="t('groups.description')">
      <DataState :loading="loading" :error="error" :empty="!groups.length" @retry="fetchAll">
        <div class="data-table">
          <el-table :data="groups">
            <el-table-column prop="name" :label="t('groups.groupName')" min-width="180" />
            <el-table-column prop="description" :label="t('groups.descriptionLabel')" min-width="220" show-overflow-tooltip />
            <el-table-column prop="owner_id" :label="t('groups.owner')" min-width="120">
              <template #default="{ row }">
                {{ resolveOwnerName(row.owner_id) }}
              </template>
            </el-table-column>
            <el-table-column prop="device_count" :label="t('groups.deviceCount')" min-width="110" />
            <el-table-column :label="t('groups.deviceIds')" min-width="180">
              <template #default="{ row }">
                {{ row.device_ids.length ? row.device_ids.join(', ') : '--' }}
              </template>
            </el-table-column>
            <el-table-column :label="t('common.actions')" min-width="170" fixed="right">
              <template #default="{ row }">
                <el-button link type="primary" @click="openEditDialog(row)">{{ t('common.edit') }}</el-button>
                <el-button link type="danger" @click="removeGroup(row.id)">{{ t('common.delete') }}</el-button>
              </template>
            </el-table-column>
          </el-table>
        </div>
      </DataState>
    </PanelCard>

    <el-dialog v-model="dialogVisible" :title="currentGroup ? t('groups.editGroup') : t('groups.createGroup')" width="460px">
      <el-form ref="formRef" :model="form" :rules="rules" label-position="top">
        <el-form-item :label="t('groups.groupName')" prop="name">
          <el-input v-model="form.name" />
        </el-form-item>
        <el-form-item :label="t('groups.descriptionLabel')" prop="description">
          <el-input v-model="form.description" type="textarea" :rows="3" />
        </el-form-item>
        <el-form-item :label="t('groups.owner')" prop="owner_id">
          <el-select v-model="form.owner_id" clearable style="width: 100%">
            <el-option
              v-for="user in ownerOptions"
              :key="user.id"
              :label="user.username"
              :value="user.id"
            />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">{{ t('common.cancel') }}</el-button>
        <el-button type="primary" :loading="submitting" @click="submitGroup">{{ t('common.save') }}</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import type { FormInstance, FormRules } from 'element-plus'
import { ElMessage, ElMessageBox } from 'element-plus'
import { computed, reactive, ref } from 'vue'

import { useI18n } from '@/composables/useI18n'
import DataState from '@/components/DataState.vue'
import PanelCard from '@/components/PanelCard.vue'
import {
  createDeviceGroupApi,
  deleteDeviceGroupApi,
  getDeviceGroupsApi,
  updateDeviceGroupApi,
} from '@/api/devices'
import { getUsersApi } from '@/api/users'
import type { DeviceGroupRead, UserRead } from '@/types/domain'

const { t } = useI18n()
const loading = ref(true)
const error = ref('')
const groups = ref<DeviceGroupRead[]>([])
const users = ref<UserRead[]>([])
const dialogVisible = ref(false)
const submitting = ref(false)
const currentGroup = ref<DeviceGroupRead | null>(null)
const formRef = ref<FormInstance>()

const form = reactive({
  name: '',
  description: '',
  owner_id: undefined as number | undefined,
})

const rules: FormRules<typeof form> = {
  name: [{ required: true, message: t('groups.validations.nameRequired'), trigger: 'blur' }],
}

const ownerOptions = computed(() => users.value)

function resolveOwnerName(ownerId: number | null) {
  if (!ownerId) return '--'
  return users.value.find((item) => item.id === ownerId)?.username || `#${ownerId}`
}

async function fetchAll() {
  loading.value = true
  error.value = ''
  try {
    const [groupData, userData] = await Promise.all([getDeviceGroupsApi(), getUsersApi()])
    groups.value = groupData
    users.value = userData
  } catch (err: any) {
    error.value = err.response?.data?.detail || t('groups.loadError')
  } finally {
    loading.value = false
  }
}

function openCreateDialog() {
  currentGroup.value = null
  form.name = ''
  form.description = ''
  form.owner_id = undefined
  dialogVisible.value = true
}

function openEditDialog(group: DeviceGroupRead) {
  currentGroup.value = group
  form.name = group.name
  form.description = group.description || ''
  form.owner_id = group.owner_id || undefined
  dialogVisible.value = true
}

async function submitGroup() {
  const valid = await formRef.value?.validate().catch(() => false)
  if (!valid) return
  submitting.value = true
  try {
    if (currentGroup.value) {
      await updateDeviceGroupApi(currentGroup.value.id, form)
      ElMessage.success(t('groups.updateSuccess'))
    } else {
      await createDeviceGroupApi(form)
      ElMessage.success(t('groups.createSuccess'))
    }
    dialogVisible.value = false
    await fetchAll()
  } catch (err: any) {
    ElMessage.error(err.response?.data?.detail || t('groups.saveFailed'))
  } finally {
    submitting.value = false
  }
}

async function removeGroup(groupId: number) {
  try {
    await ElMessageBox.confirm(t('groups.deleteConfirm'), t('groups.deleteTitle'), {
      type: 'warning',
    })
    await deleteDeviceGroupApi(groupId)
    ElMessage.success(t('groups.deleteSuccess'))
    await fetchAll()
  } catch (err: any) {
    if (err === 'cancel') return
    ElMessage.error(err.response?.data?.detail || t('groups.deleteFailed'))
  }
}

void fetchAll()
</script>
