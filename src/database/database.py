"""
資料庫操作模組
處理所有與資料庫相關的操作
"""
import sqlite3
import logging
from typing import Set, List, Optional
import instaloader
from ..models.models import PostData


class DatabaseManager:
    """資料庫管理器"""
    
    def __init__(self, database_file: str, logger: Optional[logging.Logger] = None):
        """
        初始化資料庫管理器
        
        Args:
            database_file: 資料庫檔案路徑
            logger: 日誌記錄器
        """
        self.database_file = database_file
        self.logger = logger or self._setup_default_logger()
        self._processed_ids_cache: Optional[Set[str]] = None
    
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
        """初始化資料庫，只建立 posts 表"""
        try:
            conn = sqlite3.connect(self.database_file)
            cursor = conn.cursor()
            
            # 檢查是否已有 posts 表
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='posts'")
            if cursor.fetchone():
                self.logger.info(f"使用現有資料庫: {self.database_file}")
            else:
                # 只建立 posts 表
                cursor.execute('''
                    CREATE TABLE posts (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        post_id TEXT UNIQUE NOT NULL,
                        author TEXT NOT NULL,
                        post_date DATETIME NOT NULL,
                        post_type TEXT NOT NULL,
                        likes INTEGER DEFAULT 0,
                        comments INTEGER DEFAULT 0,
                        url TEXT NOT NULL,
                        content TEXT NOT NULL,
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                # 建立索引
                cursor.execute('CREATE INDEX idx_posts_author ON posts(author)')
                cursor.execute('CREATE INDEX idx_posts_date ON posts(post_date)')
                cursor.execute('CREATE INDEX idx_posts_type ON posts(post_type)')
                
                self.logger.info(f"新資料庫已建立: {self.database_file}")
            
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            self.logger.error(f"資料庫初始化失敗: {e}")
            return False
    
    def get_all_processed_ids(self) -> Set[str]:
        """一次性載入所有已處理的貼文 ID，回傳 set 用於快速查找"""
        if self._processed_ids_cache is not None:
            return self._processed_ids_cache
            
        try:
            conn = sqlite3.connect(self.database_file)
            cursor = conn.cursor()
            cursor.execute('SELECT post_id FROM posts')
            processed_ids = {row[0] for row in cursor.fetchall()}
            conn.close()
            
            self._processed_ids_cache = processed_ids
            self.logger.info(f"載入了 {len(processed_ids)} 個已處理貼文 ID 到記憶體")
            return processed_ids
        except Exception as e:
            self.logger.error(f"載入已處理 ID 失敗: {e}")
            return set()
    
    def save_post(self, post: instaloader.Post) -> bool:
        """將貼文資料儲存到資料庫"""
        try:
            conn = sqlite3.connect(self.database_file)
            cursor = conn.cursor()
            
            # 插入貼文資料
            cursor.execute('''
                INSERT INTO posts (post_id, author, post_date, post_type, likes, comments, url, content)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                post.shortcode,
                post.owner_username,
                post.date_utc.isoformat(),
                '影片' if post.is_video else '圖片',
                post.likes,
                post.comments,
                f"https://www.instagram.com/p/{post.shortcode}/",
                post.caption or ""
            ))
            
            conn.commit()
            conn.close()
            
            # 更新快取
            if self._processed_ids_cache is not None:
                self._processed_ids_cache.add(post.shortcode)
            
            return True
            
        except sqlite3.IntegrityError:
            # 貼文已存在
            return False
        except Exception as e:
            self.logger.error(f"資料庫儲存失敗: {e}")
            return False
    
    def get_posts_count(self) -> int:
        """取得已處理的貼文數量"""
        try:
            conn = sqlite3.connect(self.database_file)
            cursor = conn.cursor()
            cursor.execute('SELECT COUNT(*) FROM posts')
            count = cursor.fetchone()[0]
            conn.close()
            return count
        except Exception as e:
            self.logger.error(f"取得貼文數量失敗: {e}")
            return 0
    
    def get_posts(self, limit: Optional[int] = None, offset: int = 0) -> List[PostData]:
        """從資料庫獲取貼文資料"""
        try:
            conn = sqlite3.connect(self.database_file)
            cursor = conn.cursor()
            
            query = '''
                SELECT post_id, author, post_date, post_type, likes, comments, url, content, created_at, updated_at
                FROM posts 
                ORDER BY post_date DESC
            '''
            
            if limit:
                query += f' LIMIT {limit} OFFSET {offset}'
            
            cursor.execute(query)
            rows = cursor.fetchall()
            conn.close()
            
            posts = []
            for row in rows:
                posts.append(PostData(
                    post_id=row[0],
                    author=row[1],
                    post_date=row[2],
                    post_type=row[3],
                    likes=row[4],
                    comments=row[5],
                    url=row[6],
                    content=row[7],
                    created_at=row[8],
                    updated_at=row[9]
                ))
            
            return posts
            
        except Exception as e:
            self.logger.error(f"從資料庫獲取貼文失敗: {e}")
            return []
    
    def search_posts(self, keyword: str, limit: Optional[int] = None) -> List[PostData]:
        """在資料庫中搜尋包含關鍵字的貼文"""
        try:
            conn = sqlite3.connect(self.database_file)
            cursor = conn.cursor()
            
            query = '''
                SELECT post_id, author, post_date, post_type, likes, comments, url, content, created_at, updated_at
                FROM posts 
                WHERE content LIKE ? OR author LIKE ?
                ORDER BY post_date DESC
            '''
            
            if limit:
                query += f' LIMIT {limit}'
            
            search_term = f'%{keyword}%'
            cursor.execute(query, (search_term, search_term))
            rows = cursor.fetchall()
            conn.close()
            
            posts = []
            for row in rows:
                posts.append(PostData(
                    post_id=row[0],
                    author=row[1],
                    post_date=row[2],
                    post_type=row[3],
                    likes=row[4],
                    comments=row[5],
                    url=row[6],
                    content=row[7],
                    created_at=row[8],
                    updated_at=row[9]
                ))
            
            return posts
            
        except Exception as e:
            self.logger.error(f"搜尋貼文失敗: {e}")
            return []
    
    def clear_cache(self):
        """清除快取"""
        self._processed_ids_cache = None
