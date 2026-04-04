import { http } from './http'
import type {
  ChangePasswordPayload,
  UserCreatePayload,
  UserProfile,
  UserRead,
  UserResetPasswordPayload,
  UserUpdatePayload,
} from '@/types/domain'

export async function getUsersApi() {
  const { data } = await http.get<UserRead[]>('/users')
  return data
}

export async function createUserApi(payload: UserCreatePayload) {
  const { data } = await http.post<UserRead>('/users', payload)
  return data
}

export async function updateUserApi(userId: number, payload: UserUpdatePayload) {
  const { data } = await http.patch<UserRead>(`/users/${userId}`, payload)
  return data
}

export async function resetUserPasswordApi(userId: number, payload: UserResetPasswordPayload) {
  const { data } = await http.post<UserRead>(`/users/${userId}/reset-password`, payload)
  return data
}

export async function changePasswordApi(payload: ChangePasswordPayload) {
  const { data } = await http.post<UserProfile>('/users/me/change-password', payload)
  return data
}
