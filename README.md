# WeatherCN Weather

基于 FastAPI、原生 JavaScript 和 PWA 的真实 WeatherCN 天气应用。后端代理全部 WeatherCN 请求，API Key 只从环境变量 `WEATHER_API_KEY` 读取。

## 启动
```bash
cp .env.example .env
# 编辑 .env 填入 WEATHER_API_KEY
python -m pip install -r requirements.txt
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```
访问 `http://127.0.0.1:8000`，健康检查：`curl http://127.0.0.1:8000/api/health`。

## Docker
```bash
cp .env.example .env
docker compose up -d --build
```
生产环境请为 Nginx 配置 HTTPS；iPhone Safari 通过“分享 → 添加到主屏幕”安装 PWA。采用文档中的城市搜索、GeoPosition、实况、10 日、24 小时、分钟降水、预警、生活指数和空气质量接口。
