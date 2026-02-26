"""
高速NewsFilter服務
整合新API、緩存、MongoDB數據庫和ChatGPT翻譯功能
"""

import requests
import json
import time
import asyncio
from typing import List, Dict, Any, Optional
from datetime import datetime
import os
import sys
from dotenv import load_dotenv

# 加載環境變量
load_dotenv()

from app.services.newsfilter_auth import NewsFilterAuth
from app.database.sqlite_cache import SQLiteCacheManager
from app.database.mongodb_manager import MongoDBManager
from app.utils.news_analyzer import NewsAnalyzer
from app.utils.chatgpt_translator import ChatGPTTranslator


class SuperFastNewsService:
    """超高速NewsFilter服務"""
    
    def __init__(self):
        self.api_url = os.getenv("NEWSFILTER_API_URL", "https://api.newsfilter.io/actions")
        
        # 初始化各個組件
        self.auth = NewsFilterAuth()
        self.sqlite_cache = SQLiteCacheManager()
        
        # MongoDB連接（帶錯誤處理）
        self.mongodb = None
        self._init_mongodb()
        
        # ChatGPT翻譯器
        self.translator = ChatGPTTranslator()
        
        # 新聞分析器
        self.news_analyzer = NewsAnalyzer()
        
        self.request_timeout = 30
        
        print("🚀 SuperFast NewsFilter Service initialized")
    
    def _init_mongodb(self):
        """初始化MongoDB連接，帶錯誤處理"""
        try:
            self.mongodb = MongoDBManager()
            if self.mongodb.client is None:
                print("⚠️ MongoDB connection failed, running without database persistence")
                self.mongodb = None
        except Exception as e:
            print(f"⚠️ MongoDB initialization error: {e}")
            print("⚠️ Running without MongoDB - data will only be cached locally")
            self.mongodb = None
    
    async def get_symbol_news(self, symbol: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        獲取指定股票的新聞
        
        查找順序：
        1. SQLite緩存（1小時內）
        2. MongoDB數據庫
        3. NewsFilter API
        
        如果有錯誤，返回 [{"msg": "error message"}]
        """
        
        try:
            symbol = symbol.upper()
            
            # 檢查是否處於登錄失敗狀態（同步 SQLite 狀態，避免 in-memory flag 未初始化）
            self.auth._check_login_failure_status()
            if self.auth.is_login_failed:
                remaining_time = self.auth.get_remaining_sleep_time()
                if remaining_time > 0:
                    return [{"msg": "NewsFilter Fail"}]
            
            # 1. 先檢查SQLite緩存
            print(f"🔍 Checking cache for {symbol}...")
            cached_articles = self.sqlite_cache.get_news_cache(symbol, limit)
            
            if cached_articles:
                print(f"✅ Found {len(cached_articles)} articles in cache")
                return await self._process_articles(cached_articles, symbol)
            
            # 2. 檢查MongoDB
            if self.mongodb:
                print(f"🔍 Checking MongoDB for {symbol}...")
                db_articles = self.mongodb.get_news_articles(symbol, limit)
                
                if db_articles:
                    print(f"✅ Found {len(db_articles)} articles in MongoDB")
                    # 保存到緩存
                    self.sqlite_cache.save_news_cache(symbol, db_articles)
                    return await self._process_articles(db_articles, symbol)
            
            # 3. 從NewsFilter API獲取
            print(f"🔍 Fetching from NewsFilter API for {symbol}...")
            api_articles = await self._fetch_from_api(symbol, limit)
            
            if not api_articles:
                print(f"📭 No articles found for {symbol}")
                return []
            
            # 檢查是否為錯誤訊息（例如 auth failure），不應存入緩存
            if len(api_articles) == 1 and "msg" in api_articles[0]:
                return api_articles
            
            # 保存到緩存和數據庫
            self.sqlite_cache.save_news_cache(symbol, api_articles)
            if self.mongodb:
                self.mongodb.save_news_articles(symbol, api_articles)
            
            # 處理並返回
            return await self._process_articles(api_articles, symbol)
            
        except Exception as e:
            print(f"❌ Error in get_symbol_news: {e}")
            return [{"msg": f"Error: {str(e)}"}]
    
    async def _fetch_from_api(self, symbol: str, limit: int) -> List[Dict[str, Any]]:
        """从NewsFilter API获取新闻 (异步非阻塞版本)"""
        
        # 将阻塞的requests调用放入线程池执行
        import asyncio
        loop = asyncio.get_running_loop()
        
        def _sync_request():
            """在线程中执行的同步请求逻辑"""
            headers = self.auth.get_auth_headers()
            if not headers:
                print(f"❌ Auth failed for {symbol}, no valid token")
                return [{"msg": "NewsFilter Fail"}]
            
            # 使用更广泛的查询字符串，匹配标题、描述或代码
            search_query = f'title:"{symbol}" OR description:"{symbol}" OR symbols:"{symbol}"'
            
            payload = {
                "type": "filterArticles",
                "isPublic": False,
                "queryString": search_query,
                "from": 0,
                "size": 50  # 恢复固定50个，如用户提供的示例
            }
            
            try:
                # Rate limiting
                time.sleep(0.5)  # 500ms延迟避免429错误
                
                print(f"DEBUG: Payload for {symbol}: {json.dumps(payload)}")
                # print(f"DEBUG: Headers: {str(headers)[:50]}...")
                
                response = requests.post(
                    self.api_url,
                    headers=headers,
                    json=payload,
                    timeout=self.request_timeout
                )
                
                if response.status_code == 200:
                    data = response.json()
                    # print(f"DEBUG: Response data keys: {data.keys()}")
                    articles = data.get("articles", [])
                    
                    if articles:
                        print(f"✅ API returned {len(articles)} articles for {symbol}")
                        # 截取用户需要的数量
                        return articles[:limit] if limit < len(articles) else articles
                    else:
                        print(f"📭 API returned no articles for {symbol}")
                        # 尝试降级查询：仅查询symbol
                        if 'OR' in search_query:
                            print(f"⚠️ Retrying with simple symbol query for {symbol}...")
                            time.sleep(1)
                            simple_payload = payload.copy()
                            simple_payload['queryString'] = symbol
                            retry_response = requests.post(
                                self.api_url,
                                headers=headers,
                                json=simple_payload,
                                timeout=self.request_timeout
                            )
                            if retry_response.status_code == 200:
                                retry_data = retry_response.json()
                                return retry_data.get("articles", [])
                        return []
                        
                elif response.status_code == 429:
                    print("⏳ Rate limited by API")
                    return []
                    
                elif response.status_code == 401:
                    print("🔑 Token rejected (401), attempting re-login...")
                    new_token = self.auth._login_and_get_token()
                    if new_token:
                        # 重新組建 headers 並重試一次
                        new_headers = self.auth.get_auth_headers()
                        if new_headers:
                            retry_response = requests.post(
                                self.api_url,
                                headers=new_headers,
                                json=payload,
                                timeout=self.request_timeout
                            )
                            if retry_response.status_code == 200:
                                return retry_response.json().get("articles", [])
                    print("❌ Re-login failed after 401, marking auth as failed")
                    self.auth._set_login_failure()
                    return [{"msg": "NewsFilter Fail"}]
                else:
                    print(f"❌ API error: {response.status_code} - {response.text}")
                    return []
                    
            except Exception as e:
                print(f"❌ API request exception: {e}")
                import traceback
                print(traceback.format_exc())
                return []

        # 使用run_in_executor执行同步函数
        return await loop.run_in_executor(None, _sync_request)
    
    async def _process_articles(self, articles: List[Dict[str, Any]], symbol: str) -> List[Dict[str, Any]]:
        """
        處理文章，使用ChatGPT翻譯，保持與原API相同的格式
        先過濾10天外的文章，再翻譯（避免浪費API調用）
        """
        processed_articles = []
        loop = asyncio.get_running_loop()
        
        # ====== 第一步：先過濾10天外的文章 ======
        valid_articles = []
        for article in articles:
            try:
                item = self._convert_to_legacy_format(article, symbol)
                timestamp = item.get("timestamp", 0)
                if not self._is_within_days(timestamp, 10):
                    print(f"⏰ Skipping article older than 10 days: {item.get('title', 'N/A')[:50]}...")
                    continue
                valid_articles.append((article, item))
            except Exception as e:
                print(f"⚠️ Error converting article: {e}")
                continue
        
        if not valid_articles:
            print(f"📭 No articles within 10 days for {symbol}")
            return []
        
        print(f"📰 {len(valid_articles)} articles within 10 days (filtered from {len(articles)})")
        
        # ====== 第二步：翻譯有效文章 ======
        articles_needing_update = []  # 記錄需要更新到DB的文章
        
        for original_article, item in valid_articles:
            try:
                # 使用本地分析器進行關鍵字分析
                analyzed_result = self.news_analyzer.analyze(
                    item.get("title", ""), 
                    item.get("summary", "")
                )
                
                title = item.get("title", "")
                summary = item.get("summary", "")
                existing_title_cn = item.get("title_cn")
                existing_summary_cn = item.get("summary_cn")
                
                # 檢查是否需要翻譯
                need_translate = not (existing_title_cn and existing_title_cn.strip() and existing_title_cn != title
                                     and existing_summary_cn and existing_summary_cn.strip() and existing_summary_cn != summary)
                
                if need_translate:
                    # 需要翻譯，調用ChatGPT
                    title_cn, summary_cn = await loop.run_in_executor(
                        None, 
                        self.translator.translate_news, 
                        title, 
                        summary,
                        existing_title_cn,
                        existing_summary_cn
                    )
                    # 記錄需要更新到DB的文章（帶翻譯結果）
                    articles_needing_update.append({
                        "original": original_article,
                        "title_cn": title_cn,
                        "summary_cn": summary_cn
                    })
                else:
                    # 已有翻譯，直接使用
                    title_cn = existing_title_cn
                    summary_cn = existing_summary_cn
                    print(f"✅ Skip translation (already exists): {title[:40]}...")
                
                # 構建響應格式
                news_item = {
                    "title": title,
                    "title_cn": title_cn,
                    "summary": summary,
                    "summary_cn": summary_cn,
                    "timestamp": item.get("timestamp", 0),
                    "original_time": item.get("original_time", ""),
                    "source": item.get("source", ""),
                    "link": item.get("link", ""),
                    "tickers": item.get("tickers", [symbol]),
                    "type": item.get("type", "news"),
                    "score": analyzed_result.get("score", 0),
                    "keywords": analyzed_result.get("important_keywords", [])
                }
                
                processed_articles.append(news_item)
                
            except Exception as e:
                print(f"⚠️ Error processing article: {e}")
                continue
        
        # ====== 第三步：把翻譯結果寫回MongoDB和SQLite緩存 ======
        if articles_needing_update:
            for update_item in articles_needing_update:
                original = update_item["original"]
                title_cn = update_item["title_cn"]
                summary_cn = update_item["summary_cn"]
                
                # 更新原始資料
                original["title_cn"] = title_cn
                original["summary_cn"] = summary_cn
                
                # 更新SQLite緩存
                try:
                    article_hash = self.sqlite_cache._generate_article_hash(original)
                    self.sqlite_cache.update_article_translation(article_hash, title_cn, summary_cn)
                except Exception as e:
                    print(f"⚠️ Error updating SQLite cache: {e}")
                
                # 更新MongoDB
                if self.mongodb:
                    try:
                        article_hash = self.mongodb._generate_article_hash(original)
                        self.mongodb.collection.update_one(
                            {"article_hash": article_hash},
                            {"$set": {
                                "raw_data.title_cn": title_cn,
                                "raw_data.summary_cn": summary_cn,
                                "updated_at": datetime.utcnow()
                            }}
                        )
                    except Exception as e:
                        print(f"⚠️ Error updating MongoDB: {e}")
            
            print(f"💾 Updated {len(articles_needing_update)} translations to cache/DB")
        
        return processed_articles
    
    def _convert_to_legacy_format(self, article: Dict[str, Any], symbol: str) -> Dict[str, Any]:
        """
        将新API格式转换为旧格式，以兼容现有的news_handler
        保留已有的 title_cn / summary_cn 避免重複翻譯
        """
        
        # 提取时间戳
        published = article.get("publishedAt", "") or article.get("published", "")
        timestamp = self._parse_timestamp(published)
        
        # 提取来源信息
        source_info = article.get("source", {})
        source_name = source_info.get("name", "Unknown") if isinstance(source_info, dict) else str(source_info)
        
        result = {
            "title": article.get("title", ""),
            "summary": article.get("description", "") or article.get("content", ""),
            "timestamp": timestamp,
            "original_time": published,
            "source": source_name,
            "link": article.get("url", ""),
            "tickers": [symbol],  # 使用查询的symbol
            "type": "news"
        }
        
        # 保留已有的中文翻譯（來自緩存或MongoDB）
        if article.get("title_cn"):
            result["title_cn"] = article["title_cn"]
        if article.get("summary_cn"):
            result["summary_cn"] = article["summary_cn"]
        
        return result
    
    def _is_within_days(self, timestamp: int, days: int = 10) -> bool:
        """检查时间戳是否在指定天数内"""
        if timestamp <= 0:
            return False  # 无效时间戳
        
        try:
            current_time = time.time()
            time_diff = current_time - timestamp
            days_diff = time_diff / (24 * 3600)  # 转换为天数
            
            return days_diff <= days
        except Exception as e:
            print(f"⚠️ Error checking date: {e}")
            return False
    
    def _parse_timestamp(self, date_str: str) -> int:
        """解析时间字符串为时间戳，無法解析時返回0（會被10天過濾器過濾掉）"""
        if not date_str:
            return 0  # 沒有日期 → 過濾掉
        
        try:
            # 清理常見時區格式: +0000 → +00:00
            clean_str = date_str.strip()
            import re as _re
            # 處理 +0000 或 -0500 等格式
            tz_match = _re.search(r'([+-])(\d{2})(\d{2})$', clean_str)
            if tz_match and ':' not in clean_str[-6:]:
                clean_str = clean_str[:tz_match.start()] + f"{tz_match.group(1)}{tz_match.group(2)}:{tz_match.group(3)}"
            
            # 尝试多种日期格式
            formats = [
                "%Y-%m-%dT%H:%M:%S.%fZ",
                "%Y-%m-%dT%H:%M:%SZ", 
                "%Y-%m-%d %H:%M:%S",
                "%Y-%m-%d",
                "%a, %d %b %Y %H:%M:%S %Z",
                "%a, %d %b %Y %H:%M:%S %z",
            ]
            
            for fmt in formats:
                try:
                    dt = datetime.strptime(clean_str, fmt)
                    return int(dt.timestamp())
                except ValueError:
                    continue
            
            # 嘗試 ISO 格式（帶時區）
            try:
                dt = datetime.fromisoformat(clean_str.replace('Z', '+00:00'))
                return int(dt.timestamp())
            except (ValueError, AttributeError):
                pass
            
            print(f"⚠️ Cannot parse date: {date_str}")
            return 0  # 無法解析 → 過濾掉
            
        except Exception:
            return 0  # 異常 → 過濾掉
    
    def cleanup_cache(self):
        """清理緩存和舊數據"""
        print("🧹 Cleaning up cache...")
        self.sqlite_cache.cleanup_old_cache()
        if self.mongodb:
            self.mongodb.cleanup_old_articles(days=30)
        
    def get_service_stats(self) -> Dict[str, Any]:
        """獲取服務統計信息"""
        auth_status = self.auth.get_status()
        cache_stats = self.sqlite_cache.get_cache_stats()
        
        # MongoDB統計
        if self.mongodb:
            db_stats = self.mongodb.get_stats()
        else:
            db_stats = {"status": "disconnected", "total_articles": 0, "symbol_stats": []}
        
        return {
            "auth": auth_status,
            "cache": cache_stats,
            "database": db_stats,
            "service_status": "running"
        }