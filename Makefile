# Instagram Food Map API - Docker 管理

.PHONY: build run stop clean clean-all logs shell help status backup data n8n update-ios-urls restart

# 預設目標
help:
	@echo "可用命令："
	@echo "  build     - 建立 Docker 映像"
	@echo "  run       - 執行 Docker Compose 服務"
	@echo "  stop      - 停止服務"
	@echo "  clean     - 清理容器和映像（保留資料）"
	@echo "  clean-all - 完全清理（包括資料）"
	@echo "  logs      - 查看日誌"
	@echo "  shell     - 進入容器 shell"
	@echo "  restart        - 重新啟動服務"
	@echo "  status         - 檢查服務狀態"
	@echo "  backup         - 備份資料庫"
	@echo "  data           - 顯示資料目錄內容"
	@echo "  n8n            - 打開 n8n 管理介面"
	@echo "  update-ios-urls - 設定 iOS app 中的固定 Cloudflare URLs"

# 建立映像
build:
	docker-compose build --no-cache

# 執行服務
run:
	docker-compose up -d

# 停止服務
stop:
	docker-compose down

# 重新啟動服務
restart: stop run

# 查看日誌
logs:
	docker-compose logs -f

# 進入容器 shell
shell:
	docker-compose exec instagram-api /bin/bash

# 清理容器和映像（保留資料）
clean:
	docker-compose down --remove-orphans
	docker rmi $$(docker images -q instagram-food-map-api) 2>/dev/null || true
	docker system prune -f

# 完全清理（包括資料 - 危險操作！）
clean-all:
	@echo "⚠️  警告：這將刪除所有資料！"
	@read -p "確定要繼續嗎？ (y/N): " confirm; \
	if [ "$$confirm" = "y" ] || [ "$$confirm" = "Y" ]; then \
		docker-compose down --volumes --remove-orphans; \
		docker rmi $$(docker images -q instagram-food-map-api) 2>/dev/null || true; \
		rm -rf data/*; \
		docker system prune -f; \
		echo "所有資料已清理"; \
	else \
		echo "操作已取消"; \
	fi

# 顯示資料目錄內容
data:
	@echo "資料目錄內容："
	@ls -la data/ 2>/dev/null || echo "data 目錄不存在"
	@echo "\n資料庫檔案大小："
	@du -h data/*.db 2>/dev/null || echo "沒有找到資料庫檔案"

# 檢查服務狀態
status:
	docker-compose ps
	@echo "\n服務健康狀態："
	@curl -s http://localhost:8080/ | jq . || echo "服務未回應"

# 備份資料（從容器內）
backup:
	@if docker-compose ps | grep -q "Up"; then \
		mkdir -p backups; \
		timestamp=$$(date +%Y%m%d_%H%M%S); \
		backup_dir="backups/data_$$timestamp"; \
		mkdir -p "$$backup_dir"; \
		docker-compose exec -T instagram-api tar -czf - -C /app data | tar -xzf - -C "$$backup_dir"; \
		echo "📦 資料已備份到: $$backup_dir"; \
		echo "📊 備份內容:"; \
		ls -lah "$$backup_dir"/data/*.db 2>/dev/null || echo "   沒有找到資料庫檔案"; \
		echo "💾 備份大小: $$(du -sh "$$backup_dir" | cut -f1)"; \
	else \
		echo "❌ 容器未運行，請先執行 'make run'"; \
		echo "💡 提示：或者直接複製主機資料： cp -r data backups/data_$$(date +%Y%m%d_%H%M%S)"; \
	fi

# 打開 n8n 管理介面
n8n:
	@echo "🚀 正在打開 n8n 管理介面..."
	@if command -v open >/dev/null 2>&1; then \
		open http://localhost:5678; \
	elif command -v xdg-open >/dev/null 2>&1; then \
		xdg-open http://localhost:5678; \
	else \
		echo "請手動打開瀏覽器訪問: http://localhost:5678"; \
	fi
	@echo "📝 n8n 管理介面: http://localhost:5678"

# 設定 iOS app 中的固定 Cloudflare URLs
update-ios-urls:
	@echo "📱 設定 iOS app 的 Cloudflare URLs..."
	@./update-ios-urls.sh
