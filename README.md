# PAL_4G

4G 压力报警联动控制系统，当前仓库包含后端、Web 管理端和微信小程序三端代码。

## 项目结构

```text
PAL_4G/
├── backend/        # 后端服务，FastAPI + SQLite
├── web/            # Web 管理端，Vue 3 + Vite + Element Plus
├── miniprogram/    # 微信小程序端，UniApp + Vue 3
├── deploy/         # 部署模板（Nginx、systemd、EMQX）
└── docs/           # 项目文档与设备对接资料
```

## 本地开发

### 端口

| 服务 | 地址 | 说明 |
|------|------|------|
| 后端 API | `http://127.0.0.1:8001` | FastAPI |
| 后端 Swagger | `http://127.0.0.1:8001/docs` | 接口文档 |
| Web 前端 | `http://127.0.0.1:5173` | Vite 开发服务器，`/api` 自动代理到后端 |

### 启动后端

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # 按需修改配置
python -m uvicorn app.main:app --host 127.0.0.1 --port 8001
```

### 启动 Web

```bash
cd web
npm install
npm run dev
```

### 启动小程序开发

```bash
cd miniprogram
npm install
```

然后使用 HBuilderX 或 UniApp CLI 编译到微信小程序，再在微信开发者工具中打开编译产物。

小程序接口说明：

- 小程序后端接口端口同样使用 `8001`
- 小程序配置支持通过 `SERVICE_ORIGIN` 动态拼接：
  - API：`{SERVICE_ORIGIN}/api/v1`
  - WebSocket：`{SERVICE_ORIGIN}/api/v1/ws/events`
- 真机调试时 `SERVICE_ORIGIN` 需改为可访问的 HTTPS 地址

## 环境变量

后端配置文件位于 `backend/.env`，参考 `backend/.env.example`。关键配置项：

### MQTT

```env
MQTT_ENABLED=true
MQTT_BROKER_HOST=your-mqtt-host
MQTT_BROKER_PORT=1883
MQTT_USERNAME=your-mqtt-username
MQTT_PASSWORD=your-mqtt-password
MQTT_CLIENT_ID=pal_4g_backend
```

### 微信小程序

```env
WECHAT_ENABLED=true
WECHAT_LOGIN_USE_REAL_CODE2SESSION=true
WECHAT_APP_ID=your-wechat-app-id
WECHAT_APP_SECRET=your-wechat-app-secret
WECHAT_SUBSCRIBE_TEMPLATE_ID=your-template-id
```

## 测试

```bash
# 后端
cd backend && python -m pytest -q

# Web 单元测试
cd web && npm run test

# Web 端到端测试
cd web && npm run test:e2e
```

## 部署

部署目标环境为 Linux + 宝塔面板，详见 `deploy/` 目录和 `docs/部署文档.md`。

核心组件：

| 组件 | 端口 | 说明 |
|------|------|------|
| Nginx | 80/443 | 反代 Web + API，宝塔面板配置 |
| 后端 API | 8001 | uvicorn，通过 systemd 管理 |
| EMQX Broker | 1883/8883 | MQTT，Docker 部署 |

设备对接流程见 `docs/设备对接指南.md`。

## 需求完成情况

以下对比以需求文档 `docs/4G 压力报警模块 · 软件需求沟通文档.md` 为准。

| 需求项 | 后端 | Web | 小程序 |
| --- | --- | --- | --- |
| 账号登录与权限区分 | 已完成 | 已完成 | 已完成 |
| 设备状态查看 | 已完成 | 已完成 | 已完成 |
| 报警记录查询 | 已完成 | 已完成 | 已完成 |
| 报警联动 | 已完成 | 已完成 | 已完成 |
| 手动控制继电器 | 已完成 | 已完成 | 已完成 |
| 设备绑定与移除 | 已完成 | 已完成 | 已完成 |
| 超级管理员管理 | 已完成 | 已完成 | 不涉及 |
| 实时状态刷新 | 已完成 (WebSocket) | 已完成 | 已完成 |
| 微信消息推送 | 已完成 | 不涉及 | 已完成（需真机验收） |
| MQTT 设备接入 | 已完成 | 不涉及 | 不涉及 |
| 自动化测试 | pytest | Vitest + Playwright | 待补充 |
