#!/usr/bin/env python3
"""
Instagram 貼文資料庫查詢工具
簡化版本，只查詢貼文資料
"""

import sqlite3
from typing import List, Dict
import argparse

DATABASE_PATH = "food_map.db"

class PostsQuery:
    def __init__(self, db_path: str):
        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = sqlite3.Row
    
    def search_by_keyword(self, keyword: str, limit: int = 5) -> List[Dict]:
        """關鍵字搜尋貼文"""
        cursor = self.conn.execute("""
            SELECT post_id, author, post_date, content
            FROM posts 
            WHERE content LIKE ? 
            ORDER BY post_date DESC 
            LIMIT ?
        """, (f"%{keyword}%", limit))
        return [dict(row) for row in cursor.fetchall()]
    
    def get_posts_by_author(self, author: str) -> List[Dict]:
        """按作者搜尋"""
        cursor = self.conn.execute("""
            SELECT post_id, post_date, post_type, likes, comments, content
            FROM posts 
            WHERE author = ? 
            ORDER BY post_date DESC
        """, (author,))
        return [dict(row) for row in cursor.fetchall()]
    
    def get_popular_posts(self, limit: int = 10) -> List[Dict]:
        """取得熱門貼文（按讚數排序）"""
        cursor = self.conn.execute("""
            SELECT post_id, author, post_date, likes, comments, content
            FROM posts 
            ORDER BY likes DESC 
            LIMIT ?
        """, (limit,))
        return [dict(row) for row in cursor.fetchall()]
    
    def get_author_statistics(self) -> List[Dict]:
        """作者統計"""
        cursor = self.conn.execute("""
            SELECT 
                author,
                COUNT(*) as post_count,
                SUM(likes) as total_likes,
                AVG(likes) as avg_likes,
                MAX(post_date) as latest_post
            FROM posts 
            GROUP BY author 
            ORDER BY post_count DESC
        """)
        return [dict(row) for row in cursor.fetchall()]
    
    def get_recent_posts(self, limit: int = 10) -> List[Dict]:
        """取得最新貼文"""
        cursor = self.conn.execute("""
            SELECT post_id, author, post_date, post_type, likes, comments, content
            FROM posts 
            ORDER BY post_date DESC 
            LIMIT ?
        """, (limit,))
        return [dict(row) for row in cursor.fetchall()]
    
    def close(self):
        self.conn.close()

def main():
    parser = argparse.ArgumentParser(description='Instagram 貼文資料庫查詢工具')
    parser.add_argument('--keyword', '-k', help='關鍵字搜尋')
    parser.add_argument('--author', '-a', help='作者搜尋')
    parser.add_argument('--popular', '-p', action='store_true', help='熱門貼文')
    parser.add_argument('--stats', '-s', action='store_true', help='作者統計')
    parser.add_argument('--recent', '-r', action='store_true', help='最新貼文')
    parser.add_argument('--limit', type=int, default=5, help='結果數量限制')
    
    args = parser.parse_args()
    
    # 如果沒有參數，顯示幫助
    if not any([args.keyword, args.author, args.popular, args.stats, args.recent]):
        parser.print_help()
        return
    
    db = PostsQuery(DATABASE_PATH)
    
    try:
        if args.keyword:
            print(f"🔍 搜尋關鍵字: {args.keyword}")
            results = db.search_by_keyword(args.keyword, args.limit)
            for post in results:
                print(f"  📅 {post['post_date']} - @{post['author']}")
                print(f"     {post['content'][:100]}...")
                print()
        
        if args.author:
            print(f"👤 作者: {args.author}")
            results = db.get_posts_by_author(args.author)
            for post in results:
                print(f"  📅 {post['post_date']} - ❤️ {post['likes']} 💬 {post['comments']}")
                print(f"     {post['content'][:80]}...")
                print()
        
        if args.popular:
            print(f"🔥 熱門貼文 (前{args.limit}名)")
            results = db.get_popular_posts(args.limit)
            for i, post in enumerate(results, 1):
                print(f"  {i}. @{post['author']} - ❤️ {post['likes']} 💬 {post['comments']}")
                print(f"     {post['content'][:80]}...")
                print()
        
        if args.stats:
            print("📊 作者統計")
            results = db.get_author_statistics()
            for author in results:
                print(f"  @{author['author']}: {author['post_count']} 篇貼文")
                print(f"     總讚數: {author['total_likes']} | 平均讚數: {author['avg_likes']:.1f}")
                print(f"     最新貼文: {author['latest_post']}")
                print()
        
        if args.recent:
            print(f"� 最新貼文 (前{args.limit}篇)")
            results = db.get_recent_posts(args.limit)
            for post in results:
                print(f"  📅 {post['post_date']} - @{post['author']}")
                print(f"     類型: {post['post_type']} | ❤️ {post['likes']} 💬 {post['comments']}")
                print(f"     {post['content'][:80]}...")
                print()
    
    finally:
        db.close()

if __name__ == "__main__":
    main()
