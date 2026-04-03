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
