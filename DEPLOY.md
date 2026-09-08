# 部署流程

目标环境：`http://120.48.175.245:13003`（Linux 服务器，Docker 部署）

## 一、服务器环境准备（首次，一次性）

SSH 登录服务器：

```bash
ssh root@120.48.175.245
```

安装 Docker（官方脚本，含 compose 插件）：

```bash
curl -fsSL https://get.docker.com | sh
systemctl enable --now docker
docker compose version   # 确认 compose 可用
```

开放端口（二选一或都做）：

- 云厂商控制台 → 安全组 → 放行 TCP 13003 入方向
- 服务器防火墙：`firewall-cmd --permanent --add-port=13003/tcp && firewall-cmd --reload`
  （Ubuntu ufw：`ufw allow 13003/tcp`）

## 二、上传代码

方式 A —— 服务器上直接 git clone（推荐，前提是代码在 Git 仓库）：

```bash
cd /opt && git clone <你的仓库地址> weather-app && cd weather-app
```

方式 B —— 本地打包上传（无 Git 仓库时）：

```bash
# 本地执行（在项目根目录）
tar --exclude='.git' --exclude='__pycache__' --exclude='*.pyc' --exclude='.env' -czf weather-app.tar.gz .
scp weather-app.tar.gz root@120.48.175.245:/opt/

# 服务器上执行
mkdir -p /opt/weather-app && cd /opt/weather-app
tar xzf /opt/weather-app.tar.gz && rm /opt/weather-app.tar.gz
```

## 三、配置环境变量

```bash
cd /opt/weather-app
cp .env.example .env
vim .env
```

必改项：

```ini
WEATHER_API_KEY=你的真实Key
```

按套餐可选调整（已有合理默认值）：

```ini
WEATHER_DAILY_QUOTA=400    # 每日上游调用上限
WEATHER_QPS_LIMIT=5        # 每秒最多 5 次上游请求
```

> 注意：`.env` 已在 `.gitignore` 中，严禁提交到仓库或复制到任何前端代码。

## 四、构建并启动

```bash
cd /opt/weather-app
docker compose up -d --build
docker compose ps          # 两个容器均应为 running/healthy
```

## 五、验证

服务器本机：

```bash
curl http://127.0.0.1:13003/api/health
# 期望：{"status":"ok","service":"weathercn-weather"}

curl "http://127.0.0.1:13003/api/search?q=北京"
# 期望：返回城市列表 JSON（首次会真实调用 WeatherCN）
```

浏览器访问 `http://120.48.175.245:13003`，搜索城市确认页面正常。

## 六、日常运维

查看日志：

```bash
docker compose logs -f weather     # 实时日志（不会包含 API Key）
```

更新版本：

```bash
cd /opt/weather-app
git pull                            # 或重新上传覆盖
docker compose up -d --build
```

重启 / 停止：

```bash
docker compose restart
docker compose down
```

数据说明：天气缓存为内存缓存，容器重启后清空，属正常现象（重启后首次访问会重新拉取）。

## 七、HTTPS（可选）

当前为 HTTP。iPhone"添加到主屏幕"和浏览器定位（geolocation）在 HTTPS 下体验最佳。两种方案：

### 方案 A：域名 + Let's Encrypt（推荐）

1. 准备一个域名，DNS A 记录指向 120.48.175.245
2. 服务器安装 certbot：`apt install -y certbot`（或 yum）
3. docker-compose.yml 的 nginx 端口改为 `["80:80","443:443"]`
4. nginx.conf 增加 443 server 块并引用证书路径（证书目录挂载进容器）
5. 签发：`certbot certonly --standalone -d weather.你的域名.com`，然后 `docker compose up -d --build`

### 方案 B：暂无域名，保持 HTTP

PWA 添加到主屏幕可用；浏览器定位功能在 HTTP 下会被部分浏览器限制，可用城市搜索代替。

## 八、故障排查

| 现象 | 排查 |
|---|---|
| 页面打不开 | `docker compose ps` 看容器状态；安全组/防火墙是否放行 13003 |
| `/api/health` 不通 | `docker compose logs weather` 看启动报错 |
| 天气数据为空 | 检查 `.env` 的 Key 是否有效；日志搜"WeatherCN 请求失败" |
| 频繁 429 | 上游限流：调低 `WEATHER_QPS_LIMIT`（如 2），或拉长各 `CACHE_TTL_*` |
| 数据长期不更新 | 检查 `WEATHER_DAILY_QUOTA` 是否太小导致配额提前用尽 |
| 改了代码没生效 | Service Worker 缓存：强刷（Cmd+Shift+R）；后端代码需 `docker compose up -d --build` |
