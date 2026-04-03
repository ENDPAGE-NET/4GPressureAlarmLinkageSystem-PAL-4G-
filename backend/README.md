# Backend

本目录为 4G 压力报警联动控制系统后端服务。

## 当前骨架

- `app/main.py`：FastAPI 入口
- `app/core/`：配置等核心基础能力
- `app/db/`：数据库连接与基类
- `app/api/`：路由层
- `app/models/`：数据模型
- `app/schemas/`：请求响应模型
- `app/services/`：业务服务层

## 本地启动

```bash
pip install -r requirements.txt
uvicorn app.main:app --reload
```

## 当前已提供

- 根路由 `/`
- 健康检查 `/api/v1/health`
- SQLite 异步数据库初始化能力

## 下一步建议

- 补充用户、设备、模块、报警记录等核心模型
- 增加鉴权与用户管理接口
- 接入 MQTT 通信与报警联动逻辑
