# PAL_4G

4G 压力报警联动控制系统，当前仓库包含后端、Web 管理端和微信小程序三端代码。

## 项目结构

```text
PAL_4G/
├─ backend/        # 后端服务，FastAPI
├─ web/            # Web 管理端，Vue 3 + Vite
├─ miniprogram/    # 微信小程序端，UniApp + Vue 3
└─ docs/           # 项目文档与联调资料
```

## 本地端口

- 后端接口服务：`http://127.0.0.1:8001`
- 后端 Swagger：`http://127.0.0.1:8001/docs`
- Web 前端开发服务：`http://127.0.0.1:5173`

## 当前完成情况

### 后端

- 已完成账号登录、鉴权、设备管理、报警记录、继电器控制、联动断开、WebSocket 实时事件。
- 已具备 MQTT 接入基础能力、协议模板管理、状态上报处理、报警处理、反馈回写。
- 已具备微信登录、微信绑定、订阅状态、订阅开关、报警通知派发相关接口。
- 已接入 `pytest`，现有后端和微信相关接口可做自动化验证。

### Web

- 已完成登录、总览、设备列表、设备详情、报警列表、日志中心、运维与调度等主要页面。
- 已与后端主接口完成对接，支持分页、筛选、图表展示和联动结果查看。
- 已接入 `Vitest` 与 `Playwright`。

### 小程序

当前小程序不再是骨架工程，首期主链路已经落地，并已对接后端真实接口。

已完成页面：

- 登录页
- 首页
- 我的设备页
- 设备详情页
- 设备绑定页
- 报警页
- 我的页
- 设置页

已完成能力：

- 账号密码登录、登录态恢复、401 失效退出
- 微信登录入口、微信绑定入口
- 首页摘要、最近报警、设备快捷入口
- 我的设备列表、本地搜索、进入详情
- 设备详情与多模块状态展示
- 按模块远程控制继电器开关
- SN 绑定设备、移除设备
- 报警分页、关键词/类型/日期筛选
- 修改密码、退出登录
- WebSocket 实时更新 + 轮询兜底
- 订阅状态查询、订阅/退订入口

当前仍未完成或仍需联调验收的部分：

- 小程序专用自动化测试体系尚未正式接入
- 微信真实 `AppID/AppSecret`、订阅模板和真机授权链路仍需最终验收
- 真机网络联调依赖 HTTPS 隧道或正式可访问域名
- 真实硬件设备 MQTT 接入仍需结合 Broker、现场参数和真实报文验证闭环

## 小程序当前对接接口

小程序当前已接入以下后端接口：

- `POST /api/v1/auth/login`
- `GET /api/v1/auth/me`
- `POST /api/v1/auth/wechat-login`
- `POST /api/v1/auth/wechat-bind`
- `GET /api/v1/dashboard/my/home`
- `GET /api/v1/dashboard/my/devices`
- `GET /api/v1/dashboard/my/alarms`
- `GET /api/v1/dashboard/alarms/page`
- `GET /api/v1/devices/{device_id}`
- `GET /api/v1/dashboard/devices/{device_id}`
- `POST /api/v1/relay-commands`
- `POST /api/v1/devices/bind`
- `POST /api/v1/devices/{device_id}/unbind`
- `POST /api/v1/users/me/change-password`
- `GET /api/v1/notifications/subscription-status`
- `POST /api/v1/notifications/subscribe`
- `POST /api/v1/notifications/unsubscribe`
- `GET /api/v1/ws/events`

## 启动说明

### 启动后端

```powershell
cd D:\project\code\PAL_4G\backend
D:\uv\venvs\pal_4g\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8001
```

如果要做小程序真机调试，建议改为：

```powershell
cd D:\project\code\PAL_4G\backend
D:\uv\venvs\pal_4g\Scripts\python.exe -m uvicorn app.main:app --host 0.0.0.0 --port 8001
```

### 启动 Web

```powershell
cd D:\project\code\PAL_4G\web
npm.cmd install
npm.cmd run dev
```

### 启动小程序开发

```powershell
cd D:\project\code\PAL_4G\miniprogram
npm.cmd install
```

然后使用 HBuilderX 或 UniApp CLI 编译到微信小程序，再在微信开发者工具中打开编译产物。

## 环境变量

后端配置文件位于 `backend/.env`。如需接入真实 MQTT 或微信能力，至少补齐以下配置。

### MQTT

```env
MQTT_ENABLED=true
MQTT_BROKER_HOST=你的MQTT服务器地址
MQTT_BROKER_PORT=1883
MQTT_USERNAME=你的MQTT用户名
MQTT_PASSWORD=你的MQTT密码
MQTT_CLIENT_ID=pal_4g_backend
```

### 微信小程序

```env
WECHAT_ENABLED=true
WECHAT_LOGIN_USE_REAL_CODE2SESSION=true
WECHAT_APP_ID=你的小程序AppID
WECHAT_APP_SECRET=你的小程序AppSecret
WECHAT_SUBSCRIBE_TEMPLATE_ID=报警订阅消息模板ID
WECHAT_SUBSCRIBE_PAGE=pages/alarms/index
WECHAT_SUBSCRIBE_MINIPROGRAM_STATE=formal
WECHAT_SUBSCRIBE_LANG=zh_CN
WECHAT_SUBSCRIBE_FIELD_ALARM_TYPE=thing1
WECHAT_SUBSCRIBE_FIELD_DEVICE_NAME=thing2
WECHAT_SUBSCRIBE_FIELD_TRIGGER_TIME=time3
WECHAT_SUBSCRIBE_FIELD_REMARK=thing4
ALARM_NOTIFICATION_DISPATCH_INTERVAL_SECONDS=60
```

## 测试说明

### 后端测试

```powershell
cd D:\project\code\PAL_4G\backend
D:\uv\venvs\pal_4g\Scripts\python.exe -m pytest -q
```

### Web 单元测试

```powershell
cd D:\project\code\PAL_4G\web
npm.cmd run test
```

### Web 端到端测试

```powershell
cd D:\project\code\PAL_4G\web
npm.cmd run test:e2e
```

### 小程序测试建议

- 接口与服务逻辑：继续使用后端 `pytest`
- 小程序页面与交互：微信开发者工具联调
- 真机能力：真机预览 / 真机调试
- 若后续补自动化：优先考虑 `miniprogram-automator` 或 `uni-automator`

## 真机调试说明

小程序真机调试不要直接依赖 `127.0.0.1`。如果电脑和手机局域网互通不稳定，建议使用 HTTPS 隧道方案，例如 `cloudflared`，再把小程序接口地址切到临时 HTTPS 域名。

相关经验文档见：

- [微信小程序开发文档](./docs/%E5%BE%AE%E4%BF%A1%E5%B0%8F%E7%A8%8B%E5%BA%8F%E5%BC%80%E5%8F%91%E6%96%87%E6%A1%A3.md)
- [小程序需求实现验收清单](./docs/%E5%B0%8F%E7%A8%8B%E5%BA%8F%E9%9C%80%E6%B1%82%E5%AE%9E%E7%8E%B0%E9%AA%8C%E6%94%B6%E6%B8%85%E5%8D%95.md)
- [真机接入资料清单（硬件直接对接网站）](./docs/%E7%9C%9F%E6%9C%BA%E6%8E%A5%E5%85%A5%E8%B5%84%E6%96%99%E6%B8%85%E5%8D%95%EF%BC%88%E7%A1%AC%E4%BB%B6%E7%9B%B4%E6%8E%A5%E5%AF%B9%E6%8E%A5%E7%BD%91%E7%AB%99%EF%BC%89.md)
