import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from dotenv import load_dotenv
import os
import pickle
from datetime import datetime, timedelta
import pytz
import re
#from utils.mongodb_handler import MongoDBHandler

class NewsSpider:
    def __init__(self):
        load_dotenv()
        self.uid = os.environ.get("NewsFilter_ID")
        self.upw = os.environ.get("NewsFilter_PW")
        if not self.uid:
            print ("沒有ID")
            return None

        if not self.upw:
            print ("沒有PW")
            return None

        self.news_urls = { 
            "latest": "https://newsfilter.io/latest/news",
            "fda": "https://newsfilter.io/latest/fda-approvals"
        }
        
        self.driver = None
        self.wait = None
        #self.mongodb_handler = MongoDBHandler()

    def search_symbol(self, symbol):
        target_url = f"https://newsfilter.io/search?query=symbols:%22{symbol}%22"
        try:
            print("開始")
            self.news = self.get_news(target_url=target_url)
            
            # If no news found, return empty list
            if self.news is None:
                return []
                
            # Filter for recent news only
            recent_news = [news for news in self.news if self.is_recent_news(news['timestamp'])]
            return recent_news
        finally:
            if self.driver:
                self.driver.quit()

    def setup_driver(self):
        options = webdriver.ChromeOptions()
        options.add_argument('--headless=new')  # 启用无头模式
        options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36')
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        options.add_argument('--disable-extensions')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-infobars')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-browser-side-navigation')
        options.add_argument('--disable-gpu')
        options.add_argument('--disable-software-rasterizer')
        options.add_argument('--disable-setuid-sandbox')
        options.add_argument('--remote-debugging-port=9222')
        options.add_argument('--window-size=1920,1080')
        
        service = Service(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=service, options=options)
        
        # Overwrite the `navigator.webdriver` property
        self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        
        self.wait = WebDriverWait(self.driver, 30)

    def login_and_configure(self):
        load_dotenv()
        uid = os.environ.get("NewsFilter_ID")
        upw = os.environ.get("NewsFilter_PW")

        options = webdriver.ChromeOptions()
        options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36')
        options.add_argument('--disable-blink-features=AutomationControlled')
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=options)
        try:
            
            
            wait = WebDriverWait(driver, 20)

            login_url = "https://newsfilter.io/login"
            driver.get(login_url)
            time.sleep(5)

            login_form = wait.until(EC.presence_of_element_located((By.XPATH, '//div[contains(@class, "sc-dxgOiQ")]')))
            email_field = login_form.find_element(By.ID, "sign-up-email")
            password_field = login_form.find_element(By.ID, "sign-up-password")
            
            email_field.send_keys(uid)
            password_field.send_keys(upw)

            login_button = login_form.find_element(By.XPATH, ".//button[contains(@class, 'sc-kGXeez')]")
            login_button.click()

            wait.until(EC.url_contains("newsfilter.io/latest/news"))
            print("Login successful!")

            settings_button = wait.until(EC.element_to_be_clickable((By.XPATH, '//button[contains(., "Manage View Settings")]')))
            settings_button.click()

            checkboxes = wait.until(EC.presence_of_all_elements_located((By.XPATH, '//div[contains(@class, "sc-RefOD")]/input[@type="checkbox"]')))
            for checkbox in checkboxes:
                if not checkbox.is_selected():
                    checkbox.click()

            print("All settings have been checked.")

            driver.find_element(By.TAG_NAME, 'body').click()

            time.sleep(5)

            time_elements = driver.find_elements(By.XPATH, '//span[contains(@class, "sc-htpNat")]')
            if time_elements:
                print(f"Found {len(time_elements)} time elements.")
                for element in time_elements[:5]:
                    print(f"Time: {element.text}")
            else:
                print("No time elements found. There might still be an issue.")

        except TimeoutException:
            print("Timed out waiting for an element to be present.")
        except Exception as e:
            print(f"An error occurred: {e}")
        finally:
            driver.quit()

    def login(self):
        login_url = "https://newsfilter.io/login"
        self.driver.get(login_url)
        self.wait = WebDriverWait(self.driver, 10)
        try:
            login_form = self.wait.until(EC.presence_of_element_located((By.XPATH, '//div[contains(@class, "sc-kpOJdX")]')))
            email_field = login_form.find_element(By.ID, "sign-up-email")
            password_field = login_form.find_element(By.ID, "sign-up-password")
            email_field.send_keys(self.uid)
            password_field.send_keys(self.upw)
            login_button = login_form.find_element(By.XPATH, ".//button[contains(@class, 'sc-kGXeez')]")
            login_button.click()
            time.sleep(10)
            pickle.dump(self.driver.get_cookies(), open("cookies.pkl", "wb"))
            print("Login successful, cookies saved")
            
            self.wait.until(EC.url_contains("newsfilter.io"))
            print("Login successful")

            if "newsfilter.io/latest/news" in self.driver.current_url:
                print("Login successful and redirected to news page")
            else:
                print(f"Login might be successful, but current URL is: {self.driver.current_url}")
            
        except Exception as e:
            print(f"An error occurred during login: {e}")
            print("Current page source:")
            print(self.driver.page_source)

    def configure_settings(self):
        news_pages = [
            "https://newsfilter.io/latest/news",
            "https://newsfilter.io/latest/analyst-ratings",
            "https://newsfilter.io/latest/fda-approvals"
        ]

        for page in news_pages:
            self.driver.get(page)
            time.sleep(5)
            try:
                settings_button = self.wait.until(EC.element_to_be_clickable((By.XPATH, '//button[contains(., "Manage View Settings")]')))
                settings_button.click()

                checkboxes = self.wait.until(EC.presence_of_all_elements_located((By.XPATH, '//div[contains(@class, "sc-RefOD")]/input[@type="checkbox"]')))
                for checkbox in checkboxes:
                    if not checkbox.is_selected():
                        checkbox.click()

                print(f"Settings configured on {page}")

                self.driver.find_element(By.TAG_NAME, 'body').click()
                time.sleep(2)

                return True
            except Exception as e:
                print(f"Could not configure settings on {page}: {e}")

        print("Could not find settings button on any page")
        return False

    def scroll_page(self, scrolls=1, wait_time=1):
        for i in range(scrolls):
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(wait_time)
            print(f"Scrolled {i+1} times")

    def convert_to_timestamp(self, time_str):
        shanghai_tz = pytz.timezone('Asia/Shanghai')
        now = datetime.now(shanghai_tz)
        time_str = time_str.strip()

        try:
            # 1. 清理與標準化 AM/PM 順序
            time_str = re.sub(r'\[.*?\]', '', time_str).strip()
            if '下午' in time_str:
                time_str = time_str.replace('下午', '') + ' PM'
            elif '上午' in time_str:
                time_str = time_str.replace('上午', '') + ' AM'
            
            # 把 "PM12:07" 翻轉成 "12:07 PM"
            time_str = re.sub(r'(AM|PM)\s*(\d{1,2}:\d{2})', r'\2 \1', time_str, flags=re.IGNORECASE)

            # 2. 提取時間部分 (HH:MM AM/PM)
            time_match = re.search(r'(\d{1,2}):(\d{2})\s*(AM|PM)', time_str, re.IGNORECASE)
            if not time_match:
                return int(now.timestamp())

            hour, minute, am_pm = int(time_match.group(1)), int(time_match.group(2)), time_match.group(3).upper()
            if am_pm == 'PM' and hour != 12: hour += 12
            elif am_pm == 'AM' and hour == 12: hour = 0

            # 3. 處理日期部分 (關鍵修正)
            date_match = re.search(r'(\d{4}/\d{1,2}/\d{1,2})|(\d{1,2}/\d{1,2}/\d{4})', time_str)
            
            if date_match:
                # 取得日期字串並拆分數字
                date_part = date_match.group(0)
                nums = list(map(int, re.findall(r'\d+', date_part)))
                
                # 自動判斷年月日順序
                if nums[0] > 1000: # 格式: 2026/2/9
                    year, month, day = nums[0], nums[1], nums[2]
                else: # 格式: 2/9/2026
                    month, day, year = nums[0], nums[1], nums[2]
                
                dt = shanghai_tz.localize(datetime(year, month, day, hour, minute))
            else:
                # 如果沒有日期，視為今天
                dt = shanghai_tz.localize(datetime(now.year, now.month, now.day, hour, minute))

            return int(dt.timestamp())

        except Exception as e:
            print(f"Error parsing: {e} (Raw: {time_str})")
            return int(now.timestamp())

    def is_recent_news(self, timestamp):
        shanghai_tz = pytz.timezone('Asia/Shanghai')
        now = datetime.now(shanghai_tz)
        
        # Get start of yesterday (00:00:00)
        yesterday = now - timedelta(days=1)
        yesterday_start = yesterday.replace(hour=0, minute=0, second=0, microsecond=0)
        
        # Convert timestamp to datetime
        news_time = datetime.fromtimestamp(timestamp, shanghai_tz)
        
        # Return True if the news is from today or yesterday
        return news_time >= yesterday_start

    def get_news(self, news_type="latest", target_url=None):
        self.setup_driver()
        self.login()
        if not self.configure_settings():
            print("Warning: Could not configure settings. Some data might be missing.")

        if target_url is None:
            target_url = self.news_urls[news_type]
            news_type = "stock_scan"

        news_data = []  # Initialize news_data as empty list
        try:
            self.driver.get(target_url)
            print(f"Navigated to: {target_url}")
            time.sleep(10)

            self.wait.until(EC.presence_of_element_located((By.XPATH, '//div[contains(@class, "sc-htoDjs")]')))
            self.scroll_page()

            news_articles = self.driver.find_elements(By.XPATH, '//div[contains(@class, "sc-htoDjs")]')
            print(f"Number of news articles found: {len(news_articles)}")

            for article in news_articles:
                try:
                    title = article.find_element(By.XPATH, './/div[contains(@class, "sc-gZMcBi")]//span').text
                    
                    time_element = self.get_time_element(article)
                    if not time_element:
                        print(f"Warning: Unable to find time element for article: {title}")
                        continue

                    timestamp = self.convert_to_timestamp(time_element)
                    
                    try:
                        source = article.find_element(By.XPATH, './/span[contains(@class, "sc-fjdhpX")]').text
                    except NoSuchElementException:
                        source = "Unknown"
                    
                    link = self.get_article_link(article)

                    summary = self.get_article_summary(article)

                    tickers = self.get_tickers(article)

                    news_item = {
                        "title": title,
                        "timestamp": timestamp,
                        "original_time": time_element,
                        "source": source,
                        "link": link,
                        "summary": summary,
                        "tickers": tickers,
                        "type": news_type
                    }

                    news_data.append(news_item)

                except Exception as e:
                    print(f"Error extracting article info: {e}")
                    print(f"Article HTML: {article.get_attribute('outerHTML')}")
                    continue

        except TimeoutException:
            print("Timed out waiting for news articles to load")
        except Exception as e:
            print(f"An error occurred: {e}")
        finally:
            print(f"Final URL: {self.driver.current_url}")
            if self.driver:
                self.driver.quit()
            
        return news_data  # Always return the list (empty if no news found)

    def get_time_element(self, article):
        time_xpaths = [
            './/span[contains(@class, "sc-htpNat")]',
            './/div[contains(@class, "sc-htpNat")]',
            './/*[contains(@class, "sc-htpNat")]'
        ]
        for xpath in time_xpaths:
            try:
                return article.find_element(By.XPATH, xpath).text
            except NoSuchElementException:
                continue
        return None
    
    def get_article_link(self, article):
        try:
            return article.find_element(By.TAG_NAME, 'a').get_attribute('href')
        except NoSuchElementException:
            return ""

    def get_article_summary(self, article):
        try:
            return article.find_element(By.XPATH, './/div[contains(@class, "sc-gqjmRU")]').text
        except NoSuchElementException:
            return ""

    def get_tickers(self, article):
        try:
            tickers_element = article.find_element(By.XPATH, './/div[2]/div')
            ticker_spans = tickers_element.find_elements(By.XPATH, './/span[contains(@class, "sc-bxivhb dirVGp")]')
            return [span.text for span in ticker_spans if span.text]
        except NoSuchElementException:
            return []

    def run(self):
        news_types = ["latest", "fda"]
        all_news = []
        try:
            for news_type in news_types:
                news = self.get_news(news_type)
                all_news.extend(news)
            return all_news
        finally:
            if self.driver:
                self.driver.quit()

import json
if __name__ == "__main__":
    news_spider = NewsSpider()
    news = news_spider.search_symbol("TSLA")
    print(json.dumps(news, indent=4))
    