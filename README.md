# Instagram 貼文提取器 - 重構模組化版本

這是一個重構的 Instagram 貼文提取器，採用物件導向和模組化設計，方便整合到 FastAPI 應用程式中。

## 📁 專案結構

```
food-map/
├── src/                           # 核心源代碼
│   ├── __init__.py
│   ├── models/                    # 資料模型
│   │   ├── __init__.py
│   │   └── models.py             # PostData, ExtractResult, UserProfile
│   ├── database/                  # 資料庫操作
│   │   ├── __init__.py
│   │   └── database.py           # DatabaseManager
│   └── instagram/                 # Instagram 相關功能
│       ├── __init__.py
│       ├── auth.py               # InstagramAuth - 認證管理
│       ├── profile.py            # ProfileManager - 個人檔案管理
│       └── extractor.py          # InstagramExtractor - 主要提取器
├── api/                          # FastAPI 應用程式
│   ├── __init__.py
│   └── app.py                    # FastAPI 路由和邏輯
├── config/                       # 配置管理
│   ├── __init__.py
│   └── settings.py               # Config - 應用程式設定
├── data/                         # 資料存儲目錄
│   └── *.db                      # SQLite 資料庫檔案
├── run_api.py                    # API 伺服器啟動腳本
├── requirements.txt              # 依賴套件
├── instagram_extractor.py        # 原始版本（保留作為參考）
├── instagram_extractor_modular.py # 舊模組化版本（保留作為參考）
└── README.md                     # 說明文件
```

## 🏗️ 模組說明

### 1. src/models/models.py
定義核心資料結構：
- `PostData`: 貼文資料結構
- `ExtractResult`: 提取結果資料結構  
- `UserProfile`: 使用者個人檔案資料結構

### 2. src/database/database.py
資料庫操作功能：
- `DatabaseManager`: 管理 SQLite 資料庫操作
- 初始化資料庫、儲存貼文、查詢貼文等功能
- 支援快取機制提升效能

### 3. src/instagram/auth.py
Instagram 認證功能：
- `InstagramAuth`: 處理登入、2FA 驗證、session 管理
- 支援自動載入已保存的 session
- 完整的錯誤處理

### 4. src/instagram/profile.py
個人檔案管理：
- `ProfileManager`: 獲取使用者個人檔案資訊
- 支援快取機制避免重複請求

### 5. src/instagram/extractor.py
主要提取器類別：
- `InstagramExtractor`: 整合所有模組的主要類別
- 提供完整的 API 介面
- 支援批次處理和進度追蹤

### 6. api/app.py
FastAPI 應用程式：
- 提供 RESTful API 介面
- 支援多使用者同時使用
- 包含背景任務處理
- 完整的錯誤處理和日誌記錄

### 7. config/settings.py
配置管理：
- `Config`: 統一管理應用程式設定
- 資料庫路徑、API 設定等
- 環境相關配置

## 🚀 安裝與使用

### 1. 安裝依賴
```bash
pip install -r requirements.txt
```

### 2. 作為模組使用
```python
from src.instagram.extractor import InstagramExtractor
from config.settings import Config

# 建立提取器實例
extractor = InstagramExtractor(
    username="your_username",
    database_file=Config.get_database_path("your_username"),
    use_saved_session=True
)

# 初始化資料庫
extractor.init_database()

# 登入
extractor.login()

# 提取儲存貼文
result = extractor.extract_saved_posts()
print(f"提取結果: {result.to_dict()}")

# 查詢貼文
posts = extractor.get_posts_from_db(limit=10)
for post in posts:
    print(f"貼文: {post.content[:50]}...")

# 搜尋貼文
search_results = extractor.search_posts("美食", limit=5)
for post in search_results:
    print(f"找到: {post.author} - {post.content[:50]}...")

# 清理資源
extractor.close()
```

### 3. FastAPI 服務
```bash
# 啟動 API 服務
python run_api.py

# 或使用 uvicorn 直接啟動
uvicorn api.app:app --host 0.0.0.0 --port 8000 --reload
```

#### API 端點：

1. **登入**
```bash
curl -X POST "http://localhost:8000/login" \
     -H "Content-Type: application/json" \
     -d '{"username": "your_username", "password": "your_password"}'
```

2. **獲取個人檔案**
```bash
curl "http://localhost:8000/profile/your_username"
```

3. **提取貼文（背景執行）**
```bash
curl -X POST "http://localhost:8000/extract/your_username" \
     -H "Content-Type: application/json" \
     -d '{}'
```

4. **提取貼文（同步執行）**
```bash
curl -X POST "http://localhost:8000/extract-sync/your_username" \
     -H "Content-Type: application/json" \
     -d '{}'
```

5. **獲取貼文列表**
```bash
curl "http://localhost:8000/posts/your_username?limit=20&offset=0"
```

6. **搜尋貼文**
```bash
curl -X POST "http://localhost:8000/search/your_username" \
     -H "Content-Type: application/json" \
     -d '{"keyword": "美食", "limit": 10}'
```

7. **獲取狀態**
```bash
curl "http://localhost:8000/status/your_username"
```

8. **登出**
```bash
curl -X DELETE "http://localhost:8000/logout/your_username"
```

## ✨ 設計優勢

### 1. 清晰的模組結構
- 按功能分離模組，易於理解和維護
- 每個模組有明確的職責
- 減少代碼耦合度

### 2. 配置管理
- 統一的配置管理系統
- 支援不同環境的配置
- 資料庫檔案自動組織

### 3. 錯誤處理
- 完整的異常處理機制
- 詳細的日誌記錄系統
- 優雅的錯誤回饋

### 4. 效能優化
- 快取機制減少重複查詢
- 批次處理提升效率
- 記憶體優化的 ID 集合操作

### 5. 擴展性
- 模組化設計易於擴展
- 支援插件式架構
- API 設計遵循 RESTful 規範

## 📝 開發指南

### 新增功能模組
1. 在 `src/` 下創建新的包
2. 在 `src/instagram/extractor.py` 中整合新功能
3. 更新 API 路由（如需要）
4. 添加對應的配置項

### 資料庫擴展
1. 修改 `src/database/database.py` 中的表結構
2. 更新 `src/models/models.py` 中的資料模型
3. 添加遷移腳本（建議）

### API 擴展
1. 在 `api/app.py` 中添加新路由
2. 更新 Pydantic 模型
3. 添加對應的錯誤處理

## ⚠️ 注意事項

1. **遵守使用條款**
   - 請遵守 Instagram 的使用條款
   - 不要過度頻繁地請求資料
   - 尊重其他使用者的隱私

2. **資料安全**
   - 保護登入憑證
   - 定期備份資料庫（位於 `data/` 目錄）
   - 謹慎處理個人資料

3. **效能考量**
   - 適當設定請求間隔
   - 監控系統資源使用
   - 定期清理過期資料

4. **日誌管理**
   - 日誌檔案會自動創建
   - 定期清理舊日誌檔案
   - 注意日誌檔案大小
