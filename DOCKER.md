# Docker 部署指南

## 快速開始

### 1. 使用 Docker Compose（推薦）

```bash
# 建立並啟動服務
docker-compose up -d

# 查看日誌
docker-compose logs -f

# 停止服務
docker-compose down
```

### 2. 使用 Makefile（更簡便）

```bash
# 查看所有可用命令
make help

# 建立並啟動服務
make build
make run

# 查看日誌
make logs

# 停止服務
make stop
```

## 詳細說明

### 建立映像
```bash
# 使用 Docker Compose
docker-compose build

# 或使用 Docker 指令
docker build -t instagram-food-map-api .
```

### 執行容器
```bash
# 背景執行
docker-compose up -d

# 前台執行（可看到即時日誌）
docker-compose up
```

### 檢查服務狀態
```bash
# 檢查容器狀態
docker-compose ps

# 測試 API
curl http://localhost:8080/
```

### 資料持久化

**重要：你的資料不會遺失！**

容器使用以下 volumes 來持久化資料：
- `./data:/app/data` - 資料庫檔案（SQLite）
- `instagram_sessions` - Instagram session 檔案

即使容器刪除重建，資料仍會保留在主機的 `data/` 目錄中。

```bash
# 查看資料目錄
make data

# 手動檢查
ls -la data/

# 資料庫檔案位置
# - 主機端：./data/food_map_<username>.db
# - 容器內：/app/data/food_map_<username>.db
```

### 環境變數

可在 `docker-compose.yml` 中設定：
- `API_HOST` - API 主機地址（預設: 0.0.0.0）
- `API_PORT` - API 端口（預設: 8080）
- `PYTHONPATH` - Python 路徑

## 使用方式

### API 端點

容器啟動後，API 將在 `http://localhost:8080` 可用：

```bash
# 健康檢查
curl http://localhost:8080/

# 登入
curl -X POST "http://localhost:8080/login" \
     -H "Content-Type: application/json" \
     -d '{"username": "your_instagram_username"}'

# 提取貼文
curl -X POST "http://localhost:8080/extract-sync/your_username" \
     -H "Content-Type: application/json" \
     -d '{}'
```

## 故障排除

### 查看日誌
```bash
# 即時日誌
docker-compose logs -f

# 最近 100 行日誌
docker-compose logs --tail=100
```

### 進入容器 debug
```bash
# 進入容器 shell
docker-compose exec instagram-api /bin/bash

# 或使用 Makefile
make shell
```

### 重新啟動服務
```bash
# 重新啟動
docker-compose restart

# 或完全重建
docker-compose down
docker-compose up -d
```

### 清理資源
```bash
# 停止並刪除容器
docker-compose down

# 完全清理（包括 volumes）
make clean
```

## 生產環境部署

### 安全考量

1. **移除 reload 模式**：修改 `run_api.py` 移除 `reload=True`
2. **使用反向代理**：建議使用 Nginx 作為反向代理
3. **HTTPS**：在生產環境中啟用 HTTPS
4. **資料備份**：定期備份 `./data` 目錄

### 效能調整

```yaml
# 在 docker-compose.yml 中添加資源限制
services:
  instagram-api:
    # ...
    deploy:
      resources:
        limits:
          memory: 1G
          cpus: '0.5'
        reservations:
          memory: 512M
          cpus: '0.25'
```

### 監控

容器內建健康檢查，可以透過以下方式監控：

```bash
# 檢查健康狀態
docker-compose ps

# 使用 Docker health check
docker inspect --format='{{.State.Health.Status}}' instagram-food-map-api
```
