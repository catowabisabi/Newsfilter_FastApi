from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
from news_spider import NewsSpider
from utils.news_handler import NewsHandler
import logging
import traceback

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="NewsFilter API",
    description="API for filtering and managing news from various sources",
    version="1.0.0"
)

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

@app.get("/")
async def root():
    return {"message": "Welcome to NewsFilter API"}


@app.get("/news/symbol/{symbol}", response_model=List[NewsResponse])
async def get_news_by_symbol(symbol: str):
    """
    Get news for a specific stock symbol
    """
    try:
        logger.info(f"Fetching news for symbol: {symbol}")
        spider = NewsSpider()
        news = spider.search_symbol(symbol)
        logger.info(f"Found {len(news)} news articles for {symbol}")
        
        news_handler = NewsHandler()
        processed_news = []
        
        for item in news:
            try:
                logger.info(f"Processing news item: {item.get('title', '')[:50]}...")
                analyzed_result = news_handler.news(item, research=True)
                translated_text = news_handler.translate()
                
                news_item = {
                    "title": item.get("title", ""),
                    "title_cn": translated_text[0],
                    "summary": item.get("summary", ""),
                    "summary_cn": translated_text[1],
                    "timestamp": item.get("timestamp", 0),
                    "original_time": item.get("original_time", ""),
                    "source": item.get("source", ""),
                    "link": item.get("link", ""),
                    "tickers": item.get("tickers", []),
                    "type": item.get("type", ""),
                    "score": analyzed_result.get("score", 0),
                    "keywords": analyzed_result.get("important_keywords", [])
                }
                processed_news.append(news_item)
            except Exception as item_error:
                logger.error(f"Error processing news item: {str(item_error)}")
                logger.error(traceback.format_exc())
                # Continue processing other items even if one fails
                continue
            
        if not processed_news:
            logger.warning(f"No news could be processed for symbol {symbol}")
            return []
            
        return processed_news
    except Exception as e:
        logger.error(f"Error in get_news_by_symbol: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(
            status_code=500, 
            detail=f"Internal server error while processing news for {symbol}: {str(e)}"
        )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
