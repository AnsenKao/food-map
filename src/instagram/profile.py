"""
Instagram 個人檔案管理模組
處理使用者個人檔案獲取等功能
"""
import instaloader
import logging
from typing import Optional
from ..models.models import UserProfile


class ProfileManager:
    """個人檔案管理器"""
    
    def __init__(self, auth_manager, logger: Optional[logging.Logger] = None):
        """
        初始化個人檔案管理器
        
        Args:
            auth_manager: 認證管理器實例
            logger: 日誌記錄器
        """
        self.auth_manager = auth_manager
        self.logger = logger or self._setup_default_logger()
        self._profile_cache: Optional[instaloader.Profile] = None
    
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
    
    def get_profile(self, username: Optional[str] = None) -> Optional[instaloader.Profile]:
        """
        獲取使用者個人檔案
        
        Args:
            username: 使用者名稱，如果不提供則使用認證管理器中的使用者名稱
        """
        target_username = username or self.auth_manager.username
        
        # 如果是相同的使用者且有快取，直接返回
        if (self._profile_cache is not None and 
            self._profile_cache.username == target_username):
            return self._profile_cache
            
        if not self.auth_manager.is_logged_in:
            self.logger.error("尚未登入，無法獲取個人檔案")
            return None
            
        try:
            self.logger.info(f"正在獲取 {target_username} 的個人檔案...")
            profile = instaloader.Profile.from_username(
                self.auth_manager.loader.context, 
                target_username
            )
            
            # 如果是認證使用者，則快取
            if target_username == self.auth_manager.username:
                self._profile_cache = profile
            
            self.logger.info("個人檔案資訊:")
            self.logger.info(f"       全名: {profile.full_name}")
            self.logger.info(f"       追蹤者: {profile.followers:,}")
            self.logger.info(f"       追蹤中: {profile.followees:,}")
            self.logger.info(f"       貼文數: {profile.mediacount:,}")
            
            return profile
            
        except instaloader.exceptions.ProfileNotExistsException:
            self.logger.error(f"使用者 {target_username} 不存在")
            return None
        except Exception as e:
            self.logger.error(f"獲取個人檔案失敗: {e}")
            return None
    
    def get_profile_info(self, username: Optional[str] = None) -> Optional[UserProfile]:
        """
        獲取使用者個人檔案資訊並轉換為 UserProfile 物件
        
        Args:
            username: 使用者名稱，如果不提供則使用認證管理器中的使用者名稱
        """
        profile = self.get_profile(username)
        if profile is None:
            return None
        
        return UserProfile(
            username=profile.username,
            full_name=profile.full_name,
            followers=profile.followers,
            followees=profile.followees,
            media_count=profile.mediacount,
            biography=profile.biography,
            is_private=profile.is_private
        )
    
    def clear_cache(self):
        """清除快取"""
        self._profile_cache = None
