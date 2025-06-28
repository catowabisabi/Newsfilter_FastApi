import time
from datetime import datetime, timedelta
import pytz
from math import floor
from utils.news_handler import NewsHandler
from news_spider import NewsSpider



class NewScanner:


    @staticmethod
    def send_tg_msg(msg):
        pass
       

    @staticmethod
    def print_end_msg(symbol):
        now = datetime.now()
        scanner = NewScanner()
        if symbol:
            scanner.send_tg_msg(f"NewsFilter 對 {symbol} 的掃瞄完結. \n掃描日期為: {now}")
        else:
            scanner.send_tg_msg(f"NewsFilter 的掃瞄完結. \n掃描日期為: {now}")

    @staticmethod
    def scan_symbol_news(symbol):
        print(f"Searching today news for stock {symbol}")
        spider = NewsSpider()
       
       
        news = spider.search_symbol(symbol)
        NewScanner.print_news(news, research=True) # 會send tg

        NewScanner.print_end_msg(symbol)
        
 
        



    @staticmethod
    def run_scan():
        print(f"Starting scan at {datetime.now(pytz.timezone('US/Eastern'))}")
        spider = NewsSpider()
        
        
        try:
            news = spider.run()
            NewScanner.print_news(news)
            NewScanner.print_end_msg(symbol=None)
            
            

        except Exception as e:
            print(f"An error occurred during the scan: {e}")
    
    @staticmethod
    def print_news(news, research= False):
        news_handler = NewsHandler()
        for item in news:
                
                # handle news
                analyzed_result = news_handler.news(item, research= research)


                score = analyzed_result["score"]
                keywords = analyzed_result["important_keywords"]

                # 改為中文
                translated_text = news_handler.translate()
                cn_title = translated_text[0]
                cn_summary = translated_text[1]

                print(f"Type: {item['type']}")
                print(f"Tickers: {item['tickers']}")
                print(f"Title EN: {item['title']}")
                print(f"Title CN: {cn_title}")
                print(f"Time: {item['original_time']}")
                print(f"Timestamp: {item['timestamp']}")
                print(f"Source: {item['source']}")
                print(f"Link: {item['link']}")
                print(f"Summary EN: {item['summary']}")
                print(f"Summary CN: {cn_summary}")
                print(f"Score: {score}")
                print(f"Keywords: {keywords}")
                print("---")


    @staticmethod
    def get_next_run_time():
        est = pytz.timezone('US/Eastern')
        now = datetime.now(est)
        
        if now.hour < 6 or (now.hour == 17 and now.minute > 0) or now.hour > 17:
            # 如果當前時間在早上6點之前或下午5點之後，設置下一次運行時間為第二天早上6點
            next_run = now.replace(hour=6, minute=0, second=0, microsecond=0) + timedelta(days=1)
        else:
            # 設置為下一個15分鐘的時間點
            minute = (now.minute // 15 + 1) * 15
            next_run = now.replace(minute=minute % 60, second=0, microsecond=0)
            if minute == 60:
                next_run += timedelta(hours=1)
        
        return next_run
    
    @staticmethod
    def run():
        est = pytz.timezone('US/Eastern')
        last_message_time = None
        while True:
            current_time = datetime.now(est)
            next_run = NewScanner.get_next_run_time()
            
            # If it's time to run or we've just passed a scheduled time
            if current_time >= next_run or (next_run - current_time).total_seconds() < 60:
                print(f"Starting scan at {current_time}")


                #########################################################################################################掃描
                NewScanner.run_scan()



                # 在每次掃描後重新計算下一次運行時間
                next_run = NewScanner.get_next_run_time()
                last_message_time = None
            
            # Calculate sleep time
            sleep_seconds_show = max(0, (next_run - current_time).total_seconds())
            
            sleep_seconds_real = min(sleep_seconds_show, 60)  # Sleep for at most 60 seconds

            show_min = floor(sleep_seconds_show // 60)

            show_sec = floor(sleep_seconds_show % 60)
            
            # Only print the next scan message if it's between 6 AM and 5 PM EST
            if 4 <= current_time.hour < 17:
                print(f"Next scan scheduled for {next_run}. Sleeping for  {show_min} min  {show_sec} seconds.")
            elif last_message_time is None or (current_time - last_message_time).total_seconds() >= 3600:
                print(f"Next scan scheduled for {next_run} (4 AM EST).")
                last_message_time = current_time
            
            time.sleep(sleep_seconds_real)# Sleep for the calculated time or 60 seconds, whichever is less

    def run_scan_one_symbol():
        print(f"One Symbol -> Starting scan at {datetime.now(pytz.timezone('US/Eastern'))}")
        spider = NewsSpider()
        news_handler = NewsHandler()
        
        try:
            news = spider.run()
            
            for item in news:
                analyzed_result = news_handler.news(item)
                score = analyzed_result["score"]
                keywords = analyzed_result["important_keywords"]

                translated_text = news_handler.translate()
                cn_title = translated_text[0]
                cn_summary = translated_text[1]

                print(f"Type: {item['type']}")
                print(f"Tickers: {item['tickers']}")
                print(f"Title EN: {item['title']}")
                print(f"Title CN: {cn_title}")
                print(f"Time: {item['original_time']}")
                print(f"Timestamp: {item['timestamp']}")
                print(f"Source: {item['source']}")
                print(f"Link: {item['link']}")
                print(f"Summary EN: {item['summary']}")
                print(f"Summary CN: {cn_summary}")
                print(f"Score: {score}")
                print(f"Keywords: {keywords}")
                print("---")

        except Exception as e:
            print(f"An error occurred during the scan: {e}")




if __name__ == "__main__":
    #NewScanner.run()
    NewScanner.scan_symbol_news("META")
    
