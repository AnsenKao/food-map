"""
Instagram 登入與會話管理模組
處理 Instagram 登入、2FA 驗證等功能
"""
import instaloader
import getpass
import logging
from typing import Optional


class InstagramAuth:
    """Instagram 認證管理器"""
    
    def __init__(self, username: str, use_saved_session: bool = True, logger: Optional[logging.Logger] = None):
        """
        初始化認證管理器
        
        Args:
            username: Instagram 使用者名稱
            use_saved_session: 是否使用已保存的 session
            logger: 日誌記錄器
        """
        self.username = username
        self.use_saved_session = use_saved_session
        self.logger = logger or self._setup_default_logger()
        
        # Instagram loader 設定
        self.loader = instaloader.Instaloader()
        self._configure_loader()
        self._is_logged_in = False
        self._needs_2fa = False  # 追蹤是否需要 2FA 驗證
    
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
    
    def _configure_loader(self):
        """配置 Instaloader 設定"""
        self.loader.download_pictures = False
        self.loader.download_videos = False
        self.loader.download_video_thumbnails = False
        self.loader.download_geotags = False
        self.loader.download_comments = False
        self.loader.save_metadata = False
    
    @property
    def is_logged_in(self) -> bool:
        """檢查是否已登入"""
        return self._is_logged_in
    
    @property
    def needs_2fa(self) -> bool:
        """檢查是否需要 2FA 驗證"""
        return self._needs_2fa
    
    def login(self, password: Optional[str] = None) -> bool:
        """支援 2FA 的登入函式"""
        if self._is_logged_in:
            return True
            
        self.logger.info(f"正在登入使用者: {self.username}")
        
        # 嘗試載入已保存的 session
        if self.use_saved_session:
            try:
                self.logger.info("嘗試使用已保存的 session...")
                self.loader.load_session_from_file(self.username)
                self.logger.info("成功載入已保存的 session")
                self._is_logged_in = True
                return True
            except FileNotFoundError:
                self.logger.info("找不到已保存的 session，需要重新登入")
            except Exception as e:
                self.logger.warning(f"載入 session 失敗: {e}")
                self.logger.info("將進行全新登入")
        
        # 進行全新登入
        try:
            if password is None:
                password = getpass.getpass("請輸入密碼: ")
            
            # 嘗試登入
            self.logger.info("正在嘗試登入...")
            self.loader.login(self.username, password)
            
            self.logger.info("登入成功！")
            
            # 保存 session 供下次使用
            try:
                self.logger.info("正在保存 session...")
                self.loader.save_session_to_file()
                self.logger.info("Session 已保存")
            except Exception as e:
                self.logger.warning(f"保存 session 失敗: {e}")
            
            self._is_logged_in = True
            return True
            
        except instaloader.exceptions.TwoFactorAuthRequiredException:
            self.logger.info("需要雙重驗證 (2FA)")
            self._needs_2fa = True
            # 不在這裡處理 2FA，讓 API 來處理
            raise  # 重新拋出異常給 API 處理
        
        except instaloader.exceptions.BadCredentialsException:
            self.logger.error("用戶名或密碼錯誤")
            return False
        
        except instaloader.exceptions.ConnectionException as e:
            self.logger.error(f"網路連線問題: {e}")
            return False
        
        except Exception as e:
            self.logger.error(f"登入失敗: {e}")
            self.logger.error(f"錯誤類型: {type(e).__name__}")
            return False
    
    def _handle_2fa(self) -> bool:
        """處理雙重驗證"""
        self.logger.info("需要雙重驗證 (2FA)")
        
        # 在 Docker 環境中，input() 不可用，拋出異常讓 API 處理
        raise instaloader.exceptions.TwoFactorAuthRequiredException("需要 2FA 驗證碼")
    
    def verify_2fa(self, two_factor_code: str) -> bool:
        """使用提供的 2FA 驗證碼進行驗證"""
        try:
            # 使用 2FA 登入
            self.logger.info("正在驗證 2FA 碼...")
            self.loader.two_factor_login(two_factor_code)
            
            self.logger.info("2FA 驗證成功！")
            
            # 保存 session
            try:
                self.logger.info("正在保存 session...")
                self.loader.save_session_to_file()
                self.logger.info("Session 已保存")
            except Exception as e:
                self.logger.warning(f"保存 session 失敗: {e}")
            
            self._is_logged_in = True
            return True
            
        except Exception as e:
            self.logger.error(f"2FA 驗證失敗: {e}")
            return False
            
        except Exception as e:
            self.logger.error(f"2FA 驗證失敗: {e}")
            return False
    
    def logout(self):
        """登出"""
        self._is_logged_in = False
        self._needs_2fa = False
        self.logger.info("已登出")
    
    def close(self):
        """清理資源"""
        try:
            if self.loader:
                self.loader.close()
        except Exception:
            pass
