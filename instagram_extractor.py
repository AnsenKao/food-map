#!/usr/bin/env python3
"""
Instagram 貼文文字提取器 - 簡化版本
只將貼文資料儲存到資料庫，不處理餐廳資訊
"""

import instaloader
import getpass
import sqlite3

# ==================== 設定區 ====================
USERNAME = "corgifatgin"
DATABASE_FILE = "food_map.db"
MAX_POSTS = None  # 設為 None 表示無限制

# 可選：如果你有儲存的 session，就不需要每次重新登入
USE_SAVED_SESSION = True
# ================================================

def init_database():
    """初始化資料庫，只建立 posts 表"""
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()
    
    # 檢查是否已有 posts 表
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='posts'")
    if cursor.fetchone():
        print(f"[INFO] 使用現有資料庫: {DATABASE_FILE}")
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
        
        print(f"[INFO] 新資料庫已建立: {DATABASE_FILE}")
    
    conn.commit()
    conn.close()

def get_all_processed_ids():
    """一次性載入所有已處理的貼文 ID，回傳 set 用於快速查找"""
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()
    cursor.execute('SELECT post_id FROM posts')
    processed_ids = {row[0] for row in cursor.fetchall()}
    conn.close()
    print(f"[INFO] 載入了 {len(processed_ids)} 個已處理貼文 ID 到記憶體")
    return processed_ids

def save_post_to_db(post, processed_set):
    """將貼文資料儲存到資料庫"""
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()
    
    try:
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
        # 成功插入後，將 ID 加入到記憶體中的 set
        processed_set.add(post.shortcode)
        return True
        
    except sqlite3.IntegrityError:
        # 貼文已存在
        return False
    except Exception as e:
        print(f"       ❌ 資料庫儲存失敗: {e}")
        return False
    finally:
        conn.close()

def get_processed_count():
    """取得已處理的貼文數量"""
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()
    cursor.execute('SELECT COUNT(*) FROM posts')
    count = cursor.fetchone()[0]
    conn.close()
    return count

def login_with_2fa(loader, username):
    """支援 2FA 的登入函式"""
    print(f"[INFO] 正在登入使用者: {username}")
    
    # 嘗試載入已保存的 session
    if USE_SAVED_SESSION:
        try:
            print("[INFO] 嘗試使用已保存的 session...")
            loader.load_session_from_file(username)
            print("[SUCCESS] 成功載入已保存的 session")
            return True
        except FileNotFoundError:
            print("[INFO] 找不到已保存的 session，需要重新登入")
        except Exception as e:
            print(f"[WARNING] 載入 session 失敗: {e}")
            print("[INFO] 將進行全新登入")
    
    # 進行全新登入
    try:
        password = getpass.getpass("請輸入密碼: ")
        
        # 嘗試登入
        print("[INFO] 正在嘗試登入...")
        loader.login(username, password)
        
        print("[SUCCESS] 登入成功！")
        
        # 保存 session 供下次使用
        try:
            print("[INFO] 正在保存 session...")
            loader.save_session_to_file()
            print("[SUCCESS] Session 已保存")
        except Exception as e:
            print(f"[WARNING] 保存 session 失敗: {e}")
        
        return True
        
    except instaloader.exceptions.TwoFactorAuthRequiredException:
        print("[INFO] 需要雙重驗證 (2FA)")
        
        # 獲取 2FA 驗證碼
        two_factor_code = input("請輸入 2FA 驗證碼: ")
        
        try:
            # 使用 2FA 登入
            print("[INFO] 正在驗證 2FA 碼...")
            loader.two_factor_login(two_factor_code)
            
            print("[SUCCESS] 2FA 驗證成功！")
            
            # 保存 session
            try:
                print("[INFO] 正在保存 session...")
                loader.save_session_to_file()
                print("[SUCCESS] Session 已保存")
            except Exception as e:
                print(f"[WARNING] 保存 session 失敗: {e}")
            
            return True
            
        except Exception as e:
            print(f"[ERROR] 2FA 驗證失敗: {e}")
            return False
    
    except instaloader.exceptions.BadCredentialsException:
        print("[ERROR] 用戶名或密碼錯誤")
        return False
    
    except instaloader.exceptions.ConnectionException as e:
        print(f"[ERROR] 網路連線問題: {e}")
        return False
    
    except Exception as e:
        print(f"[ERROR] 登入失敗: {e}")
        print(f"錯誤類型: {type(e).__name__}")
        return False

def main():
    """主要執行函式"""
    
    # 初始化資料庫
    init_database()
    
    # 建立 Instaloader 實例
    loader = instaloader.Instaloader()
    
    # 關閉不需要的下載功能
    loader.download_pictures = False
    loader.download_videos = False
    loader.download_video_thumbnails = False
    loader.download_geotags = False
    loader.download_comments = False
    loader.save_metadata = False
    
    print("=== Instagram 貼文資料庫提取器 ===")
    print(f"目標使用者: {USERNAME}")
    print(f"資料庫檔案: {DATABASE_FILE}")
    print(f"最大提取數: {MAX_POSTS if MAX_POSTS else '無限制'}")
    print("提取內容: 貼文資料直接存入資料庫")
    print("=" * 50)
    
    try:
        # 登入
        if not login_with_2fa(loader, USERNAME):
            print("[ERROR] 登入失敗，程式結束")
            return
        
        # 獲取個人檔案
        print(f"\n[INFO] 正在獲取 {USERNAME} 的個人檔案...")
        profile = instaloader.Profile.from_username(loader.context, USERNAME)
        
        print("[INFO] 個人檔案資訊:")
        print(f"       全名: {profile.full_name}")
        print(f"       追蹤者: {profile.followers:,}")
        print(f"       追蹤中: {profile.followees:,}")
        print(f"       貼文數: {profile.mediacount:,}")
        
        # 顯示資料庫現有資料
        existing_count = get_processed_count()
        print(f"[INFO] 資料庫現有貼文: {existing_count} 篇")
        
        # 載入所有已處理的貼文 ID 到記憶體 (一次性查詢，大幅提升效能)
        processed_set = get_all_processed_ids()
        
        # 提取儲存貼文並直接存入資料庫
        print("\n[INFO] 開始處理儲存貼文...")
        
        count = 0
        total_found = 0
        skipped_count = 0
        
        try:
            # 獲取儲存的貼文
            print("[INFO] 正在獲取儲存貼文清單...")
            saved_posts = profile.get_saved_posts()
            
            # 先收集所有儲存貼文的 shortcode 到 set
            print("[INFO] 正在分析儲存貼文...")
            saved_posts_list = list(saved_posts)  # 轉換為 list 以便重複使用
            saved_shortcodes = {post.shortcode for post in saved_posts_list}
            total_found = len(saved_shortcodes)
            
            # 使用 set 差集直接找出需要處理的貼文
            new_shortcodes = saved_shortcodes - processed_set
            skipped_count = total_found - len(new_shortcodes)
            
            print(f"[INFO] 找到 {total_found} 篇儲存貼文，其中 {len(new_shortcodes)} 篇為新貼文")
            if skipped_count > 0:
                print(f"[INFO] 跳過 {skipped_count} 篇已處理貼文")
            
            print("[INFO] 開始處理新貼文...")
            
            # 只處理新的貼文
            for post in saved_posts_list:
                if post.shortcode not in new_shortcodes:
                    continue  # 跳過已處理的貼文
                
                if MAX_POSTS and count >= MAX_POSTS:
                    print(f"[INFO] 已達到最大處理數量 {MAX_POSTS}，停止處理")
                    break
                
                try:
                    print(f"\n[INFO] 處理第 {count + 1} 篇新貼文:")
                    print(f"       ID: {post.shortcode}")
                    print(f"       作者: @{post.owner_username}")
                    print(f"       時間: {post.date_utc}")
                    print(f"       類型: {'影片' if post.is_video else '圖片'}")
                    print(f"       互動: {post.likes:,} 讚, {post.comments:,} 留言")
                    
                    # 直接儲存到資料庫，並更新記憶體中的 processed_set
                    if save_post_to_db(post, processed_set):
                        count += 1
                        print("       ✅ 已儲存到資料庫")
                        
                        # 顯示文字內容預覽
                        if post.caption:
                            preview = post.caption[:100] + "..." if len(post.caption) > 100 else post.caption
                            print(f"       內容預覽: {preview}")
                        else:
                            print("       內容預覽: （無文字內容）")
                    else:
                        print("       ⚠️ 跳過（可能重複）")
                    
                except KeyboardInterrupt:
                    print("\n[INFO] 使用者中斷處理")
                    break
                except Exception as e:
                    print(f"       ❌ 處理失敗: {e}")
                    continue
        
        except instaloader.LoginRequiredException:
            print("[ERROR] 登入權限不足，無法存取儲存貼文")
            
        except Exception as e:
            print(f"[ERROR] 處理儲存貼文失敗: {e}")
            print(f"錯誤類型: {type(e).__name__}")
        
        # 顯示處理結果
        final_count = get_processed_count()
        new_count = final_count - existing_count
        
        if new_count > 0:
            print("\n[SUCCESS] 處理完成！")
            print(f"[INFO] 新增 {new_count} 篇貼文到資料庫")
            print(f"[INFO] 資料庫總計: {final_count} 篇貼文")
            if skipped_count > 0:
                print(f"[INFO] 跳過 {skipped_count} 篇已存在的貼文")
        elif total_found == 0:
            print("\n[INFO] 沒有找到任何儲存的貼文")
        elif skipped_count == total_found:
            print(f"\n[INFO] 所有 {total_found} 篇貼文都已在資料庫中")
        else:
            print(f"\n[INFO] 找到 {total_found} 篇儲存貼文，但沒有新增任何資料")
        
        print(f"[INFO] 資料庫檔案: {DATABASE_FILE}")
        
    except instaloader.exceptions.ProfileNotExistsException:
        print(f"[ERROR] 使用者 {USERNAME} 不存在")
    except Exception as e:
        print(f"[ERROR] 執行失敗: {e}")
        print(f"錯誤類型: {type(e).__name__}")
    
    finally:
        # 清理
        try:
            loader.close()
        except Exception:
            pass

if __name__ == "__main__":
    main()
