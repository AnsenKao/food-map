"""
重構後的 Instagram 貼文提取器 - 主要模組
使用模組化設計，將功能分離到不同的模組中
"""
import logging
from typing import Optional, List
from src.models.models import PostData, ExtractResult
from src.database.database import DatabaseManager
from src.instagram.auth import InstagramAuth
from src.instagram.profile import ProfileManager


class InstagramExtractor:
    """Instagram 貼文提取器類別 - 重構版本"""
    
    def __init__(self, 
                 username: str,
                 database_file: str = "food_map.db",
                 use_saved_session: bool = True,
                 logger: Optional[logging.Logger] = None):
        """
        初始化 Instagram 提取器
        
        Args:
            username: Instagram 使用者名稱
            database_file: 資料庫檔案路徑
            use_saved_session: 是否使用已保存的 session
            logger: 日誌記錄器
        """
        self.username = username
        self.logger = logger or self._setup_default_logger()
        
        # 初始化各個管理器
        self.db_manager = DatabaseManager(database_file, self.logger)
        self.auth_manager = InstagramAuth(username, use_saved_session, self.logger)
        self.profile_manager = ProfileManager(self.auth_manager, self.logger)
        
    def _setup_default_logger(self) -> logging.Logger:
        """設定預設日誌記錄器"""
        logger = logging.getLogger(__name__)
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('[%(levelname)s] %(message)s')
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            logger.setLevel(logging.INFO)
        return logger
    
    def init_database(self) -> bool:
        """初始化資料庫"""
        return self.db_manager.init_database()
    
    def login(self, password: Optional[str] = None) -> bool:
        """登入 Instagram"""
        return self.auth_manager.login(password)
    
    def get_profile(self):
        """獲取個人檔案"""
        return self.profile_manager.get_profile()
    
    def get_profile_info(self):
        """獲取個人檔案資訊"""
        return self.profile_manager.get_profile_info()
    
    def extract_saved_posts(self) -> ExtractResult:
        """提取儲存貼文並直接存入資料庫"""
        if not self.auth_manager.is_logged_in:
            self.logger.error("尚未登入，無法提取貼文")
            return ExtractResult(success=False, error="未登入")
        
        profile = self.profile_manager.get_profile()
        if profile is None:
            return ExtractResult(success=False, error="無法獲取個人檔案")
        
        # 顯示資料庫現有資料
        existing_count = self.db_manager.get_posts_count()
        self.logger.info(f"資料庫現有貼文: {existing_count} 篇")
        
        # 載入所有已處理的貼文 ID 到記憶體
        processed_set = self.db_manager.get_all_processed_ids()
        
        # 提取儲存貼文並直接存入資料庫
        self.logger.info("開始處理儲存貼文...")
        
        count = 0
        total_found = 0
        skipped_count = 0
        
        try:
            # 獲取儲存的貼文
            self.logger.info("正在獲取儲存貼文清單...")
            saved_posts = profile.get_saved_posts()
            
            # 先收集所有儲存貼文的 shortcode 到 set
            self.logger.info("正在分析儲存貼文...")
            saved_posts_list = list(saved_posts)  # 轉換為 list 以便重複使用
            saved_shortcodes = {post.shortcode for post in saved_posts_list}
            total_found = len(saved_shortcodes)
            
            # 使用 set 差集直接找出需要處理的貼文
            new_shortcodes = saved_shortcodes - processed_set
            skipped_count = total_found - len(new_shortcodes)
            
            self.logger.info(f"找到 {total_found} 篇儲存貼文，其中 {len(new_shortcodes)} 篇為新貼文")
            if skipped_count > 0:
                self.logger.info(f"跳過 {skipped_count} 篇已處理貼文")
            
            self.logger.info("開始處理新貼文...")
            
            # 只處理新的貼文
            for post in saved_posts_list:
                if post.shortcode not in new_shortcodes:
                    continue  # 跳過已處理的貼文
                
                # 移除數量限制，提取所有儲存的貼文
                
                try:
                    self.logger.info(f"處理第 {count + 1} 篇新貼文:")
                    self.logger.info(f"       ID: {post.shortcode}")
                    self.logger.info(f"       作者: @{post.owner_username}")
                    self.logger.info(f"       時間: {post.date_utc}")
                    self.logger.info(f"       類型: {'影片' if post.is_video else '圖片'}")
                    self.logger.info(f"       互動: {post.likes:,} 讚, {post.comments:,} 留言")
                    
                    # 直接儲存到資料庫
                    if self.db_manager.save_post(post):
                        count += 1
                        self.logger.info("       ✅ 已儲存到資料庫")
                        
                        # 顯示文字內容預覽
                        if post.caption:
                            preview = post.caption[:100] + "..." if len(post.caption) > 100 else post.caption
                            self.logger.info(f"       內容預覽: {preview}")
                        else:
                            self.logger.info("       內容預覽: （無文字內容）")
                    else:
                        self.logger.warning("       ⚠️ 跳過（可能重複）")
                    
                except KeyboardInterrupt:
                    self.logger.info("使用者中斷處理")
                    break
                except Exception as e:
                    self.logger.error(f"       ❌ 處理失敗: {e}")
                    continue
        
        except Exception as e:
            self.logger.error(f"處理儲存貼文失敗: {e}")
            self.logger.error(f"錯誤類型: {type(e).__name__}")
            return ExtractResult(success=False, error=str(e))
        
        # 顯示處理結果
        final_count = self.db_manager.get_posts_count()
        new_count = final_count - existing_count
        
        result = ExtractResult(
            success=True,
            total_found=total_found,
            new_posts=new_count,
            skipped_posts=skipped_count,
            total_in_db=final_count
        )
        
        if new_count > 0:
            self.logger.info("處理完成！")
            self.logger.info(f"新增 {new_count} 篇貼文到資料庫")
            self.logger.info(f"資料庫總計: {final_count} 篇貼文")
            if skipped_count > 0:
                self.logger.info(f"跳過 {skipped_count} 篇已存在的貼文")
        elif total_found == 0:
            self.logger.info("沒有找到任何儲存的貼文")
        elif skipped_count == total_found:
            self.logger.info(f"所有 {total_found} 篇貼文都已在資料庫中")
        else:
            self.logger.info(f"找到 {total_found} 篇儲存貼文，但沒有新增任何資料")
        
        self.logger.info(f"資料庫檔案: {self.db_manager.database_file}")
        return result
    
    def get_posts_from_db(self, limit: Optional[int] = None, offset: int = 0) -> List[PostData]:
        """從資料庫獲取貼文資料"""
        return self.db_manager.get_posts(limit, offset)
    
    def search_posts(self, keyword: str, limit: Optional[int] = None) -> List[PostData]:
        """在資料庫中搜尋包含關鍵字的貼文"""
        return self.db_manager.search_posts(keyword, limit)
    
    def get_posts_count(self) -> int:
        """取得已處理的貼文數量"""
        return self.db_manager.get_posts_count()
    
    def close(self):
        """清理資源"""
        self.auth_manager.close()
        self.db_manager.clear_cache()
        self.profile_manager.clear_cache()
