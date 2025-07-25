"""
API 伺服器啟動腳本
"""
import sys
import os
import uvicorn

# 添加專案根目錄到 Python 路徑
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config.settings import Config

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("api.app:app", host="0.0.0.0", port=8080, reload=True)
