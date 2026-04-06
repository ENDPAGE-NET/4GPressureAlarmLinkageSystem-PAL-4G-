import { request } from '@/api/http'

export function getSubscriptionStatusApi() {
  return request({
    url: '/notifications/subscription-status',
    method: 'GET',
  })
}

export function subscribeNotificationsApi(payload) {
  return request({
    url: '/notifications/subscribe',
    method: 'POST',
    data: payload,
    header: {
      'Content-Type': 'application/json',
    },
  })
}

export function unsubscribeNotificationsApi() {
  return request({
    url: '/notifications/unsubscribe',
    method: 'POST',
  })
}
