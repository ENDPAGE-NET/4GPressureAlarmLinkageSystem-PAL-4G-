import { http } from './http'
import type { TokenResponse, UserProfile } from '@/types/domain'

export async function loginApi(username: string, password: string) {
  const body = new URLSearchParams({
    username,
    password,
  })
  const { data } = await http.post<TokenResponse>('/auth/login', body, {
    headers: {
      'Content-Type': 'application/x-www-form-urlencoded',
    },
  })
  return data
}

export async function getCurrentUserApi() {
  const { data } = await http.get<UserProfile>('/auth/me')
  return data
}
