# PAL_4G

4G 压力报警联动控制系统项目工作区。

## 项目概述

根据 [docs/4G 压力报警模块 · 软件需求沟通文档.md](./docs/4G%20压力报警模块%20·%20软件需求沟通文档.md) 与 [docs/4G 压力报警模块系统技术栈选择.md](./docs/4G%20压力报警模块系统技术栈选择.md)，本项目包含以下核心交付内容：

- Web 管理后台
- 微信小程序客户端
- 服务端程序

## 目录结构

```text
PAL_4G/
├── backend/        # 后端服务，推荐使用 FastAPI
├── web/            # Web 管理后台，推荐使用 Vue 3 + Vite
├── miniprogram/    # 微信小程序端，推荐使用 UniApp
└── docs/           # 项目需求与技术栈文档
```

## 技术栈约定

- `backend`：FastAPI、Uvicorn、SQLAlchemy、aiosqlite、JWT、MQTT
- `web`：Vue 3、Vite、TypeScript、Pinia、Vue Router、Element Plus、ECharts
- `miniprogram`：UniApp、Vue 3、uView Plus、Pinia

## 当前状态

当前仓库已完成基础目录初始化，后续可分别在 `backend`、`web`、`miniprogram` 下继续搭建具体工程。

## 后端实现

当前 `backend` 已完成第一版核心后端能力，主要包括：

- 账号体系：JWT 登录鉴权、当前用户查询、用户管理、密码修改与重置
- 设备管理：设备、模块、设备分组、设备绑定与归属管理
- 报警联动：报警记录、同组联动、离线补发、报警恢复、人工控制优先
- 通信接入：HTTP 状态上报、MQTT 状态消息接入、设备反馈回写、协议映射准备层
- 运维支撑：APScheduler 定时任务、离线检测、告警恢复检查、日志落库、数据库备份
- 业务接口：Web 管理后台与微信小程序所需的 dashboard 聚合接口、导出接口与日志查询接口

后端核心目录：

- `backend/app/api/`：接口路由层
- `backend/app/models/`：数据模型
- `backend/app/schemas/`：请求与响应结构
- `backend/app/services/`：业务逻辑与调度、协议、联动实现
- `backend/tests/`：本地 `pytest` 测试

当前后端已可作为 Web 管理后台和微信小程序联调的第一版服务端基础。
