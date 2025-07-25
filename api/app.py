"""
FastAPI 應用程式 - Instagram 貼文提取器 API
展示如何將模組化的 Instagram 提取器整合到 FastAPI 中
"""
import sys
import os
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional, List
import logging
from contextlib import asynccontextmanager

# 添加專案根目錄到 Python 路徑
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 導入我們的模組
from src.instagram.extractor import InstagramExtractor
from src.models.models import PostData, ExtractResult, UserProfile
from config.settings import Config

# 設定日誌
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 全域變數存儲提取器實例
extractor_instances = {}

# Pydantic 模型
class LoginRequest(BaseModel):
    username: str
    password: Optional[str] = None
    use_saved_session: bool = True

class SearchRequest(BaseModel):
    keyword: str
    limit: Optional[int] = 100

# 應用程式生命週期管理
@asynccontextmanager
async def lifespan(app: FastAPI):
    # 啟動時
    logger.info("FastAPI 應用程式啟動")
    yield
    # 關閉時
    logger.info("正在清理資源...")
    for extractor in extractor_instances.values():
        try:
            extractor.close()
        except Exception as e:
            logger.error(f"清理提取器時發生錯誤: {e}")
    extractor_instances.clear()
    logger.info("FastAPI 應用程式關閉")

# 建立 FastAPI 應用程式
app = FastAPI(
    title="Instagram 貼文提取器 API",
    description="用於提取和管理 Instagram 儲存貼文的 RESTful API",
    version="1.0.0",
    lifespan=lifespan
)

# 依賴函數
def get_extractor(username: str) -> InstagramExtractor:
    """獲取或建立提取器實例"""
    if username not in extractor_instances:
        extractor_instances[username] = InstagramExtractor(
            username=username,
            database_file=Config.get_database_path(username),
            logger=logger
        )
    return extractor_instances[username]

# API 路由

@app.get("/")
async def root():
    """根路由"""
    return {
        "message": "Instagram 貼文提取器 API",
        "version": "1.0.0",
        "endpoints": {
            "login": "POST /login",
            "profile": "GET /profile/{username}",
            "extract": "POST /extract/{username}",
            "posts": "GET /posts/{username}",
            "search": "POST /search/{username}",
            "status": "GET /status/{username}"
        }
    }

@app.post("/login")
async def login(request: LoginRequest):
    """登入 Instagram"""
    try:
        extractor = get_extractor(request.username)
        
        # 初始化資料庫
        if not extractor.init_database():
            raise HTTPException(status_code=500, detail="資料庫初始化失敗")
        
        # 登入
        success = extractor.login(request.password)
        
        if success:
            return {
                "success": True,
                "message": f"成功登入使用者 {request.username}",
                "username": request.username
            }
        else:
            raise HTTPException(status_code=401, detail="登入失敗")
            
    except Exception as e:
        logger.error(f"登入時發生錯誤: {e}")
        raise HTTPException(status_code=500, detail=f"登入時發生錯誤: {str(e)}")

@app.get("/profile/{username}")
async def get_profile(username: str) -> UserProfile:
    """獲取使用者個人檔案"""
    try:
        extractor = get_extractor(username)
        
        if not extractor.auth_manager.is_logged_in:
            raise HTTPException(status_code=401, detail="尚未登入")
        
        profile_info = extractor.get_profile_info()
        
        if profile_info is None:
            raise HTTPException(status_code=404, detail="找不到使用者個人檔案")
        
        return profile_info
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"獲取個人檔案時發生錯誤: {e}")
        raise HTTPException(status_code=500, detail=f"獲取個人檔案時發生錯誤: {str(e)}")

@app.post("/extract/{username}")
async def extract_posts(username: str, background_tasks: BackgroundTasks):
    """提取儲存貼文（背景執行）"""
    try:
        extractor = get_extractor(username)
        
        if not extractor.auth_manager.is_logged_in:
            raise HTTPException(status_code=401, detail="尚未登入")
        
        # 提取所有儲存的貼文（無數量限制）
        
        # 在背景執行提取
        def extract_task():
            try:
                result = extractor.extract_saved_posts()
                logger.info(f"提取完成: {result.to_dict()}")
            except Exception as e:
                logger.error(f"背景提取失敗: {e}")
        
        background_tasks.add_task(extract_task)
        
        return {
            "success": True,
            "message": "開始提取儲存貼文，請稍後查看狀態",
            "username": username,
            "max_posts": "無限制"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"啟動提取時發生錯誤: {e}")
        raise HTTPException(status_code=500, detail=f"啟動提取時發生錯誤: {str(e)}")

@app.post("/extract-sync/{username}")
async def extract_posts_sync(username: str) -> ExtractResult:
    """提取儲存貼文（同步執行）"""
    try:
        extractor = get_extractor(username)
        
        if not extractor.auth_manager.is_logged_in:
            raise HTTPException(status_code=401, detail="尚未登入")
        
        # 提取所有儲存的貼文（無數量限制）
        
        # 同步執行提取
        result = extractor.extract_saved_posts()
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"提取時發生錯誤: {e}")
        raise HTTPException(status_code=500, detail=f"提取時發生錯誤: {str(e)}")

@app.get("/posts/{username}")
async def get_posts(username: str, limit: Optional[int] = 50, offset: int = 0) -> List[PostData]:
    """獲取貼文列表"""
    try:
        extractor = get_extractor(username)
        posts = extractor.get_posts_from_db(limit=limit, offset=offset)
        return posts
        
    except Exception as e:
        logger.error(f"獲取貼文時發生錯誤: {e}")
        raise HTTPException(status_code=500, detail=f"獲取貼文時發生錯誤: {str(e)}")

@app.post("/search/{username}")
async def search_posts(username: str, request: SearchRequest) -> List[PostData]:
    """搜尋貼文"""
    try:
        extractor = get_extractor(username)
        posts = extractor.search_posts(request.keyword, request.limit)
        return posts
        
    except Exception as e:
        logger.error(f"搜尋貼文時發生錯誤: {e}")
        raise HTTPException(status_code=500, detail=f"搜尋貼文時發生錯誤: {str(e)}")

@app.get("/status/{username}")
async def get_status(username: str):
    """獲取提取器狀態"""
    try:
        extractor = get_extractor(username)
        
        posts_count = extractor.get_posts_count()
        is_logged_in = extractor.auth_manager.is_logged_in
        
        status = {
            "username": username,
            "is_logged_in": is_logged_in,
            "posts_count": posts_count,
            "database_file": extractor.db_manager.database_file,
        }
        
        return status
        
    except Exception as e:
        logger.error(f"獲取狀態時發生錯誤: {e}")
        raise HTTPException(status_code=500, detail=f"獲取狀態時發生錯誤: {str(e)}")

@app.delete("/logout/{username}")
async def logout(username: str):
    """登出並清理資源"""
    try:
        if username in extractor_instances:
            extractor = extractor_instances[username]
            extractor.close()
            del extractor_instances[username]
        
        return {
            "success": True,
            "message": f"已登出使用者 {username}"
        }
        
    except Exception as e:
        logger.error(f"登出時發生錯誤: {e}")
        raise HTTPException(status_code=500, detail=f"登出時發生錯誤: {str(e)}")

# 錯誤處理
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    logger.error(f"未處理的錯誤: {exc}")
    return JSONResponse(
        status_code=500,
        content={"detail": "內部伺服器錯誤"}
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
