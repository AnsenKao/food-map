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
        """初始化資料庫，建立 posts 表並確保包含所有必要欄位"""
        try:
            conn = sqlite3.connect(self.database_file)
            cursor = conn.cursor()
            
            # 檢查是否已有 posts 表
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='posts'")
            if cursor.fetchone():
                # 檢查是否需要添加新欄位
                cursor.execute("PRAGMA table_info(posts)")
                columns = [column[1] for column in cursor.fetchall()]
                
                # 如果沒有 parsed_store 欄位，添加它
                if 'parsed_store' not in columns:
                    cursor.execute('ALTER TABLE posts ADD COLUMN parsed_store TEXT')
                    self.logger.info("已添加 parsed_store 欄位")
                
                # 如果沒有 parsed_address 欄位，添加它
                if 'parsed_address' not in columns:
                    cursor.execute('ALTER TABLE posts ADD COLUMN parsed_address TEXT')
                    self.logger.info("已添加 parsed_address 欄位")
                
                self.logger.info(f"使用現有資料庫: {self.database_file}")
            else:
                # 建立包含所有欄位的新表
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
                        parsed_store TEXT,
                        parsed_address TEXT,
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                # 建立索引
                cursor.execute('CREATE INDEX idx_posts_author ON posts(author)')
                cursor.execute('CREATE INDEX idx_posts_date ON posts(post_date)')
                cursor.execute('CREATE INDEX idx_posts_type ON posts(post_type)')
                cursor.execute('CREATE INDEX idx_posts_parsed_store ON posts(parsed_store)')
                cursor.execute('CREATE INDEX idx_posts_parsed_address ON posts(parsed_address)')
                
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
    
    def update_post_metadata(self, post_id: str, parsed_store: Optional[str] = None, parsed_address: Optional[str] = None) -> bool:
        """更新貼文的 parsed_store 和 parsed_address 欄位"""
        try:
            conn = sqlite3.connect(self.database_file)
            cursor = conn.cursor()
            
            # 構建動態 SQL 更新語句
            update_fields = []
            params = []
            
            if parsed_store is not None:
                update_fields.append("parsed_store = ?")
                params.append(parsed_store)
            
            if parsed_address is not None:
                update_fields.append("parsed_address = ?")
                params.append(parsed_address)
            
            if not update_fields:
                self.logger.warning("沒有提供要更新的欄位")
                return False
            
            # 始終更新 updated_at 欄位
            update_fields.append("updated_at = CURRENT_TIMESTAMP")
            params.append(post_id)
            
            sql = f"UPDATE posts SET {', '.join(update_fields)} WHERE post_id = ?"
            
            cursor.execute(sql, params)
            rows_affected = cursor.rowcount
            
            conn.commit()
            conn.close()
            
            if rows_affected > 0:
                self.logger.info(f"成功更新貼文 {post_id} 的元數據")
                return True
            else:
                self.logger.warning(f"找不到貼文 ID: {post_id}")
                return False
                
        except Exception as e:
            self.logger.error(f"更新貼文元數據失敗: {e}")
            return False
    
    def get_unparsed_posts(self, limit: Optional[int] = None, offset: int = 0) -> List[dict]:
        """獲取尚未解析店家和地址的貼文，只返回 post_id 和 content"""
        try:
            conn = sqlite3.connect(self.database_file)
            cursor = conn.cursor()
            
            # 查詢 parsed_store 和 parsed_address 都為 NULL 的貼文
            base_query = """
                SELECT post_id, content 
                FROM posts 
                WHERE (parsed_store IS NULL OR parsed_store = '') 
                  AND parsed_address IS NULL
                ORDER BY post_date DESC
            """
            
            if limit is not None:
                query = f"{base_query} LIMIT ? OFFSET ?"
                cursor.execute(query, (limit, offset))
            else:
                query = f"{base_query} OFFSET ?"
                cursor.execute(query, (offset,))
            
            rows = cursor.fetchall()
            conn.close()
            
            # 返回字典格式的結果
            results = []
            for row in rows:
                results.append({
                    'post_id': row[0],
                    'content': row[1]
                })
            
            return results
            
        except Exception as e:
            self.logger.error(f"獲取未解析貼文失敗: {e}")
            return []
    
    def batch_update_post_metadata(self, updates: List[dict]) -> dict:
        """批次更新多個貼文的 parsed_store 和 parsed_address 欄位
        
        Args:
            updates: 包含更新資料的字典列表，每個字典包含 post_id, parsed_store, parsed_address
            
        Returns:
            包含成功、失敗數量和詳細結果的字典
        """
        results = {
            "success_count": 0,
            "failed_count": 0,
            "success_posts": [],
            "failed_posts": []
        }
        
        try:
            conn = sqlite3.connect(self.database_file)
            cursor = conn.cursor()
            
            for update in updates:
                post_id = update.get("post_id")
                parsed_store = update.get("parsed_store")
                parsed_address = update.get("parsed_address")
                
                if not post_id:
                    results["failed_count"] += 1
                    results["failed_posts"].append({
                        "post_id": post_id,
                        "error": "缺少 post_id"
                    })
                    continue
                
                # 構建動態 SQL 更新語句
                update_fields = []
                params = []
                
                if parsed_store is not None:
                    update_fields.append("parsed_store = ?")
                    params.append(parsed_store)
                
                if parsed_address is not None:
                    update_fields.append("parsed_address = ?")
                    params.append(parsed_address)
                
                if not update_fields:
                    results["failed_count"] += 1
                    results["failed_posts"].append({
                        "post_id": post_id,
                        "error": "沒有提供要更新的欄位"
                    })
                    continue
                
                # 始終更新 updated_at 欄位
                update_fields.append("updated_at = CURRENT_TIMESTAMP")
                params.append(post_id)
                
                sql = f"UPDATE posts SET {', '.join(update_fields)} WHERE post_id = ?"
                
                try:
                    cursor.execute(sql, params)
                    rows_affected = cursor.rowcount
                    
                    if rows_affected > 0:
                        results["success_count"] += 1
                        results["success_posts"].append({
                            "post_id": post_id,
                            "parsed_store": parsed_store,
                            "parsed_address": parsed_address
                        })
                        self.logger.info(f"成功更新貼文 {post_id}")
                    else:
                        results["failed_count"] += 1
                        results["failed_posts"].append({
                            "post_id": post_id,
                            "error": "找不到該貼文 ID"
                        })
                        
                except Exception as e:
                    results["failed_count"] += 1
                    results["failed_posts"].append({
                        "post_id": post_id,
                        "error": str(e)
                    })
                    self.logger.error(f"更新貼文 {post_id} 失敗: {e}")
            
            conn.commit()
            conn.close()
            
            self.logger.info(f"批次更新完成: 成功 {results['success_count']} 篇，失敗 {results['failed_count']} 篇")
            return results
                
        except Exception as e:
            self.logger.error(f"批次更新貼文元數據失敗: {e}")
            return {
                "success_count": 0,
                "failed_count": len(updates),
                "success_posts": [],
                "failed_posts": [{"post_id": "批次操作", "error": str(e)}]
            }
    
    def get_parsed_posts(self, limit: Optional[int] = None, offset: int = 0) -> List[dict]:
        """獲取已解析且地址不為空的貼文，返回 post_id, parsed_store, parsed_address"""
        try:
            conn = sqlite3.connect(self.database_file)
            cursor = conn.cursor()
            
            # 查詢 parsed_address 不為 NULL 且不為空字串的貼文
            base_query = """
                SELECT post_id, parsed_store, parsed_address 
                FROM posts 
                WHERE parsed_address IS NOT NULL AND parsed_address != ''
                ORDER BY updated_at DESC
            """
            
            if limit is not None:
                query = f"{base_query} LIMIT ? OFFSET ?"
                cursor.execute(query, (limit, offset))
            else:
                query = f"{base_query} OFFSET ?"
                cursor.execute(query, (offset,))
            
            rows = cursor.fetchall()
            conn.close()
            
            # 返回字典格式的結果
            results = []
            for row in rows:
                results.append({
                    'post_id': row[0],
                    'parsed_store': row[1],
                    'parsed_address': row[2]
                })
            
            return results
            
        except Exception as e:
            self.logger.error(f"獲取已解析貼文失敗: {e}")
            return []
    
    def delete_post_by_id(self, post_id: str) -> bool:
        """根據 post_id 刪除貼文"""
        try:
            conn = sqlite3.connect(self.database_file)
            cursor = conn.cursor()
            
            # 刪除貼文
            cursor.execute('DELETE FROM posts WHERE post_id = ?', (post_id,))
            rows_affected = cursor.rowcount
            
            conn.commit()
            conn.close()
            
            if rows_affected > 0:
                # 從快取中移除
                if self._processed_ids_cache is not None:
                    self._processed_ids_cache.discard(post_id)
                
                self.logger.info(f"成功刪除貼文 {post_id}")
                return True
            else:
                self.logger.warning(f"找不到貼文 ID: {post_id}")
                return False
                
        except Exception as e:
            self.logger.error(f"刪除貼文失敗: {e}")
            return False
    
    def batch_delete_posts(self, post_ids: List[str]) -> dict:
        """批次刪除多個貼文
        
        Args:
            post_ids: 要刪除的貼文 ID 列表
            
        Returns:
            包含成功、失敗數量和詳細結果的字典
        """
        results = {
            "success_count": 0,
            "failed_count": 0,
            "success_posts": [],
            "failed_posts": []
        }
        
        try:
            conn = sqlite3.connect(self.database_file)
            cursor = conn.cursor()
            
            for post_id in post_ids:
                if not post_id:
                    results["failed_count"] += 1
                    results["failed_posts"].append({
                        "post_id": post_id,
                        "error": "post_id 為空"
                    })
                    continue
                
                try:
                    cursor.execute('DELETE FROM posts WHERE post_id = ?', (post_id,))
                    rows_affected = cursor.rowcount
                    
                    if rows_affected > 0:
                        results["success_count"] += 1
                        results["success_posts"].append(post_id)
                        
                        # 從快取中移除
                        if self._processed_ids_cache is not None:
                            self._processed_ids_cache.discard(post_id)
                        
                        self.logger.info(f"成功刪除貼文 {post_id}")
                    else:
                        results["failed_count"] += 1
                        results["failed_posts"].append({
                            "post_id": post_id,
                            "error": "找不到該貼文 ID"
                        })
                        
                except Exception as e:
                    results["failed_count"] += 1
                    results["failed_posts"].append({
                        "post_id": post_id,
                        "error": str(e)
                    })
                    self.logger.error(f"刪除貼文 {post_id} 失敗: {e}")
            
            conn.commit()
            conn.close()
            
            self.logger.info(f"批次刪除完成: 成功 {results['success_count']} 篇，失敗 {results['failed_count']} 篇")
            return results
                
        except Exception as e:
            self.logger.error(f"批次刪除貼文失敗: {e}")
            return {
                "success_count": 0,
                "failed_count": len(post_ids),
                "success_posts": [],
                "failed_posts": [{"post_id": "批次操作", "error": str(e)}]
            }

    def clear_cache(self):
        """清除快取"""
        self._processed_ids_cache = None
