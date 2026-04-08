# PAL_4G 部署模板

部署目标环境为 **Linux + 宝塔面板**。

## 文件说明

| 文件 | 用途 |
|------|------|
| `backend.env.production.example` | 后端生产环境变量模板 |
| `web.env.production.example` | Web 前端生产环境变量模板 |
| `emqx-docker-compose.yml` | EMQX MQTT Broker Docker 部署 |
| `emqx.env.example` | EMQX 环境变量模板 |
| `nginx.pal4g.conf` | Nginx 反代配置（可导入宝塔） |
| `pal4g-backend.service` | systemd 服务文件 |

## 部署步骤

### 1. 后端

```bash
# 上传代码到服务器
cd /www/wwwroot/pal4g/backend

# 创建虚拟环境并安装依赖
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# 配置环境变量
cp /path/to/deploy/backend.env.production.example .env
# 编辑 .env，填入真实配置

# 注册 systemd 服务
sudo cp /path/to/deploy/pal4g-backend.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable pal4g-backend
sudo systemctl start pal4g-backend
```

### 2. Web 前端

```bash
cd /www/wwwroot/pal4g/web
npm install
npm run build
# dist/ 目录即为静态文件，在宝塔中配置网站根目录指向此处
```

### 3. EMQX MQTT Broker

```bash
cd /www/wwwroot/pal4g/deploy
cp emqx.env.example emqx.env
# 编辑 emqx.env，修改密码

docker compose -f emqx-docker-compose.yml up -d
```

启动后在 EMQX Dashboard (http://服务器IP:18083) 中配置 HTTP 认证，详见 `emqx.env.example` 中的注释。

### 4. Nginx（宝塔面板）

在宝塔面板中新建网站，域名填 `usr-iot.endpage.net`，然后在网站设置 -> 配置文件中参考 `nginx.pal4g.conf` 的内容配置反向代理。

关键配置：
- `/` -> Web 静态文件
- `/api/` -> 反代到 `127.0.0.1:8001`
- `/api/v1/ws/` -> WebSocket 反代到 `127.0.0.1:8001`

### 5. 微信小程序

在本地编译后通过微信开发者工具上传、提审、发布。

## 端口清单

| 服务 | 端口 | 公网 | 说明 |
|------|------|------|------|
| Nginx HTTPS | 443 | 是 | Web + API 入口 |
| Nginx HTTP | 80 | 可选 | 自动跳转 HTTPS |
| 后端 API | 8001 | 否 | 仅 Nginx 内部访问 |
| MQTT 明文 | 1883 | 是 | 设备接入（开发联调用） |
| MQTT TLS | 8883 | 是 | 设备接入（生产推荐） |
| EMQX Dashboard | 18083 | 否 | 仅管理员内网访问 |
