"""
高速NewsFilter FastAPI
使用新的NewsFilter API替换Selenium，保持原有格式和接口
"""

from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel
from typing import List, Optional
import logging
import traceback
import asyncio
import os
from contextlib import asynccontextmanager
from dotenv import load_dotenv
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

# 加载环境变量
load_dotenv()

from app.services.news_service import SuperFastNewsService
from app.services.worker_manager import NewsWorkerSystem

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 初始化服务
news_service = None
worker_system = None

# 初始化Rate Limiter
limiter = Limiter(key_func=get_remote_address)
# 每分鐘30個請求的全局限制

@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动
    global news_service, worker_system
    logger.info("🚀 Starting NewsFilter Pro API...")
    news_service = SuperFastNewsService()
    
    # 启动工作者系统 (10个worker)
    worker_system = NewsWorkerSystem(news_service, worker_count=10)
    await worker_system.start()
    
    logger.info("✅ All services initialized")
    
    yield
    
    # 关闭
    logger.info("🛑 Shutting down NewsFilter Pro API...")
    if worker_system:
        await worker_system.stop()
    if news_service:
        news_service.cleanup_cache()

# 创建FastAPI应用
app = FastAPI(
    title="NewsFilter Pro API",
    description="高速新闻过滤API - 使用真实NewsFilter API + 智能缓存 (限制: 每分鐘30請求)",
    version="2.0.0",
    lifespan=lifespan
)

# 添加Rate Limiting
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
# 保持与原API相同的响应模型
class NewsResponse(BaseModel):
    title: str
    title_cn: Optional[str]
    summary: str
    summary_cn: Optional[str]
    timestamp: int
    original_time: str
    source: str
    link: str
    tickers: List[str]
    type: str
    score: Optional[float]
    keywords: Optional[List[str]]

class ServiceStats(BaseModel):
    auth: dict
    cache: dict
    database: dict
    service_status: str

@app.get("/")
@limiter.limit("30/minute")
async def root(request: Request):
    """根路径，显示API信息"""
    return {
        "message": "Welcome to NewsFilter Pro API",
        "version": "2.0.0",
        "description": "高速新闻过滤API - 真实NewsFilter API + 智能缓存",
        "endpoints": [
            "/news/symbol/{symbol} - 获取股票新闻（与原API兼容）",
            "/news/symbol/{symbol}/fast - 高速获取股票新闻",
            "/stats - 查看服务状态",
            "/health - 健康检查"
        ]
    }

@app.get("/health")
@limiter.limit("30/minute")
async def health_check(request: Request):
    """健康检查"""
    return {"status": "healthy", "timestamp": int(asyncio.get_event_loop().time())}

@app.get("/stats", response_model=ServiceStats)
@limiter.limit("10/minute")  # 更嚴格的限制，因為這是管理端點
async def service_stats(request: Request):
    """获取服务统计信息"""
    try:
        stats = news_service.get_service_stats()
        return stats
    except Exception as e:
        logger.error(f"Error getting stats: {e}")
        raise HTTPException(status_code=500, detail=f"Stats error: {str(e)}")

@app.post("/admin/reset-auth")
@limiter.limit("5/minute")  # 管理操作更嚴格限制
async def reset_auth_failure(request: Request):
    """重置认证失败状态 (管理员功能)"""
    try:
        if news_service and hasattr(news_service, 'auth_manager'):
            news_service.auth_manager._clear_login_failure()
            return {"message": "Auth failure status cleared successfully", "status": "success"}
        else:
            raise HTTPException(status_code=503, detail="Service not available")
    except Exception as e:
        logger.error(f"Reset auth error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to reset auth: {e}")

# 保持与原API完全相同的接口
@app.get("/news/symbol/{symbol}", response_model=List[NewsResponse])
@limiter.limit("30/minute")  # 主要API端點限制
async def get_news_by_symbol(request: Request, symbol: str):
    """
    获取指定股票的新闻（与原API接口完全兼容）
    
    Args:
        symbol: 股票代码（如 TSLA, AAPL）
        
    Returns:
        新闻列表，格式与原API相同
    """
    try:
        logger.info(f"📰 Fetching news for symbol: {symbol}")
        
        # 使用Worker系统进行排队处理
        # 即使多个请求同时到达，也会进入队列由10个worker处理
        news_articles = await worker_system.process_news_request(symbol, limit=10)
        
        if not news_articles:
            logger.info(f"📭 No news found for {symbol}")
            return []
        
        # 检查是否有错误消息
        if len(news_articles) == 1 and "msg" in news_articles[0]:
            error_msg = news_articles[0]["msg"]
            logger.warning(f"⚠️ Service error for {symbol}: {error_msg}")
            
            if "NewsFilter Fail" in error_msg:
                raise HTTPException(status_code=503, detail="NewsFilter service temporarily unavailable")
            else:
                raise HTTPException(status_code=500, detail=error_msg)
        
        logger.info(f"✅ Found {len(news_articles)} news articles for {symbol}")
        return news_articles
        
    except HTTPException:
        raise  # 重新抛出HTTP异常
    except Exception as e:
        logger.error(f"❌ Error in get_news_by_symbol: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(
            status_code=500, 
            detail=f"Internal server error while processing news for {symbol}: {str(e)}"
        )

# 新增：快速获取接口
@app.get("/news/symbol/{symbol}/fast", response_model=List[NewsResponse])
@limiter.limit("20/minute")  # 快速端點稍微寬鬆的限制
async def get_news_by_symbol_fast(request: Request, symbol: str, limit: int = 20):
    """
    高速获取指定股票的新闻（更多数量，更快响应）
    
    Args:
        symbol: 股票代码（如 TSLA, AAPL）
        limit: 返回数量限制（默认20，最大50）
        
    Returns:
        新闻列表
    """
    try:
        # 限制最大数量避免过载
        limit = min(limit, 50)
        
        logger.info(f"⚡ Fast fetching {limit} news for symbol: {symbol}")
        
        news_articles = await news_service.get_symbol_news(symbol, limit=limit)
        
        if not news_articles:
            return []
        
        # 处理错误消息
        if len(news_articles) == 1 and "msg" in news_articles[0]:
            error_msg = news_articles[0]["msg"]
            if "NewsFilter Fail" in error_msg:
                raise HTTPException(status_code=503, detail="NewsFilter service temporarily unavailable")
            else:
                raise HTTPException(status_code=500, detail=error_msg)
        
        logger.info(f"⚡ Fast returned {len(news_articles)} articles for {symbol}")
        return news_articles
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error in fast endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Fast endpoint error: {str(e)}")

# 新增：缓存管理接口
@app.post("/cache/cleanup")
async def cleanup_cache():
    """清理过期缓存"""
    try:
        news_service.cleanup_cache()
        return {"message": "Cache cleanup completed", "status": "success"}
    except Exception as e:
        logger.error(f"Cache cleanup error: {e}")
        raise HTTPException(status_code=500, detail=f"Cache cleanup failed: {str(e)}")

# 处理跨域（如果需要）
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境中应该限制具体域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

if __name__ == "__main__":
    import uvicorn
    
    # 从环境变量获取端口，默认8001
    port = int(os.getenv("API_PORT", "8001"))
    
    print(f"🚀 Starting NewsFilter Pro API on port {port}")
    print("📋 Available endpoints:")
    print("   GET /news/symbol/TSLA - 获取TSLA新闻（兼容原API）")
    print("   GET /news/symbol/TSLA/fast?limit=20 - 高速获取更多新闻")
    print("   GET /stats - 查看服务状态")
    print("   GET /health - 健康检查")
    
    uvicorn.run(
        app, 
        host="0.0.0.0", 
        port=port,
        log_level="info"
    )