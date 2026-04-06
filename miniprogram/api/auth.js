import { request } from '@/api/http'

export function loginApi(username, password) {
  const payload = `username=${encodeURIComponent(username)}&password=${encodeURIComponent(password)}`
  return request({
    url: '/auth/login',
    method: 'POST',
    data: payload,
    header: {
      'Content-Type': 'application/x-www-form-urlencoded',
    },
  })
}

export function getCurrentUserApi() {
  return request({
    url: '/auth/me',
    method: 'GET',
  })
}

export function wechatLoginApi(payload) {
  return request({
    url: '/auth/wechat-login',
    method: 'POST',
    data: payload,
    header: {
      'Content-Type': 'application/json',
    },
  })
}

export function wechatBindApi(payload) {
  return request({
    url: '/auth/wechat-bind',
    method: 'POST',
    data: payload,
    header: {
      'Content-Type': 'application/json',
    },
  })
}
