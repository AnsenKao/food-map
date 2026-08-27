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
    
    # OpenRouter AI 設定
    OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY", "")
    OPENROUTER_MODEL = os.environ.get("OPENROUTER_MODEL", "z-ai/glm-5.3-flash")
    # GLM 系列預設開啟 thinking，OpenRouter 不允許停用，只能以 effort 壓到 0 reasoning token；
    # 且僅部分 provider 真的遵守，故一併鎖定 provider（實測 Novita、GMICloud 為 0）。
    OPENROUTER_REASONING_EFFORT = os.environ.get("OPENROUTER_REASONING_EFFORT", "minimal")
    OPENROUTER_PROVIDERS = [
        p.strip() for p in os.environ.get("OPENROUTER_PROVIDERS", "Novita,GMICloud").split(",") if p.strip()
    ]
    # 允許在指定 provider 都不可用時改用其他家：可能退回會 thinking 的 provider（較慢較貴），
    # 但至少拿得到結果，避免分析迴圈空轉。
    OPENROUTER_ALLOW_FALLBACKS = os.environ.get("OPENROUTER_ALLOW_FALLBACKS", "true").lower() != "false"
    ANALYZE_BATCH_SIZE = int(os.environ.get("ANALYZE_BATCH_SIZE", "10"))

    @classmethod
    def get_default_database_path(cls) -> str:
        """獲取預設資料庫路徑"""
        os.makedirs(cls.DATABASE_DIR, exist_ok=True)
        return os.path.join(cls.DATABASE_DIR, cls.DEFAULT_DATABASE_FILE)
