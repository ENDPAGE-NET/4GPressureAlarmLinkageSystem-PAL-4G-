# PAL_4G

## 端口说明

当前项目本地联调默认使用以下端口：

- 后端接口服务：`http://127.0.0.1:8000`
- Web 前端开发服务：`http://127.0.0.1:5173`
- 后端 Swagger：`http://127.0.0.1:8000/docs`

说明：

- 前端通过 `5173` 访问页面，并请求 `8000` 后端接口
- 若需进行前后端联调，请先分别启动 `web` 与 `backend`

## 项目结构

```text
PAL_4G/
├─ backend/        # 后端服务，基于 FastAPI
├─ web/            # Web 管理端，基于 Vue 3 + Vite
├─ miniprogram/    # 小程序端（UniApp）
└─ docs/           # 项目文档
```

## 当前实现范围

本 README 以当前代码状态为准，包含后端、Web 与小程序三端的实现现状。

## 需求实现对比

下表按需求文档中的主要能力进行对照，统一展示后端、Web、小程序当前状态。

| 需求项 | 后端 | Web | 小程序 |
| --- | --- | --- | --- |
| 账号登录与权限区分 | 已完成。支持 `super_admin`、`manager`、`device_user`，包含登录、当前用户、改密、重置密码、安全删除用户 | 已完成。登录页、权限路由、用户信息展示已接通 | 已完成。支持账号密码登录、当前用户获取、登录态恢复、401 失效退出、微信登录与补绑定 |
| 设备管理 | 已完成。支持设备创建、查询、分页、分配负责人、解绑、删除；一个设备一个业务 SN | 已完成。支持设备列表、设备详情、设备控制、状态展示 | 已完成。支持设备列表、按 SN 绑定、移除设备、设备详情与多模块状态查看 |
| 管理者只管理自己名下设备 | 已完成。按 `owner_id` 做数据隔离与权限校验 | 已完成。页面与路由已按角色控制访问 | 已完成。小程序仅面向普通设备账号，不承载管理员菜单 |
| 报警记录查询 | 已完成。支持查询、筛选、分页、恢复 | 已完成。报警列表页、分页跳页、中文文案已接通 | 已完成。支持关键词、报警类型、起止日期筛选与分页加载 |
| 报警联动断开 | 已完成。任一设备报警后，可按同一管理者名下整套设备生成联动断开指令 | 已完成基础展示。可查看报警、指令和联动结果 | 已完成基础展示。首页、设备详情、报警页可查看报警与最近指令结果 |
| 手动控制设备 | 已完成。支持手动继电器指令、执行反馈、补发 | 已完成。设备详情页可执行控制操作 | 已完成。设备详情页支持按模块下发继电器开/关指令 |
| 实时状态展示 | 已完成。支持 WebSocket 事件推送、状态上报、反馈回写 | 已完成。支持实时状态提示与联动展示 | 已完成。首页、设备页、详情页接入 WebSocket，并保留轮询兜底 |
| 设备通信接入 | 已完成基础能力。包含 MQTT 骨架、协议模板管理、状态上报、通信日志；真实设备协议联调仍需最终确认 | 不涉及 | 不涉及 |
| 状态历史与日志 | 已完成。支持设备状态历史、运行日志、操作日志、通信日志 | 已完成。日志中心、运维页面、导出中心已接通 | 未完成 |
| 仪表盘总览 | 已完成。提供聚合接口、统计接口、分页接口 | 已完成。总览卡片、报警分布、指令状态分布、设备状态分布已接通，图表使用 ECharts | 未完成 |
| 分页与跳页 | 已完成。核心列表接口已支持分页 | 已完成。设备、报警、日志等页面支持分页和直接跳页 | 未完成 |
| 运维与调度 | 已完成。支持 APScheduler、离线检测、补发扫描、自动恢复检查、备份与清理 | 已完成。运维页面和调度页面已接通 | 未完成 |
| 中文化提示与交付态文案 | 不涉及前端展示 | 已完成。登录页、顶部状态卡片、错误提示、主要业务文案已改为交付态表达 | 未完成 |
| 自动化测试 | 已完成。`pytest` 已接入，微信相关接口用例可通过 | 已完成。`Vitest` 与 `Playwright` 已接入 | 未完成。当前以微信开发者工具联调与真机测试为主，尚未接入小程序专用自动化测试框架 |

补充说明：

- 当前后端、Web 与小程序首期主流程均已具备联调基础。
- 小程序已完成首期主要业务页面和后端接口对接，但仍缺真机专项回归与自动化测试体系。
- 真实设备协议、有人云 / WH-GM5 实际联调仍需在最终交付前确认闭环。

## 技术栈

- 后端：FastAPI、SQLAlchemy、Pydantic、APScheduler、MQTT
- Web：Vue 3、Vite、TypeScript、Pinia、Vue Router、Element Plus、ECharts

## 启动说明

### 启动后端

```powershell
cd D:\project\code\PAL_4G\backend
D:\uv\venvs\pal_4g\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

### 后端环境变量

后端配置文件位于 `backend/.env`。如需接真实 MQTT 或微信小程序能力，请至少补齐以下配置。

MQTT 配置：

```env
MQTT_ENABLED=true
MQTT_BROKER_HOST=你的MQTT服务器地址
MQTT_BROKER_PORT=1883
MQTT_USERNAME=你的MQTT用户名
MQTT_PASSWORD=你的MQTT密码
MQTT_CLIENT_ID=pal_4g_backend
MQTT_STATUS_TOPIC=pal_4g/status/#
MQTT_FEEDBACK_TOPIC=pal_4g/feedback/#
MQTT_COMMAND_TOPIC_PREFIX=pal_4g/commands
```

微信小程序配置：

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

你需要提供的微信信息：

- 小程序 `AppID`
- 小程序 `AppSecret`
- 订阅消息模板 ID
- 模板字段 key 名
- 消息点击后跳转的小程序页面路径

说明：

- `POST /api/v1/auth/wechat-login` 在开启 `WECHAT_LOGIN_USE_REAL_CODE2SESSION=true` 后，会由后端调用微信 `code2Session`
- `POST /api/v1/auth/wechat-bind` 同时支持真实 `code` 和开发阶段直传 `wechat_open_id`
- `GET /api/v1/notifications/subscription-status`
- `POST /api/v1/notifications/subscribe`
- `POST /api/v1/notifications/unsubscribe`
- `POST /api/v1/jobs/alarm-notification-dispatch` 可手动触发一次报警订阅消息派发

报警订阅消息派发规则：

- 新报警创建后会进入待发送状态
- APScheduler 会按 `ALARM_NOTIFICATION_DISPATCH_INTERVAL_SECONDS` 周期扫描待发送报警
- 只有设备归属用户已绑定微信、用户已开启订阅、系统已配置模板 ID 时才会真正发送
- 派发结果会记录到报警通知状态字段和通信日志中

### 启动 Web

```powershell
cd D:\project\code\PAL_4G\web
npm.cmd install
npm.cmd run dev
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

## 相关文档

- [需求文档](./docs/4G%20%E5%8E%8B%E5%8A%9B%E6%8A%A5%E8%AD%A6%E6%A8%A1%E5%9D%97%20%C2%B7%20%E8%BD%AF%E4%BB%B6%E9%9C%80%E6%B1%82%E6%B2%9F%E9%80%9A%E6%96%87%E6%A1%A3.md)
- [后端开发进度文档](./docs/%E5%90%8E%E7%AB%AF%E5%BC%80%E5%8F%91%E8%BF%9B%E5%BA%A6%E6%96%87%E6%A1%A3.md)
- [Web与后端测试结果报告](./docs/Web%E4%B8%8E%E5%90%8E%E7%AB%AF%E6%B5%8B%E8%AF%95%E7%BB%93%E6%9E%9C%E6%8A%A5%E5%91%8A.md)
