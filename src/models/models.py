"""
資料模型定義
"""
from dataclasses import dataclass
from typing import Optional


@dataclass
class PostData:
    """貼文資料結構"""
    post_id: str
    author: str
    post_date: str
    post_type: str
    likes: int
    comments: int
    url: str
    content: str
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

    def to_dict(self) -> dict:
        """轉換為字典格式"""
        return {
            'post_id': self.post_id,
            'author': self.author,
            'post_date': self.post_date,
            'post_type': self.post_type,
            'likes': self.likes,
            'comments': self.comments,
            'url': self.url,
            'content': self.content,
            'created_at': self.created_at,
            'updated_at': self.updated_at
        }


@dataclass
class ExtractResult:
    """提取結果資料結構"""
    success: bool
    username: Optional[str] = None
    total_found: int = 0
    new_posts: int = 0
    skipped_posts: int = 0
    total_in_db: int = 0
    error: Optional[str] = None

    def to_dict(self) -> dict:
        """轉換為字典格式"""
        return {
            'success': self.success,
            'username': self.username,
            'total_found': self.total_found,
            'new_posts': self.new_posts,
            'skipped_posts': self.skipped_posts,
            'total_in_db': self.total_in_db,
            'error': self.error
        }


@dataclass
class UserProfile:
    """使用者個人檔案資料結構"""
    username: str
    full_name: str
    followers: int
    followees: int
    media_count: int
    biography: Optional[str] = None
    is_private: bool = False

    def to_dict(self) -> dict:
        """轉換為字典格式"""
        return {
            'username': self.username,
            'full_name': self.full_name,
            'followers': self.followers,
            'followees': self.followees,
            'media_count': self.media_count,
            'biography': self.biography,
            'is_private': self.is_private
        }
