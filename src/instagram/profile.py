"""
Instagram 個人檔案管理模組
處理使用者個人檔案獲取等功能
"""
import instaloader
import logging
from typing import Optional, Iterator
from ..models.models import UserProfile
from .auth import SessionInvalidError, is_session_error


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
            
            # 只記錄網頁內嵌就有的欄位；followers 等欄位會額外觸發 graphql 查詢，常被 403 擋下
            self.logger.info(f"個人檔案: {profile.full_name} (id: {profile.userid})")
            
            return profile
            
        except instaloader.exceptions.ProfileNotExistsException:
            self.logger.error(f"使用者 {target_username} 不存在")
            return None
        except Exception as e:
            self.logger.error(f"獲取個人檔案失敗: {e}")
            if is_session_error(e):
                self.clear_cache()
                self.auth_manager.invalidate_session(str(e))
                raise SessionInvalidError(str(e)) from e
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
        
        def safe(getter, default=None):
            # 這些欄位可能需要額外查詢，失敗時回預設值，不讓整個 profile 失敗
            try:
                return getter()
            except Exception as e:
                self.logger.warning(f"讀取個人檔案欄位失敗: {e}")
                return default

        return UserProfile(
            username=profile.username,
            full_name=profile.full_name,
            followers=safe(lambda: profile.followers, 0),
            followees=safe(lambda: profile.followees, 0),
            media_count=safe(lambda: profile.mediacount, 0) or 0,
            biography=safe(lambda: profile.biography, ""),
            is_private=safe(lambda: profile.is_private, False)
        )
    
    def iter_saved_posts(self) -> Iterator[instaloader.Post]:
        """
        透過 Instagram App 的 API（api/v1/feed/saved/posts/）逐頁取得儲存貼文，新存的在前。

        instaloader 的 Profile.get_saved_posts() 使用舊的 graphql query_hash，
        已被 Instagram 以 feedback_required 拒絕，因此改走 App API。
        """
        if not self.auth_manager.is_logged_in:
            raise instaloader.exceptions.LoginRequiredException("尚未登入，無法取得儲存貼文")

        context = self.auth_manager.loader.context
        max_id = None
        while True:
            params = {"max_id": max_id} if max_id else {}
            data = context.get_iphone_json("api/v1/feed/saved/posts/", params)

            for item in data.get("items", []):
                media = item.get("media")
                if not media:
                    continue
                post = self._post_from_media(context, media)
                if post is not None:
                    yield post

            max_id = data.get("next_max_id")
            if not data.get("more_available") or not max_id:
                break

    def _post_from_media(self, context, media: dict) -> Optional[instaloader.Post]:
        """把 App API 的 media 轉成 instaloader.Post，並補上程式會用到的欄位"""
        if media.get("media_type") not in (1, 2, 8):
            self.logger.warning(f"略過不支援的貼文類型 {media.get('media_type')}: {media.get('code')}")
            return None

        # 隱藏讚數的貼文不會有這些欄位
        media.setdefault("like_count", 0)
        media.setdefault("has_liked", False)

        post = instaloader.Post.from_iphone_struct(context, media)
        user = media.get("user") or {}
        post._node["owner"] = {"username": user.get("username"), "id": str(user.get("pk", ""))}
        post._node["edge_media_to_comment"] = {"count": media.get("comment_count") or 0}
        return post

    def clear_cache(self):
        """清除快取"""
        self._profile_cache = None
