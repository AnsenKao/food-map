# Instagram 儲存貼文下載器

使用 instaloader 下載你在 Instagram 儲存的貼文。

## 📁 腳本檔案

- `simple_saved_posts.py` - 基本版（需要密碼登入）
- `cookie_saved_posts.py` - Cookie 版（推薦，支援 2FA）
- `advanced_cookie_downloader.py` - 進階 Cookie 版
- `instagram_saved_posts.py` - 命令列完整版

## 🚀 使用方式

### 方法一：Cookie 版（推薦，支援雙重驗證）

適合有開啟雙重驗證（2FA）的帳號：

1. **取得 sessionid**：
   - 在瀏覽器登入 Instagram
   - 按 F12 開啟開發者工具
   - 到 Application > Cookies > https://www.instagram.com
   - 找到 'sessionid' 並複製其值

2. **設定腳本**：
   編輯 `cookie_saved_posts.py`：
   ```python
   USERNAME = "你的Instagram使用者名稱"
   SESSIONID = "你複製的sessionid值"
   ```

3. **執行**：
   ```bash
   python cookie_saved_posts.py
   ```

### 方法二：密碼版

1. 編輯 `simple_saved_posts.py`，修改第 10 行的使用者名稱：
   ```python
   USERNAME = "你的Instagram使用者名稱"  # 請改成你的帳號
   ```

2. 執行腳本：
   ```bash
   python simple_saved_posts.py
   ```

3. 輸入密碼（只需要第一次，之後會記住 session）

### 方法三：命令列版

使用命令列參數：
```bash
python instagram_saved_posts.py 你的使用者名稱 [-p 密碼] [-d 下載目錄] [-n 最大數量]
```

範例：
```bash
# 下載全部儲存貼文
python instagram_saved_posts.py myusername

# 只下載前 5 篇
python instagram_saved_posts.py myusername -n 5

# 指定下載目錄
python instagram_saved_posts.py myusername -d my_saved_posts
```

## 下載內容

腳本會下載：
- 📷 圖片檔案
- 🎥 影片檔案  
- 📄 貼文資訊（JSON 格式）
- 📝 說明文字

## 檔案命名

下載的檔案會依照以下格式命名：
```
下載目錄/
├── saved_你的使用者名稱/
│   ├── 20240123_143022_ABC123.jpg     # 圖片
│   ├── 20240123_143022_ABC123.mp4     # 影片
│   └── 20240123_143022_ABC123.json    # 貼文資訊
```

## 注意事項

⚠️ **重要提醒**：
1. 請遵守 Instagram 的使用條款
2. 不要過於頻繁執行，避免被限制
3. 首次登入會建立 session 檔案，請妥善保管
4. 只能下載自己帳號儲存的貼文

## 錯誤處理

如果遇到問題：
1. 確認網路連線正常
2. 確認 Instagram 帳號密碼正確
3. 檢查是否被 Instagram 暫時限制
4. 刪除 `.session-使用者名稱` 檔案重新登入

## 依賴套件

- `instaloader>=4.14.2`

已包含在 `pyproject.toml` 中，使用 `uv sync` 自動安裝。
