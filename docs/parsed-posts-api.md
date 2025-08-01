# Parsed Posts API 使用說明

新增的 `GET /posts/parsed/{username}` API 端點可以提取已解析且地址不為空的貼文資料。

## API 規格

**端點**: `GET /posts/parsed/{username}`  
**功能**: 獲取已解析且 parsed_address 不為空的貼文（返回 post_id, parsed_store, parsed_address）

### 參數

| 參數名 | 類型 | 必需 | 預設值 | 說明 |
|---------|------|------|--------|------|
| username | string | 是 | - | Instagram 用戶名 |
| limit | integer | 否 | 100 | 返回結果的最大數量 |
| offset | integer | 否 | 0 | 跳過的記錄數量（用於分頁） |

### 回應格式

```json
{
  "success": true,
  "count": 5,
  "posts": [
    {
      "post_id": "DI75yMkh4WO",
      "parsed_store": "伊根鍋屋",
      "parsed_address": "高雄市三民區大順二路242-3號"
    },
    {
      "post_id": "DFshOxiztaW", 
      "parsed_store": "萩沢料理 私廚拉麵",
      "parsed_address": "高雄市左營區裕誠路209號"
    }
  ],
  "limit": 5,
  "offset": 0
}
```

## 使用範例

### 1. 獲取前 5 筆已解析的貼文
```bash
curl "http://localhost:8080/posts/parsed/corgifatgin?limit=5"
```

### 2. 分頁查詢（跳過前 5 筆，取接下來的 10 筆）
```bash
curl "http://localhost:8080/posts/parsed/corgifatgin?limit=10&offset=5"
```

### 3. 獲取所有已解析的貼文（使用預設限制）
```bash
curl "http://localhost:8080/posts/parsed/corgifatgin"
```

## 注意事項

- 只會返回 `parsed_address` 不為 NULL 且不為空字串的記錄
- 結果按照 `updated_at` 降序排列（最近更新的在前）
- 如果指定的用戶不存在或沒有已解析的貼文，會返回空陣列
- 此 API 與現有的批次更新 API 配合使用，可以形成完整的資料處理流程

## 相關 API

- `GET /posts/unparsed/{username}` - 獲取尚未解析的貼文
- `PATCH /posts/update-metadata/{username}` - 批次更新貼文的解析資料
