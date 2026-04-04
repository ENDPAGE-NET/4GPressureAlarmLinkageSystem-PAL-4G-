<template>
  <div class="page-shell">
    <div class="page-title">
      <div>
        <h1>{{ t('devices.title') }}</h1>
        <p>{{ t('devices.description') }}</p>
      </div>
      <div class="toolbar__actions">
        <el-button v-if="!isAdmin" type="primary" @click="bindDialogVisible = true">
          {{ t('devices.bindDevice') }}
        </el-button>
        <el-button type="primary" plain @click="fetchDevices">{{ t('common.refresh') }}</el-button>
      </div>
    </div>

    <PanelCard>
        <div class="toolbar">
          <div class="toolbar__filters">
          <el-input v-model="keyword" clearable :placeholder="t('devices.searchPlaceholder')" style="width: 260px" />
        </div>
      </div>
    </PanelCard>

    <PanelCard :title="t('devices.title')" :description="t('devices.description')">
      <DataState
        :loading="loading"
        :error="error"
        :empty="!filteredDevices.length"
        :empty-text="t('common.noData')"
        @retry="fetchDevices"
      >
        <div class="data-table">
          <el-table :data="filteredDevices">
            <el-table-column prop="device_name" :label="t('devices.table.device')" min-width="180" />
            <el-table-column prop="serial_number" :label="t('devices.table.serial')" min-width="160">
              <template #default="{ row }">
                <span class="mono">{{ row.serial_number }}</span>
              </template>
            </el-table-column>
            <el-table-column :label="t('common.status')" min-width="110">
              <template #default="{ row }">
                <StatusPill :value="row.device_status" :mapping="deviceStatusMeta" />
              </template>
            </el-table-column>
            <el-table-column :label="t('devices.table.modules')" min-width="100">
              <template #default="{ row }">{{ row.module_count }}</template>
            </el-table-column>
            <el-table-column :label="t('devices.table.online')" min-width="100">
              <template #default="{ row }">{{ row.online_module_count }}</template>
            </el-table-column>
            <el-table-column :label="t('devices.table.offline')" min-width="100">
              <template #default="{ row }">{{ row.offline_module_count }}</template>
            </el-table-column>
            <el-table-column v-if="isAdmin" :label="t('devices.owner')" min-width="140">
              <template #default="{ row }">{{ resolveOwnerName(row.owner_id) }}</template>
            </el-table-column>
            <el-table-column v-if="isAdmin" :label="t('devices.group')" min-width="160">
              <template #default="{ row }">{{ resolveGroupName(row.linkage_group_id) }}</template>
            </el-table-column>
            <el-table-column :label="t('devices.table.latestAlarm')" min-width="140">
              <template #default="{ row }">{{ row.latest_alarm_type || '--' }}</template>
            </el-table-column>
            <el-table-column :label="t('devices.table.latestAlarmTime')" min-width="180">
              <template #default="{ row }">{{ formatDateTime(row.latest_alarm_time) }}</template>
            </el-table-column>
            <el-table-column :label="t('common.actions')" min-width="240" fixed="right">
              <template #default="{ row }">
                <el-button type="primary" link @click="router.push(`/devices/${row.device_id}`)">
                  {{ t('common.details') }}
                </el-button>
                <el-button v-if="isAdmin" link type="warning" @click="openOwnerDialog(row)">
                  {{ t('devices.assignOwner') }}
                </el-button>
                <el-button v-if="isAdmin" link @click="openGroupDialog(row)">
                  {{ t('devices.assignGroup') }}
                </el-button>
                <el-button v-else link type="danger" @click="handleUnbind(row.device_id)">
                  {{ t('devices.unbind') }}
                </el-button>
              </template>
            </el-table-column>
          </el-table>
        </div>
      </DataState>
    </PanelCard>

    <el-dialog v-model="bindDialogVisible" :title="t('devices.bindDialogTitle')" width="460px">
      <el-form label-position="top">
        <el-alert
          :title="t('devices.bindDescription')"
          type="info"
          :closable="false"
          show-icon
          style="margin-bottom: 16px"
        />
        <el-form-item :label="t('devices.bindBySerial')" required>
          <el-input v-model="bindForm.serial_number" :placeholder="t('devices.bindSerialPlaceholder')" />
        </el-form-item>
        <el-form-item :label="`${t('devices.bindName')} (${t('common.optional')})`">
          <el-input v-model="bindForm.name" :placeholder="t('devices.bindNamePlaceholder')" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="bindDialogVisible = false">{{ t('common.cancel') }}</el-button>
        <el-button type="primary" :loading="submitting" @click="submitBind">{{ t('common.confirm') }}</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="ownerDialogVisible" :title="t('devices.assignOwner')" width="420px">
      <el-form label-position="top">
        <el-form-item :label="t('devices.owner')">
          <el-select v-model="ownerForm.owner_id" clearable style="width: 100%">
            <el-option v-for="user in users" :key="user.id" :label="user.username" :value="user.id" />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="ownerDialogVisible = false">{{ t('common.cancel') }}</el-button>
        <el-button type="primary" :loading="submitting" @click="submitOwner">{{ t('common.save') }}</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="groupDialogVisible" :title="t('devices.assignGroup')" width="420px">
      <el-form label-position="top">
        <el-form-item :label="t('devices.group')">
          <el-select v-model="groupForm.linkage_group_id" clearable style="width: 100%">
            <el-option v-for="group in groups" :key="group.id" :label="group.name" :value="group.id" />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="groupDialogVisible = false">{{ t('common.cancel') }}</el-button>
        <el-button type="primary" :loading="submitting" @click="submitGroup">{{ t('common.save') }}</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ElMessage } from 'element-plus'
import { computed, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'

import {
  assignDeviceGroupApi,
  assignDeviceOwnerApi,
  bindDeviceApi,
  getDeviceGroupsApi,
  getDeviceMonitoringApi,
  getDevicesApi,
  unbindDeviceApi,
} from '@/api/devices'
import { getUsersApi } from '@/api/users'
import DataState from '@/components/DataState.vue'
import PanelCard from '@/components/PanelCard.vue'
import StatusPill from '@/components/StatusPill.vue'
import { useI18n } from '@/composables/useI18n'
import { useAuthStore } from '@/stores/auth'
import type { DeviceGroupRead, DeviceMonitoringItem, DeviceRead, UserRead } from '@/types/domain'
import { formatDateTime } from '@/utils/format'
import { deviceStatusMeta } from '@/utils/status'

type DeviceRow = DeviceMonitoringItem & {
  owner_id: number | null
  linkage_group_id: number | null
}

const { t } = useI18n()
const authStore = useAuthStore()
const router = useRouter()
const loading = ref(true)
const error = ref('')
const keyword = ref('')
const devices = ref<DeviceRow[]>([])
const users = ref<UserRead[]>([])
const groups = ref<DeviceGroupRead[]>([])
const currentDeviceId = ref<number | null>(null)
const ownerDialogVisible = ref(false)
const groupDialogVisible = ref(false)
const bindDialogVisible = ref(false)
const submitting = ref(false)

const bindForm = reactive({
  serial_number: '',
  name: '',
})

const ownerForm = reactive({
  owner_id: undefined as number | undefined,
})

const groupForm = reactive({
  linkage_group_id: undefined as number | undefined,
})

const isAdmin = computed(() => authStore.profile?.role === 'super_admin')

const filteredDevices = computed(() => {
  const search = keyword.value.trim().toLowerCase()
  if (!search) return devices.value
  return devices.value.filter(
    (item) =>
      item.device_name.toLowerCase().includes(search) ||
      item.serial_number.toLowerCase().includes(search),
  )
})

function resolveOwnerName(ownerId: number | null) {
  if (!ownerId) return '--'
  return users.value.find((item) => item.id === ownerId)?.username || `#${ownerId}`
}

function resolveGroupName(groupId: number | null) {
  if (!groupId) return '--'
  return groups.value.find((item) => item.id === groupId)?.name || `#${groupId}`
}

async function fetchDevices() {
  loading.value = true
  error.value = ''
  try {
    const requests: Promise<any>[] = [getDeviceMonitoringApi(), getDevicesApi()]
    if (isAdmin.value) {
      requests.push(getUsersApi(), getDeviceGroupsApi())
    }
    const [monitoring, rawDevices, userData, groupData] = await Promise.all(requests)
    const deviceMap = new Map<number, DeviceRead>((rawDevices as DeviceRead[]).map((item) => [item.id, item]))
    devices.value = (monitoring as DeviceMonitoringItem[]).map((item) => ({
      ...item,
      owner_id: deviceMap.get(item.device_id)?.owner_id ?? null,
      linkage_group_id: deviceMap.get(item.device_id)?.linkage_group_id ?? null,
    }))
    users.value = ((userData as UserRead[]) || []).filter((item) => item.role !== 'super_admin')
    groups.value = (groupData as DeviceGroupRead[]) || []
  } catch (err: any) {
    error.value = err.response?.data?.detail || t('devices.loadError')
  } finally {
    loading.value = false
  }
}

function openOwnerDialog(row: DeviceRow) {
  currentDeviceId.value = row.device_id
  ownerForm.owner_id = row.owner_id || undefined
  ownerDialogVisible.value = true
}

function openGroupDialog(row: DeviceRow) {
  currentDeviceId.value = row.device_id
  groupForm.linkage_group_id = row.linkage_group_id || undefined
  groupDialogVisible.value = true
}

async function submitOwner() {
  if (!currentDeviceId.value) return
  submitting.value = true
  try {
    if (ownerForm.owner_id == null) {
      await unbindDeviceApi(currentDeviceId.value)
    } else {
      await assignDeviceOwnerApi(currentDeviceId.value, ownerForm.owner_id)
    }
    ElMessage.success(t('devices.ownerUpdated'))
    ownerDialogVisible.value = false
    await fetchDevices()
  } catch (err: any) {
    ElMessage.error(err.response?.data?.detail || t('devices.ownerUpdateFailed'))
  } finally {
    submitting.value = false
  }
}

async function submitGroup() {
  if (!currentDeviceId.value) return
  submitting.value = true
  try {
    await assignDeviceGroupApi(currentDeviceId.value, groupForm.linkage_group_id ?? null)
    ElMessage.success(t('devices.groupUpdated'))
    groupDialogVisible.value = false
    await fetchDevices()
  } catch (err: any) {
    ElMessage.error(err.response?.data?.detail || t('devices.groupUpdateFailed'))
  } finally {
    submitting.value = false
  }
}

async function submitBind() {
  const serial = bindForm.serial_number.trim()
  if (!serial) {
    ElMessage.error(t('devices.validations.serialRequired'))
    return
  }

  submitting.value = true
  try {
    await bindDeviceApi({
      serial_number: serial,
      name: bindForm.name.trim() || undefined,
    })
    ElMessage.success(t('devices.bindSuccess'))
    bindDialogVisible.value = false
    bindForm.serial_number = ''
    bindForm.name = ''
    await fetchDevices()
  } catch (err: any) {
    ElMessage.error(err.response?.data?.detail || t('devices.bindError'))
  } finally {
    submitting.value = false
  }
}

async function handleUnbind(deviceId: number) {
  try {
    const confirmed = window.confirm(t('devices.unbindConfirm'))
    if (!confirmed) return
    await unbindDeviceApi(deviceId)
    ElMessage.success(t('devices.unbindSuccess'))
    await fetchDevices()
  } catch (err: any) {
    ElMessage.error(err.response?.data?.detail || t('devices.unbindError'))
  }
}

void fetchDevices()
</script>
