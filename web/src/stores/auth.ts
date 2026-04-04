import { computed, ref } from 'vue'
import { defineStore } from 'pinia'

import { getCurrentUserApi, loginApi } from '@/api/auth'
import { tokenStorage } from '@/api/http'
import type { UserProfile } from '@/types/domain'

export const useAuthStore = defineStore('auth', () => {
  const token = ref<string | null>(tokenStorage.get())
  const profile = ref<UserProfile | null>(null)
  const bootstrapped = ref(false)
  const loading = ref(false)

  const isAuthenticated = computed(() => Boolean(token.value && profile.value))

  function setToken(nextToken: string | null) {
    token.value = nextToken
    if (nextToken) {
      tokenStorage.set(nextToken)
    } else {
      tokenStorage.clear()
    }
  }

  async function fetchProfile() {
    profile.value = await getCurrentUserApi()
    return profile.value
  }

  async function initialize() {
    if (bootstrapped.value) {
      return
    }

    if (!token.value) {
      bootstrapped.value = true
      return
    }

    try {
      await fetchProfile()
    } catch {
      setToken(null)
      profile.value = null
    } finally {
      bootstrapped.value = true
    }
  }

  async function login(username: string, password: string) {
    loading.value = true
    try {
      const data = await loginApi(username, password)
      setToken(data.access_token)
      await fetchProfile()
    } finally {
      loading.value = false
      bootstrapped.value = true
    }
  }

  function logout() {
    setToken(null)
    profile.value = null
    bootstrapped.value = true
  }

  return {
    bootstrapped,
    isAuthenticated,
    loading,
    profile,
    token,
    fetchProfile,
    initialize,
    login,
    logout,
  }
})
