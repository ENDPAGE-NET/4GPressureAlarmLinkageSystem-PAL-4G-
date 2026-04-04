# Web 前端完成情况与接口对接检查

## 1. 检查范围

- 检查时间：2026-04-04
- 检查对象：
  - `docs/web端首期开发计划.md`
  - `docs/Web 端第二期开发计划.md`
  - `docs/后端开发进度文档.md`
  - `docs/4G 压力报警模块 · 软件需求沟通文档.md`
  - `web/src/**`
  - `backend/app/api/routes/**`
- 说明：本次仅核查文档、前端源码与后端路由实现的一致性，不改动后端逻辑。

## 2. 总体结论

当前 `web/` 前端已经不是“首期未开始”的状态，而是已经完成了一个可编译、可登录、可查询、可控制的后台前端，并且**首期核心链路已基本打通，二期大部分管理/运维页面也已经落地**。

综合判断如下：

| 维度 | 结论 |
| ---- | ---- |
| 首期 MVP 页面完成度 | 高，核心链路基本可用 |
| 首期接口对接完成度 | 高，登录、仪表盘、报警、设备详情、继电器控制、修改密码均已接入 |
| 二期页面完成度 | 中高，用户管理、设备分组、日志、导出、调度、MQTT、运维首页均已实现 |
| 二期接口对接完成度 | 中高，大多数页面已与后端真实接口对接 |
| 实时能力 | 未完成，当前只有轮询和占位状态提示，没有真实 WebSocket 对接 |
| 国际化/主题 | 已有全局能力，但仍是部分完成，仍存在较多硬编码文案 |

补充结论：

1. 前端构建已验证通过：`web/` 下执行 `npm run build` 可以成功构建。
2. 前端已统一采用 `/api/v1` 前缀、JWT Bearer Token、401 失效跳回登录页。
3. 仪表盘和设备详情已按文档实现 30 秒轮询刷新。
4. 当前最大差距不在“有没有页面”，而在“是否完全满足文档细项”和“横切能力是否真正收口”。

## 3. 页面完成情况

### 3.1 首期范围

| 页面/能力 | 文档目标 | 当前状态 | 结论 | 说明 |
| ---- | ---- | ---- | ---- | ---- |
| 登录页 | 用户名密码登录、拉取当前用户、登录态恢复 | 已实现 | 已完成 | 已接 `/auth/login` 和 `/auth/me`，登录表单采用 `application/x-www-form-urlencoded`，符合文档约定 |
| 路由守卫 | 未登录跳登录、管理员权限控制 | 已实现 | 已完成 | 已区分 `requiresAuth`、`guestOnly`、`adminOnly` |
| 仪表盘 | 概览、图表、近期报警、近期指令 | 已实现 | 已完成 | 已接 `/dashboard/home`、`/dashboard/charts`、`/dashboard/recent-alarms`、`/dashboard/recent-commands` |
| 报警记录页 | 分页、筛选、历史记录查看 | 已实现 | 部分完成 | 已支持分页、关键字、报警状态、联动状态；但缺少时间范围、模块编号、报警类型等更完整筛选项 |
| 设备列表页 | 查看设备状态、进入详情 | 已实现 | 已完成 | 已接 `/devices/monitoring` 和 `/devices`，列表展示完整 |
| 设备详情页 | 模块状态、最近报警、最近指令、继电器控制 | 已实现 | 已完成 | 已接 `/dashboard/devices/{id}`、`/devices/{id}`、`/relay-commands` |
| 手动继电器控制 | 开/关控制、反馈结果刷新 | 已实现 | 已完成 | 控制后会刷新详情 |
| 个人设置/修改密码 | 修改密码并重新登录 | 已实现 | 已完成 | 已接 `/users/me/change-password` |
| 普通用户设备绑定/移除 | 按 SN 添加新设备、移除已绑定设备 | 未看到完整页面入口 | 未完成 | 后端有 `/devices/bind`、`/devices/{id}/unbind`，但前端没有普通用户绑定设备的页面流程 |

### 3.2 二期范围

| 页面/能力 | 二期计划 | 当前状态 | 结论 | 说明 |
| ---- | ---- | ---- | ---- | ---- |
| 用户管理 | 列表、创建、编辑、启停用、删除、重置密码 | 已实现 | 已完成 | 已接 `GET/POST/PATCH/DELETE /users` 与 `POST /users/{user_id}/reset-password`，删除时已限制“不可删除自己”和“存在设备/分组归属时不可删除” |
| 设备分组管理 | 列表、新建、编辑、删除、查看分组下设备 | 已实现 | 已完成 | 已接 `/devices/groups` 相关接口 |
| 设备归属分配 | 分配 owner、回收 owner | 已实现 | 已完成 | 入口放在设备列表管理员操作中 |
| 设备分组分配 | 设备加入/移出分组 | 已实现 | 已完成 | 入口放在设备列表管理员操作中 |
| 日志中心 | 运行/操作/通信日志分页筛选 | 已实现 | 部分完成 | 已接三类分页接口；缺时间范围、日志联动跳转、高亮等细节 |
| 导出中心 | 报警导出、命令导出 | 已实现 | 已完成 | 同时在日志中心也加了导出快捷入口 |
| 调度任务页 | 调度状态、任务历史、手动触发、备份 | 已实现 | 大体完成 | 主流程已接通，但页面初始化缺统一错误兜底 |
| MQTT 状态页 | 查看连接状态与摘要 | 已实现 | 已完成 | 已接 `/mqtt/status` |
| 运维首页 | 汇总调度、MQTT、日志概览、备份 | 已实现 | 大体完成 | 已做概览聚合，但缺统一加载/错误态处理 |
| 国际化 | 至少 `zh-CN` / `en-US` | 已实现基础框架 | 部分完成 | 字典、切换器、Element Plus locale 已接入，但仍存在不少硬编码中文/英文文案 |
| 深色模式 | 全站主题切换 | 已实现基础能力 | 大体完成 | 主题切换、CSS 变量、全局 data-theme 已落地 |
| WebSocket 实时更新 | 仪表盘/设备详情/报警等实时更新 | 仅有占位逻辑 | 未完成 | 当前 `useRealtime` 只显示状态文案，没有真正建立 WebSocket 连接 |

## 4. 接口对接情况

### 4.1 已确认接通的核心接口

以下接口在前端中同时满足“有 API 封装 + 有页面调用 + 后端路由存在”：

| 接口 | 前端页面 | 状态 | 说明 |
| ---- | ---- | ---- | ---- |
| `POST /api/v1/auth/login` | 登录页 | 已接通 | 表单提交方式正确 |
| `GET /api/v1/auth/me` | 登录恢复、个人页 | 已接通 | 用于恢复登录态和展示当前用户 |
| `GET /api/v1/dashboard/home` | 仪表盘 | 已接通 | |
| `GET /api/v1/dashboard/charts` | 仪表盘 | 已接通 | |
| `GET /api/v1/dashboard/recent-alarms` | 仪表盘 | 已接通 | |
| `GET /api/v1/dashboard/recent-commands` | 仪表盘 | 已接通 | |
| `GET /api/v1/dashboard/alarms/page` | 报警记录页 | 已接通 | |
| `GET /api/v1/devices/monitoring` | 设备列表页 | 已接通 | |
| `GET /api/v1/devices` | 设备列表页 | 已接通 | 用于补充 owner/group 等字段 |
| `GET /api/v1/devices/{device_id}` | 设备详情页 | 已接通 | |
| `GET /api/v1/dashboard/devices/{device_id}` | 设备详情页 | 已接通 | |
| `POST /api/v1/relay-commands` | 设备详情页 | 已接通 | 继电器手动控制 |
| `POST /api/v1/users/me/change-password` | 个人设置页 | 已接通 | |
| `GET /api/v1/users` | 用户管理、设备列表、分组页 | 已接通 | 管理员场景 |
| `POST /api/v1/users` | 用户管理 | 已接通 | |
| `PATCH /api/v1/users/{user_id}` | 用户管理 | 已接通 | |
| `DELETE /api/v1/users/{user_id}` | 用户管理 | 已接通 | 支持删除用户，含后端约束校验 |
| `POST /api/v1/users/{user_id}/reset-password` | 用户管理 | 已接通 | |
| `GET /api/v1/devices/groups` | 设备分组、设备列表 | 已接通 | |
| `POST /api/v1/devices/groups` | 设备分组 | 已接通 | |
| `PATCH /api/v1/devices/groups/{group_id}` | 设备分组 | 已接通 | |
| `DELETE /api/v1/devices/groups/{group_id}` | 设备分组 | 已接通 | |
| `POST /api/v1/devices/{device_id}/assign-owner` | 设备列表 | 已接通 | |
| `POST /api/v1/devices/{device_id}/assign-group` | 设备列表 | 已接通 | |
| `POST /api/v1/devices/{device_id}/unbind` | 设备列表 | 已接通 | 当前用于回收归属 |
| `GET /api/v1/logs/overview` | 日志中心、运维首页 | 已接通 | |
| `GET /api/v1/logs/runtime/page` | 日志中心 | 已接通 | |
| `GET /api/v1/logs/operations/page` | 日志中心 | 已接通 | |
| `GET /api/v1/logs/communication/page` | 日志中心 | 已接通 | |
| `GET /api/v1/dashboard/alarms/export` | 导出中心、日志中心 | 已接通 | |
| `GET /api/v1/dashboard/commands/export` | 导出中心、日志中心 | 已接通 | |
| `GET /api/v1/jobs/scheduler` | 调度页、运维首页 | 已接通 | |
| `GET /api/v1/jobs/history` | 调度页、运维首页 | 已接通 | |
| `POST /api/v1/jobs/offline-check` | 调度页 | 已接通 | |
| `POST /api/v1/jobs/retry-pending` | 调度页 | 已接通 | |
| `POST /api/v1/jobs/alarm-recovery-check` | 调度页 | 已接通 | |
| `POST /api/v1/jobs/cleanup-files` | 调度页 | 已接通 | |
| `POST /api/v1/jobs/backup-database` | 调度页 | 已接通 | |
| `GET /api/v1/jobs/backups` | 调度页、运维首页 | 已接通 | |
| `GET /api/v1/mqtt/status` | MQTT 状态页、运维首页 | 已接通 | |

### 4.2 后端已存在、但前端未看到实际使用的接口

以下接口后端已有实现，但当前 Web 前端没有形成明确页面流程或没有实际调用：

| 接口 | 当前情况 | 影响 |
| ---- | ---- | ---- |
| `POST /api/v1/devices/bind` | 前端没有普通用户“按 SN 绑定设备”入口 | 原始需求中的设备绑定流程未闭环 |
| `POST /api/v1/devices` | 前端无创建设备页面 | 若业务需要后台新增设备，当前 Web 不支持 |
| `PATCH /api/v1/devices/{device_id}` | 前端无设备编辑页 | 设备基础信息维护未落地 |
| `DELETE /api/v1/devices/{device_id}` | 前端无删除入口 | 管理员设备删除未落地 |
| `POST /api/v1/devices/{device_id}/modules` | 前端无新增模块入口 | 模块运维能力未落地 |
| `GET /api/v1/devices/modules/{module_id}` | 前端未使用 | 无单模块详情 |
| `DELETE /api/v1/devices/modules/{module_id}` | 前端未使用 | 无模块删除操作 |
| `GET /api/v1/dashboard/commands/page` | 前端未使用 | 当前只能看近期指令，缺完整分页指令页 |
| `GET /api/v1/alarms` 及相关恢复接口 | 前端未使用 | Web 端主要走 dashboard 聚合接口 |
| `GET /api/v1/logs/runtime` 等非分页接口 | 前端未使用 | 当前统一使用分页接口是合理的 |
| `POST /api/v1/mqtt/simulate`、`/simulate-raw` | 前端未使用 | 本地协议联调能力未前置到 Web |
| `GET /api/v1/relay-commands`、`/{id}/feedback` | 前端未使用 | 指令管理仍偏只读，缺更深控制与反馈页 |

### 4.3 对接方式符合文档的点

1. 所有请求统一走 `web/src/api/http.ts`，基础前缀为 `VITE_API_BASE`，默认 `/api/v1`。
2. 请求拦截器统一注入 Bearer Token。
3. 响应拦截器对 `401` 统一清 token 并跳转登录页。
4. 仪表盘、设备详情均通过 `usePolling` 每 30 秒刷新一次，符合首期联调约定。
5. 管理员接口通过前端路由 `adminOnly` 和后端管理员鉴权双重限制。

## 5. 完成度判断

为便于排期，这里给出一个偏工程化的完成度判断：

| 模块 | 完成度判断 |
| ---- | ---- |
| 首期核心业务链路 | 85% - 90% |
| 二期管理与运维页面 | 70% - 80% |
| 接口基础对接 | 85% 以上 |
| 二期横切能力（主题/国际化/实时） | 40% - 60% |

说明：

- 首期扣分主要在“普通用户设备绑定/移除流程未完整前端化”和“报警页筛选维度不足”。
- 二期扣分主要在“WebSocket 未实现”“国际化未彻底收口”“部分页面缺统一错误态/加载态”。

## 6. 当前主要差距

### 6.1 功能差距

1. 普通用户设备绑定能力未落地，和需求文档中的“输入 SN/扫码绑定设备”不一致。
2. 报警记录页筛选项不完整，缺少时间范围、报警类型、模块编号等。
3. 用户删除能力已补齐，但删除前仍受“不可删除自己”和“不可删除仍持有设备/设备分组的用户”约束。
4. 缺少完整的指令分页中心，只展示了近期指令。
5. 缺少设备新增、设备编辑、模块新增/删除等更深层管理入口。

### 6.2 横切能力差距

1. `useRealtime` 目前只是状态文案封装，没有建立真实 WebSocket 连接，也没有事件订阅与消息分发。
2. 国际化只是“框架在、字典在、部分页面接入”，但很多页面标题、按钮、描述、表头仍是硬编码。
3. 运维首页、调度页等页面虽然能调用接口，但错误态/空态处理不如首期核心页面统一。

### 6.3 体验与质量风险

1. `OperationsOverviewView.vue`、`SchedulerView.vue` 这类页面初始化请求没有做统一 `DataState` 包装，任一接口异常时用户感知不够明确。
2. 构建虽然通过，但产物中 `element` 和 `charts` chunk 较大，后续可能需要继续做按需拆分或性能优化。
3. 当前“二期正式后台”的产品定位已经写入界面文案，但实时能力仍未完成，容易造成交付认知偏差。

## 7. 建议的下一步

建议按照下面顺序收口：

1. 先补普通用户设备绑定/移除流程，完成原始业务闭环。
2. 补报警记录页筛选项，至少补时间范围、报警类型、模块编号。
3. 补实时能力真实实现；若后端暂未提供 WebSocket，则把当前能力明确标注为“轮询版”。
4. 统一把二期页面补齐加载态、空态、错误态。
5. 清理硬编码文案，完成首期和二期页面的国际化收口。
6. 视管理需求再决定是否补设备/模块更深层管理页面和完整指令中心。

## 8. 最终判断

当前 Web 前端可以认定为：

- **已经完成首期 MVP 的主体实现，并且核心接口已经对接成功；**
- **已经提前实现了二期的大部分管理/运维页面与接口联动；**
- **但距离“二期完全收口”还差实时能力、国际化收口、部分业务入口补齐与页面兜底完善。**

如果只看“是否可用于首轮联调和演示”，答案是：**可以**。

如果看“是否已经完全符合首期+二期文档细项”，答案是：**还没有，需要继续收口**。
