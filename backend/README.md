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

## 需要你提供的微信配置

如果要启用真实微信小程序登录和报警订阅消息，请在 `backend/.env` 中补齐以下配置：

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

你需要提供给我的信息：

- 小程序 `AppID`
- 小程序 `AppSecret`
- 订阅消息模板 ID
- 模板里每个字段对应的 key 名
- 用户点击消息后要跳转的小程序页面路径

字段 key 很重要，因为微信订阅消息模板的数据键名不是固定的，必须与你在微信公众平台里选定的模板保持一致。当前后端默认按下面 4 个字段发送：

- 报警类型
- 设备名称
- 触发时间
- 备注

如果你实际模板字段不是 `thing1/thing2/time3/thing4`，只需要改 `.env` 里的 `WECHAT_SUBSCRIBE_FIELD_*` 配置，不需要再改代码。

## 当前微信能力说明

- `POST /api/v1/auth/wechat-login`
  - 当 `WECHAT_LOGIN_USE_REAL_CODE2SESSION=true` 时，后端会使用微信 `code2Session` 交换 `openid`
  - 当该开关为 `false` 时，仍可继续用 `wechat_open_id` 直传方式本地联调
- `POST /api/v1/auth/wechat-bind`
  - 支持真实 `code` 绑定，也支持开发阶段直传 `wechat_open_id`
- `GET /api/v1/notifications/subscription-status`
- `POST /api/v1/notifications/subscribe`
- `POST /api/v1/notifications/unsubscribe`
- `POST /api/v1/jobs/alarm-notification-dispatch`
  - 管理员可手动触发一次报警订阅消息派发

## 报警订阅消息派发规则

- 新报警创建后会进入待发送状态
- APScheduler 会按 `ALARM_NOTIFICATION_DISPATCH_INTERVAL_SECONDS` 周期扫描待发送报警
- 只有同时满足以下条件才会真正发送：
  - 设备归属用户已绑定微信
  - 用户已开启订阅
  - 系统已配置模板 ID
- 派发结果会记录到报警通知状态字段和通信日志中

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
