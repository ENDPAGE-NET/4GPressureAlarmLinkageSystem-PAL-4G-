# Backend

PAL_4G 后端基于 FastAPI 开发，当前已经具备账号鉴权、设备管理、报警联动、MQTT 接入骨架、定时任务和日志落库能力。

## 目录

- `app/main.py`：FastAPI 入口
- `app/api/`：API 路由
- `app/models/`：SQLAlchemy 数据模型
- `app/schemas/`：请求与响应 schema
- `app/services/`：业务服务层
- `app/db/`：数据库初始化与会话
- `tests/`：本地 pytest 测试

## 本地启动

```bash
pip install -r requirements.txt
uvicorn app.main:app --reload
```

## 当前已实现

- 登录与 JWT 鉴权
- 用户管理
- 设备、模块、设备分组管理
- 报警记录与联动指令
- MQTT 状态消息接入
- MQTT 设备反馈消息回写
- APScheduler 定时任务
- 运行日志、操作日志、通信日志落库

## 需要你提供的 MQTT 配置

如果要接真实 broker，请在 `backend/.env` 中补齐以下配置：

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

## 当前默认 topic 约定

状态上报 topic：

```text
pal_4g/status/{serial_number}/{module_code}
```

设备反馈 topic：

```text
pal_4g/feedback/{serial_number}/{module_code}
```

下发命令 topic：

```text
pal_4g/commands/{serial_number}/{module_code}
```

## 当前默认 payload 约定

状态上报 payload：

```json
{
  "serial_number": "SN-1001",
  "module_code": "A",
  "is_online": true,
  "relay_state": false,
  "battery_level": 80,
  "voltage_value": 3.6,
  "trigger_alarm_type": "low_voltage",
  "alarm_message": "voltage below threshold"
}
```

设备反馈 payload：

```json
{
  "command_id": 12,
  "execution_status": "success",
  "feedback_status": "device_ack",
  "feedback_message": "relay closed by device",
  "serial_number": "SN-1001",
  "module_code": "A"
}
```

## 说明

- 当前这套 MQTT 协议字段是后端联调默认版本。
- 你一旦提供真实设备协议，我会直接把 topic 规则和 payload 字段映射替换成真实版本。
- 即使本地不连真实 broker，也可以通过 `/api/v1/mqtt/simulate` 和 `/api/v1/mqtt/simulate-raw` 做联调。
