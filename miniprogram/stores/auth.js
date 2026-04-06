import { computed, reactive, readonly } from 'vue'

import { getCurrentUserApi, loginApi, wechatLoginApi } from '@/api/auth'
import {
  clearSessionStorage,
  clearProfile,
  getProfile,
  getToken,
  setProfile,
  setToken,
} from '@/utils/storage'

const state = reactive({
  token: getToken(),
  profile: getProfile(),
  bootstrapped: false,
  loading: false,
})

function applySession(token, profile) {
  state.token = token
  state.profile = profile

  if (token) {
    setToken(token)
  } else {
    clearSessionStorage()
  }

  if (profile) {
    setProfile(profile)
  } else {
    clearProfile()
  }
}

export function useAuthStore() {
  const isAuthenticated = computed(() => Boolean(state.token && state.profile))

  async function fetchProfile() {
    const profile = await getCurrentUserApi()
    applySession(state.token, profile)
    return profile
  }

  async function initialize(force = false) {
    if (state.bootstrapped && !force) {
      return
    }

    if (!state.token) {
      state.bootstrapped = true
      state.profile = null
      return
    }

    try {
      await fetchProfile()
    } catch {
      logout(false)
    } finally {
      state.bootstrapped = true
    }
  }

  async function login(username, password) {
    state.loading = true
    try {
      const tokenResponse = await loginApi(username, password)
      applySession(tokenResponse.access_token, null)
      await fetchProfile()
      state.bootstrapped = true
    } finally {
      state.loading = false
    }
  }

  async function loginWithWechat(identityPayload) {
    state.loading = true
    try {
      const tokenResponse = await wechatLoginApi(identityPayload)
      applySession(tokenResponse.access_token, null)
      await fetchProfile()
      state.bootstrapped = true
    } finally {
      state.loading = false
    }
  }

  function logout(showToast = false) {
    state.token = ''
    state.profile = null
    state.bootstrapped = true
    clearSessionStorage()

    if (showToast) {
      uni.showToast({
        title: '登录已失效，请重新登录',
        icon: 'none',
      })
    }
  }

  return {
    state: readonly(state),
    isAuthenticated,
    initialize,
    fetchProfile,
    login,
    loginWithWechat,
    logout,
  }
}
