#!/bin/bash

# 自動更新 iOS app 中的 ngrok URLs
# 使用方法: ./update-ios-urls.sh [Swift檔案路徑]

set -e

# 配置
SWIFT_FILE_PATH="${1:-../food-map-app-v2/food-map-app-v2/Services/Configuration.swift}"
NGROK_API="http://localhost:4040/api/tunnels"

# 顏色輸出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🔄 開始更新 iOS App 的 ngrok URLs...${NC}"

# 檢查 ngrok 是否運行
if ! curl -s "$NGROK_API" > /dev/null 2>&1; then
    echo -e "${RED}❌ 錯誤: 無法連接到 ngrok API ($NGROK_API)${NC}"
    echo -e "${YELLOW}💡 請確保 Docker Compose 中的 ngrok 服務正在運行${NC}"
    exit 1
fi

# 檢查 Swift 文件是否存在
if [[ ! -f "$SWIFT_FILE_PATH" ]]; then
    echo -e "${RED}❌ 錯誤: Swift 文件不存在: $SWIFT_FILE_PATH${NC}"
    echo -e "${YELLOW}💡 請確認文件路徑或使用: $0 <Swift檔案路徑>${NC}"
    exit 1
fi

echo -e "${BLUE}📱 Swift 文件: $SWIFT_FILE_PATH${NC}"

# 獲取 ngrok tunnels
echo -e "${BLUE}🌐 獲取 ngrok tunnels...${NC}"
TUNNELS_JSON=$(curl -s "$NGROK_API")

# 提取 URLs
SERVICE_5678_URL=$(echo "$TUNNELS_JSON" | jq -r '.tunnels[] | select(.name=="service5678") | .public_url')
SERVICE_8080_URL=$(echo "$TUNNELS_JSON" | jq -r '.tunnels[] | select(.name=="service8080") | .public_url')

# 檢查是否成功獲取 URLs
if [[ "$SERVICE_5678_URL" == "null" || -z "$SERVICE_5678_URL" ]]; then
    echo -e "${RED}❌ 錯誤: 無法獲取 service5678 的 URL${NC}"
    exit 1
fi

if [[ "$SERVICE_8080_URL" == "null" || -z "$SERVICE_8080_URL" ]]; then
    echo -e "${RED}❌ 錯誤: 無法獲取 service8080 的 URL${NC}"
    exit 1
fi

echo -e "${GREEN}✅ 獲取到的 URLs:${NC}"
echo -e "  📦 service5678 (N8N): $SERVICE_5678_URL"
echo -e "  🍔 service8080 (API): $SERVICE_8080_URL"

# 更新 Swift 文件中的 URLs
echo -e "${BLUE}✏️  更新 Swift 文件...${NC}"

# 根據你的 Swift 文件結構，更新對應的 URLs
# authURL 和 twoFAURL 使用 service5678 (N8N)
# dataURL 使用 service8080 (API)

# 使用 sed 來替換 URLs
sed -i '' "s|static let authURL = \"https://[^\"]*\"|static let authURL = \"$SERVICE_5678_URL/webhook/start-login\"|g" "$SWIFT_FILE_PATH"
sed -i '' "s|static let twoFAURL = \"https://[^\"]*\"|static let twoFAURL = \"$SERVICE_5678_URL/webhook/send-2fa\"|g" "$SWIFT_FILE_PATH"
sed -i '' "s|static let dataURL = \"https://[^\"]*\"|static let dataURL = \"$SERVICE_8080_URL/posts/parsed\"|g" "$SWIFT_FILE_PATH"

echo -e "${GREEN}🎉 更新完成！${NC}"

# 顯示更新後的配置
echo -e "${BLUE}📋 更新後的配置:${NC}"
grep -E "(authURL|twoFAURL|dataURL)" "$SWIFT_FILE_PATH" | sed 's/^/  /'

echo ""
echo -e "${GREEN}✨ iOS App URLs 已自動更新！${NC}"
echo -e "${YELLOW}💡 提醒: 請重新編譯 iOS app 以使用新的 URLs${NC}"