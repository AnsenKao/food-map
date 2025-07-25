"""
配置檔案
"""
import os

class Config:
    """應用程式配置類別"""
    
    # 資料庫設定
    DATABASE_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
    DEFAULT_DATABASE_FILE = "food_map.db"
    
    # Instagram 設定
    USE_SAVED_SESSION = True
    
    # API 設定
    API_HOST = "0.0.0.0"
    API_PORT = 8000
    LOG_LEVEL = "info"
    
    # 日誌設定
    LOG_FORMAT = "[%(levelname)s] %(asctime)s - %(name)s - %(message)s"
    
    @classmethod
    def get_database_path(cls, username: str) -> str:
        """獲取指定使用者的資料庫路徑"""
        os.makedirs(cls.DATABASE_DIR, exist_ok=True)
        return os.path.join(cls.DATABASE_DIR, f"food_map_{username}.db")
    
    @classmethod
    def get_default_database_path(cls) -> str:
        """獲取預設資料庫路徑"""
        os.makedirs(cls.DATABASE_DIR, exist_ok=True)
        return os.path.join(cls.DATABASE_DIR, cls.DEFAULT_DATABASE_FILE)
