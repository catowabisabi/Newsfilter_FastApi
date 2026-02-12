"""
SQLite缓存数据库管理器
保留1小时内的新闻数据，管理JWT token
"""

import sqlite3
import json
import hashlib
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import os


class SQLiteCacheManager:
    """SQLite缓存管理器 - 用于临时数据和JWT存储"""
    
    def __init__(self, db_path: str = "cache.db"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """初始化数据库表"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 新闻缓存表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS news_cache (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol TEXT NOT NULL,
                article_hash TEXT UNIQUE NOT NULL,
                title TEXT,
                url TEXT,
                content TEXT,
                published_at TEXT,
                source_name TEXT,
                raw_data TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # JWT Token存储表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS jwt_tokens (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                token_type TEXT DEFAULT 'access',
                access_token TEXT,
                refresh_token TEXT,
                expires_at TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_active INTEGER DEFAULT 1
            )
        """)
        
        # 系统状态表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS system_status (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                status_key TEXT UNIQUE,
                status_value TEXT,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # 创建索引
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_news_symbol_time ON news_cache(symbol, created_at)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_news_hash ON news_cache(article_hash)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_jwt_active ON jwt_tokens(is_active, expires_at)")
        
        conn.commit()
        conn.close()
        
        print("✅ SQLite cache database initialized")
    
    def _generate_article_hash(self, article: Dict[str, Any]) -> str:
        """生成文章唯一hash"""
        unique_string = f"{article.get('title', '')}{article.get('url', '')}"
        return hashlib.md5(unique_string.encode()).hexdigest()
    
    def save_news_cache(self, symbol: str, articles: List[Dict[str, Any]]) -> int:
        """保存新闻到缓存"""
        if not articles:
            return 0
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        saved_count = 0
        
        for article in articles:
            try:
                article_hash = self._generate_article_hash(article)
                
                # 检查是否已存在
                cursor.execute("SELECT id FROM news_cache WHERE article_hash = ?", (article_hash,))
                if cursor.fetchone():
                    continue
                
                # 插入新文章
                cursor.execute("""
                    INSERT INTO news_cache 
                    (symbol, article_hash, title, url, content, published_at, source_name, raw_data)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    symbol.upper(),
                    article_hash,
                    article.get('title', ''),
                    article.get('url', ''),
                    article.get('description') or article.get('content', ''),
                    article.get('publishedAt', '') or article.get('published', ''),
                    self._extract_source_name(article.get('source', {})),
                    json.dumps(article, ensure_ascii=False)
                ))
                
                saved_count += 1
                
            except Exception as e:
                print(f"⚠️ Error saving article to cache: {e}")
                continue
        
        conn.commit()
        conn.close()
        
        if saved_count > 0:
            print(f"💾 Cached {saved_count} articles for {symbol}")
        
        return saved_count
    
    def update_article_translation(self, article_hash: str, title_cn: str, summary_cn: str):
        """更新緩存中文章的翻譯結果到raw_data"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute("SELECT raw_data FROM news_cache WHERE article_hash = ?", (article_hash,))
            row = cursor.fetchone()
            if row:
                article = json.loads(row[0])
                article["title_cn"] = title_cn
                article["summary_cn"] = summary_cn
                cursor.execute(
                    "UPDATE news_cache SET raw_data = ? WHERE article_hash = ?",
                    (json.dumps(article, ensure_ascii=False), article_hash)
                )
                conn.commit()
        except Exception as e:
            print(f"⚠️ Error updating cache translation: {e}")
        finally:
            conn.close()
    
    def get_news_cache(self, symbol: str, limit: int = 10) -> List[Dict[str, Any]]:
        """从缓存获取新闻"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                SELECT raw_data FROM news_cache 
                WHERE symbol = ? AND created_at > datetime('now', '-1 hour')
                ORDER BY created_at DESC 
                LIMIT ?
            """, (symbol.upper(), limit))
            
            articles = []
            for row in cursor.fetchall():
                try:
                    article = json.loads(row[0])
                    articles.append(article)
                except json.JSONDecodeError:
                    continue
            
            conn.close()
            
            if articles:
                print(f"📚 Retrieved {len(articles)} cached articles for {symbol}")
            
            return articles
            
        except Exception as e:
            conn.close()
            print(f"❌ Error retrieving cached articles: {e}")
            return []
    
    def cleanup_old_cache(self):
        """清理旧缓存数据"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 删除1小时前的新闻缓存
        cursor.execute("""
            DELETE FROM news_cache 
            WHERE created_at < datetime('now', '-1 hour')
        """)
        
        deleted_news = cursor.rowcount
        
        # 但是保留昨天有相同ticker的新闻
        cursor.execute("""
            DELETE FROM news_cache 
            WHERE created_at < datetime('now', '-1 day')
            AND symbol IN (
                SELECT DISTINCT symbol FROM news_cache 
                WHERE created_at > datetime('now', '-1 day')
            )
        """)
        
        conn.commit()
        conn.close()
        
        if deleted_news > 0:
            print(f"🗑️ Cleaned up {deleted_news} old cached articles")
    
    def save_jwt_token(self, access_token: str, refresh_token: str = None, expires_in: int = 86400):
        """保存JWT token"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 停用旧token
        cursor.execute("UPDATE jwt_tokens SET is_active = 0")
        
        # 计算过期时间
        expires_at = datetime.now() + timedelta(seconds=expires_in)
        
        # 插入新token
        cursor.execute("""
            INSERT INTO jwt_tokens (access_token, refresh_token, expires_at, is_active)
            VALUES (?, ?, ?, 1)
        """, (access_token, refresh_token, expires_at.isoformat()))
        
        conn.commit()
        conn.close()
        
        print("🔑 JWT token saved to cache")
    
    def get_jwt_token(self) -> Optional[Dict[str, Any]]:
        """获取有效的JWT token"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT access_token, refresh_token, expires_at 
            FROM jwt_tokens 
            WHERE is_active = 1 AND expires_at > datetime('now')
            ORDER BY created_at DESC 
            LIMIT 1
        """)
        
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return {
                "access_token": row[0],
                "refresh_token": row[1], 
                "expires_at": row[2]
            }
        
        return None
    
    def set_system_status(self, key: str, value: str):
        """设置系统状态"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT OR REPLACE INTO system_status (status_key, status_value, updated_at)
            VALUES (?, ?, datetime('now'))
        """, (key, value))
        
        conn.commit()
        conn.close()
    
    def get_system_status(self, key: str) -> Optional[str]:
        """获取系统状态"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT status_value FROM system_status WHERE status_key = ?", (key,))
        row = cursor.fetchone()
        
        conn.close()
        
        return row[0] if row else None
    
    def _extract_source_name(self, source: Any) -> str:
        """提取来源名称"""
        if isinstance(source, dict):
            return source.get('name', 'Unknown')
        elif isinstance(source, str):
            return source
        else:
            return 'Unknown'
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """获取缓存统计"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 总计数据
        cursor.execute("SELECT COUNT(*) FROM news_cache")
        total_articles = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM news_cache WHERE created_at > datetime('now', '-1 hour')")
        recent_articles = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM jwt_tokens WHERE is_active = 1")
        active_tokens = cursor.fetchone()[0]
        
        # 按符号统计
        cursor.execute("""
            SELECT symbol, COUNT(*) 
            FROM news_cache 
            WHERE created_at > datetime('now', '-1 hour')
            GROUP BY symbol 
            ORDER BY COUNT(*) DESC
        """)
        symbol_stats = cursor.fetchall()
        
        conn.close()
        
        return {
            "total_articles": total_articles,
            "recent_articles": recent_articles,
            "active_tokens": active_tokens,
            "top_symbols": dict(symbol_stats[:10])
        }