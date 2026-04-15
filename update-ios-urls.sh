#!/bin/bash

# 設定 iOS app 中的固定 Cloudflare Tunnel URLs
# 使用方法: ./update-ios-urls.sh [Swift檔案路徑]

set -e

# ──────────────────────────────────────────────
# 請修改以下兩個網域為你在 Cloudflare 設定的 Public Hostname
# ──────────────────────────────────────────────
API_DOMAIN="https://api.sunnyansen.com"
N8N_DOMAIN="https://n8n.sunnyansen.com"
# ──────────────────────────────────────────────

SWIFT_FILE_PATH="${1:-../food-map-app-v2/food-map-app-v2/Services/Configuration.swift}"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}🔄 設定 iOS App 的 Cloudflare URLs...${NC}"

if [[ ! -f "$SWIFT_FILE_PATH" ]]; then
    echo -e "${RED}❌ 錯誤: Swift 文件不存在: $SWIFT_FILE_PATH${NC}"
    echo -e "${YELLOW}💡 請確認文件路徑或使用: $0 <Swift檔案路徑>${NC}"
    exit 1
fi

echo -e "${BLUE}📱 Swift 文件: $SWIFT_FILE_PATH${NC}"

sed -i '' "s|static let authURL = \"https://[^\"]*\"|static let authURL = \"$N8N_DOMAIN/webhook/start-login\"|g" "$SWIFT_FILE_PATH"
sed -i '' "s|static let twoFAURL = \"https://[^\"]*\"|static let twoFAURL = \"$N8N_DOMAIN/webhook/send-2fa\"|g" "$SWIFT_FILE_PATH"
sed -i '' "s|static let dataURL = \"https://[^\"]*\"|static let dataURL = \"$API_DOMAIN/posts/parsed\"|g" "$SWIFT_FILE_PATH"

echo -e "${GREEN}✅ 更新完成！${NC}"
echo -e "${BLUE}📋 更新後的配置:${NC}"
grep -E "(authURL|twoFAURL|dataURL)" "$SWIFT_FILE_PATH" | sed 's/^/  /'

echo ""
echo -e "${YELLOW}💡 提醒: 請重新編譯 iOS app 以套用新的 URLs${NC}"
