import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.news_analyzer import NewsAnalyzer
from datetime import datetime, timedelta
import pytz
import re
#from utils.chatgpt_connect import ChatGPTConnector
import time
from translate import Translator

class NewsHandler:
    def __init__(self):
        self.news_analyzer = NewsAnalyzer()
        #self.gpt = ChatGPTConnector()

    def format_msg(self, score, keywords, news, title_cn, summary_cn):
        """Format a news message with both English and Chinese content.
        
        Args:
            score (int): News importance score
            keywords (list): List of important keywords
            news (dict): News item dictionary containing title, summary, etc.
            title_cn (str): Chinese translation of title
            summary_cn (str): Chinese translation of summary
        
        Returns:
            str: Formatted message
        """
        # Get tickers with fallback to N/A
        tickers = news.get("tickers", [])
        tickers_str = ", ".join(tickers) if tickers else "N/A"
        
        # Get news text for GPT summary
        input_text = f"{news.get('title', '')} {news.get('summary', '')}"
        #gpt_summary = self.gpt.summarize_all(input_text)
        
        # Format full message with all details
        full_msg = f"""股票: {tickers_str}
分數: {score}
關鍵字: {', '.join(keywords) if keywords else 'N/A'}
英文題目: {news.get('title', 'N/A')}
中文題目: {title_cn}
英文摘要: {news.get('summary', 'N/A')}
中文摘要: {summary_cn}
時間: {news.get('original_time', 'N/A')}
來源: {news.get('source', 'N/A')}
連結: {news.get('link', 'N/A')}"""

        # Format short message with just key info
        short_msg = f"[{tickers_str}] 時間: {news.get('original_time', 'N/A')}"

        # Return the short message format by default
        return short_msg


    def send_tg(self, score, keywords, news, title_cn, summary_cn):
        msg = self.format_msg(score, keywords, news, title_cn, summary_cn)
        self.tg.send_message(msg)
        
    def send_tg_hot_news(self, score, keywords, news, title_cn, summary_cn):
        msg = self.format_msg(score, keywords, news, title_cn, summary_cn)
        self.tg_hot_news.send_message(msg)
        
    def send_tg_msg(self, msg):
        self.tg_hot_news.send_message(msg)


    #重覆代碼
    def convert_to_timestamp(self, time_str):
        if not time_str or time_str == 'N/A':
            return int(datetime.now(pytz.timezone('Asia/Shanghai')).timestamp())

        shanghai_tz = pytz.timezone('Asia/Shanghai')
        now = datetime.now(shanghai_tz)

        try:
            # Clean up the time string
            time_str = time_str.strip()
            
            # Handle GMT+8 format
            if 'GMT+8' in time_str:
                time_str = time_str.replace('GMT+8', '').strip()
                time_match = re.search(r'(\d{1,2}):(\d{2})\s*(AM|PM)', time_str, re.IGNORECASE)
                if time_match:
                    hour = int(time_match.group(1))
                    minute = int(time_match.group(2))
                    am_pm = time_match.group(3).upper()

                    if am_pm == 'PM' and hour != 12:
                        hour += 12
                    elif am_pm == 'AM' and hour == 12:
                        hour = 0

                    dt = shanghai_tz.localize(datetime(now.year, now.month, now.day, hour, minute))
                    return int(dt.timestamp())
            else:
                # Handle format like "6/19/2025, 4:23 AM"
                if ',' in time_str:
                    date_part, time_part = time_str.split(',', 1)
                else:
                    # If no comma, try to split on space
                    parts = time_str.split()
                    date_part = parts[0] if parts else ''
                    time_part = ' '.join(parts[1:]) if len(parts) > 1 else ''

                # Clean up date part and split
                date_part = re.sub(r'[^\d/]', '', date_part)  # Remove everything except digits and /
                if not date_part:
                    return int(now.timestamp())

                date_parts = date_part.split('/')
                if len(date_parts) != 3:
                    return int(now.timestamp())

                month, day, year = map(int, date_parts)

                # Parse time part
                time_match = re.search(r'(\d{1,2}):(\d{2})\s*(AM|PM)', time_part.strip(), re.IGNORECASE)
                if time_match:
                    hour = int(time_match.group(1))
                    minute = int(time_match.group(2))
                    am_pm = time_match.group(3).upper()

                    if am_pm == 'PM' and hour != 12:
                        hour += 12
                    elif am_pm == 'AM' and hour == 12:
                        hour = 0

                    try:
                        dt = shanghai_tz.localize(datetime(year, month, day, hour, minute))
                        return int(dt.timestamp())
                    except ValueError as e:
                        print(f"Invalid date/time values: year={year}, month={month}, day={day}, hour={hour}, minute={minute}")
                        return int(now.timestamp())

            print(f"Unable to parse time string: {time_str}")
            return int(now.timestamp())
        except Exception as e:
            print(f"Error parsing datetime string '{time_str}': {e}")
            return int(now.timestamp())
        


    def is_for_today_or_yesterday(self, timestamp):
        # 獲取當前時間（EST）
        est = pytz.timezone('America/New_York')
        now = datetime.now(est)
        
        # 設置今天和昨天的開始時間
        today_start = datetime(now.year, now.month, now.day, 0, 0, 0, tzinfo=est)
        yesterday_start = today_start - timedelta(days=2)
    
        # 檢查時間戳是否在今天或昨天的範圍內
        return yesterday_start.timestamp() <= timestamp <= now.timestamp()
    
    def gpt_to_tg(self):
        print("sending to chatgpt for analysis ==========================")

        input_text = self.title + " " + self.summary
        self.msg = self.gpt.summarize(input_text)   
        
        # Create a news dictionary with the required fields
        news_dict = {
            'title': self.title,
            'summary': self.summary,
            'original_time': self.time,
            'tickers': self.tickers
        }
        
        self.msg = self.format_msg(
            score=self.score,
            keywords=self.keywords,
            news=news_dict,
            title_cn=self.title_cn,
            summary_cn=self.summary_cn
        )
        #self.send_tg_msg(self.msg)




    def news(self, item, research = False):
        self.symbol = item
        self.title = item.get('title', '')
        self.tickers = item.get('tickers', '')
        self.summary = item.get('summary', '')
        self.analyed_result = self.news_analyzer.analyze(self.title, self.summary)
        self.score = self.analyed_result["score"]
        self.keywords = self.analyed_result["important_keywords"]
        self.title_cn = self.translate_to_chinese(self.title)
        self.summary_cn = self.translate_to_chinese(self.summary)
        self.time       = item.get('original_time', 'N/A')
        self.timestamp  = self.convert_to_timestamp(self.time)
        self.is_for_today = self.is_for_today_or_yesterday(self.timestamp)
        #self.gpt = ChatGPTConnector()
        

        # research呢度
        if research :
            if self.is_for_today:
                print(f"在做research, 新聞的timestamp為{self.timestamp}")
                #if self.score >= 0:
                        #self.send_tg_hot_news(self.score, self.keywords, item,  self.title_cn, self.summary_cn)

                """ # chatgpt
                if self.score >= 0:  
                    print(f"在做research, 發送ChatGPT") 
                    self.gpt_to_tg() """
                    
            else: 
                print("不是今天的新聞")


        else:   
            if self.keywords !=[] and self.keywords !="N/A" and self.tickers !=[] and self.tickers != '' :
                if self.score > 0:
                    print ("向TG DAYTRADE 新聞 發送 MSG - NewsFilter")
                    #self.send_tg(self.score, self.keywords, item,  self.title_cn, self.summary_cn)

                if self.score >= 5:
                    print ("向TG DAYTRADE 重要 發送 MSG - NewsFilter")
                    #self.send_tg_hot_news(self.score, self.keywords, item,  self.title_cn, self.summary_cn)
                    print(f"發送ChatGPT 分析到 TG") 
                    #self.gpt_to_tg()
        

        
                
        
        
        return self.analyed_result
        



    def translate_to_chinese(self, text):
        if not text:
            return ""
        try:
            # Create a new translator instance for each translation
            translator = Translator(to_lang='zh', provider="mymemory")
            
            # Split text into smaller chunks to avoid length limits
            chunks = [text[i:i+500] for i in range(0, len(text), 500)]
            translated_chunks = []
            
            for chunk in chunks:
                try:
                    # Add a small delay between translations
                    time.sleep(0.5)
                    
                    # Translate the chunk
                    translation = translator.translate(chunk)
                    if translation:
                        translated_chunks.append(translation)
                    else:
                        translated_chunks.append(chunk)
                except Exception as e:
                    print(f"Chunk translation failed: {str(e)}")
                    translated_chunks.append(chunk)
            
            return ' '.join(translated_chunks)
        except Exception as e:
            print(f"Translation error: {str(e)}")
            return text
        
    def translate(self):
        self.title = self.translate_to_chinese(self.title)
        self.summary = self.translate_to_chinese(self.summary)
        return [self.title, self.summary]