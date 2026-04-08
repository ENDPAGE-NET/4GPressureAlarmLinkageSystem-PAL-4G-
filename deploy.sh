#!/bin/bash
# PAL_4G 一键部署脚本（前后端分域）
# 用法: bash deploy.sh
# 宝塔面板: 计划任务 -> Shell脚本 -> 粘贴此脚本路径

set -e

# === 按实际路径修改 ===
PROJECT_DIR="/www/wwwroot/usr-iot.endpage.net"
BACKEND_DIR="/www/wwwroot/usr-iot-backend.endpage.net"
WEB_DIR="$PROJECT_DIR"

echo "===== PAL_4G 部署开始 ====="

# 1. 拉取最新代码
echo "[1/4] 拉取代码..."
cd "$PROJECT_DIR"
git pull origin main

# 2. 后端依赖更新
echo "[2/4] 更新后端依赖..."
cd "$BACKEND_DIR/backend"
source .venv/bin/activate
pip install -r requirements.txt -q

# 3. 前端构建
echo "[3/4] 构建前端..."
cd "$WEB_DIR/web"
npm install --production=false
npm run build

# 4. 重启后端
echo "[4/4] 重启后端..."
sudo systemctl restart pal4g-backend

echo "===== 部署完成 ====="
echo "前端: $WEB_DIR/web/dist/"
echo "后端: systemctl status pal4g-backend"
