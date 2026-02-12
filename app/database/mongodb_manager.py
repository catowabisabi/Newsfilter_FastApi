"""
MongoDB数据库管理类
"""

import os
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from pymongo import MongoClient
from pymongo.errors import DuplicateKeyError, PyMongoError
import hashlib
import json
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()


class MongoDBManager:
    """MongoDB数据库管理器"""
    
    def __init__(self):
        self.connection_string = os.getenv("MONGODB_CONNECTION_STRING", "mongodb://localhost:27017/newsfilter")
        self.client = None
        self.db = None
        self.collection = None
        self._connect()
    
    def _connect(self):
        """连接到MongoDB"""
        try:
            self.client = MongoClient(self.connection_string, serverSelectionTimeoutMS=5000)
            
            # 實際測試連接（ping會觸發真正的連接）
            self.client.admin.command('ping')
            
            # 提取数据库名
            db_name = self.connection_string.split('/')[-1] if '/' in self.connection_string else 'newsfilter'
            self.db = self.client[db_name]
            self.collection = self.db.news_articles
            
            # 创建唯一索引
            self.collection.create_index("article_hash", unique=True)
            self.collection.create_index([("symbol", 1), ("published_at", -1)])
            
            print(f"✅ MongoDB connected to: {db_name}")
            
        except Exception as e:
            print(f"❌ MongoDB connection failed: {e}")
            print("⚠️ Running without MongoDB - data will only be cached in SQLite")
            self.client = None
    
    def _generate_article_hash(self, article: Dict[str, Any]) -> str:
        """生成文章唯一hash"""
        # 使用标题+URL+发布时间生成唯一hash
        unique_string = f"{article.get('title', '')}{article.get('url', '')}{article.get('published', '')}"
        return hashlib.md5(unique_string.encode()).hexdigest()
    
    def save_news_articles(self, symbol: str, articles: List[Dict[str, Any]]) -> int:
        """保存新闻文章到MongoDB，去重处理"""
        if not self.client:
            return 0
        
        saved_count = 0
        
        for article in articles:
            try:
                # 准备文档
                doc = {
                    "article_hash": self._generate_article_hash(article),
                    "symbol": symbol.upper(),
                    "title": article.get("title", ""),
                    "url": article.get("url", ""),
                    "description": article.get("description", ""),
                    "published": article.get("publishedAt", "") or article.get("published", ""),
                    "published_at": self._parse_published_date(article.get("publishedAt", "") or article.get("published", "")),
                    "source": article.get("source", {}),
                    "raw_data": article,
                    "created_at": datetime.utcnow(),
                    "updated_at": datetime.utcnow()
                }
                
                # 尝试插入，如果重复则跳过
                self.collection.insert_one(doc)
                saved_count += 1
                
            except DuplicateKeyError:
                # 文章已存在，跳过
                continue
            except Exception as e:
                print(f"⚠️ Error saving article: {e}")
                continue
        
        if saved_count > 0:
            print(f"💾 Saved {saved_count} new articles for {symbol} to MongoDB")
        
        return saved_count
    
    def get_news_articles(self, symbol: str, limit: int = 10) -> List[Dict[str, Any]]:
        """从MongoDB获取新闻文章"""
        if not self.client:
            return []
        
        try:
            cursor = self.collection.find(
                {"symbol": symbol.upper()},
                {"_id": 0, "raw_data": 1}  # 只返回原始数据
            ).sort("published_at", -1).limit(limit)
            
            articles = [doc["raw_data"] for doc in cursor]
            
            if articles:
                print(f"📚 Retrieved {len(articles)} articles for {symbol} from MongoDB")
            
            return articles
            
        except Exception as e:
            print(f"❌ Error retrieving articles from MongoDB: {e}")
            return []
    
    def _parse_published_date(self, date_str: str) -> Optional[datetime]:
        """解析发布日期"""
        if not date_str:
            return None
        
        try:
            # 尝试多种日期格式
            formats = [
                "%Y-%m-%dT%H:%M:%S.%fZ",
                "%Y-%m-%dT%H:%M:%SZ", 
                "%Y-%m-%d %H:%M:%S",
                "%Y-%m-%d"
            ]
            
            for fmt in formats:
                try:
                    return datetime.strptime(date_str, fmt)
                except ValueError:
                    continue
            
            return None
            
        except Exception:
            return None
    
    def cleanup_old_articles(self, days: int = 30):
        """清理旧文章"""
        if not self.client:
            return
        
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            result = self.collection.delete_many({
                "created_at": {"$lt": cutoff_date}
            })
            
            if result.deleted_count > 0:
                print(f"🗑️ Deleted {result.deleted_count} old articles from MongoDB")
                
        except Exception as e:
            print(f"❌ Error cleaning up MongoDB: {e}")
    
    def get_stats(self) -> Dict[str, Any]:
        """获取数据库统计信息"""
        if not self.client:
            return {}
        
        try:
            total_articles = self.collection.count_documents({})
            
            # 按符号统计
            symbol_stats = list(self.collection.aggregate([
                {"$group": {
                    "_id": "$symbol", 
                    "count": {"$sum": 1},
                    "latest": {"$max": "$published_at"}
                }},
                {"$sort": {"count": -1}},
                {"$limit": 10}
            ]))
            
            return {
                "total_articles": total_articles,
                "symbol_stats": symbol_stats
            }
            
        except Exception as e:
            print(f"❌ Error getting MongoDB stats: {e}")
            return {}
    
    def close(self):
        """关闭连接"""
        if self.client:
            self.client.close()
            print("🔌 MongoDB connection closed")