import { APP_CONFIG } from '@/utils/config'

export async function requestWechatLoginCode() {
  if (!APP_CONFIG.WECHAT_LOGIN_ENABLED) {
    throw new Error('\u5f53\u524d\u9879\u76ee\u5c1a\u672a\u542f\u7528\u5fae\u4fe1\u767b\u5f55\uff0c\u8bf7\u5148\u4f7f\u7528\u8d26\u53f7\u5bc6\u7801\u767b\u5f55')
  }

  if (typeof uni.login !== 'function') {
    throw new Error('\u5f53\u524d\u73af\u5883\u4e0d\u652f\u6301\u5fae\u4fe1\u6388\u6743\u767b\u5f55\uff0c\u8bf7\u5728\u5fae\u4fe1\u5c0f\u7a0b\u5e8f\u4e2d\u4f7f\u7528')
  }

  const result = await new Promise((resolve, reject) => {
    uni.login({
      provider: 'weixin',
      success: resolve,
      fail: reject,
    })
  })

  if (!result?.code) {
    throw new Error('\u672a\u83b7\u53d6\u5230\u5fae\u4fe1\u767b\u5f55\u51ed\u8bc1\uff0c\u8bf7\u7a0d\u540e\u91cd\u8bd5')
  }

  return result.code
}
