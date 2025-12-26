# NewsFilter FastAPI

基於 FastAPI 的金融新聞爬取和過濾服務，從 newsfilter.io 獲取實時股票相關新聞，提供中文翻譯和重要性評分。

---

## 📋 項目概述

本項目提供了一個完整的新聞爬取和分析系統，包含以下核心功能：

- 實時爬取 NewsFilter.io 網站的金融新聞
- 支持按股票代碼過濾新聞
- 自動翻譯新聞標題和摘要為中文
- 使用 AI 對新聞進行重要性評分和關鍵詞提取
- RESTful API 接口，方便集成到其他系統

---

## 📁 主要文件說明

### 1. `newsfilter_api.py` - FastAPI 服務器
**功能**: 提供 RESTful API 接口，作為整個系統的對外服務入口

**主要特點**:
- 定義了 FastAPI 應用和 API 端點
- 提供按股票代碼查詢新聞的接口 (`/news/symbol/{symbol}`)
- 集成了新聞爬取、翻譯和分析功能
- 完善的錯誤處理和日誌記錄

**使用場景**: 當你需要通過 HTTP API 獲取和分析新聞時使用此文件

**啟動方式**:
```bash
python newsfilter_api.py
```
服務將在 `http://localhost:8000` 啟動

---

### 2. `news_spider.py` - 新聞爬蟲核心
**功能**: 使用 Selenium 爬取 NewsFilter.io 網站的新聞數據

**主要特點**:
- 自動化瀏覽器操作（使用 Selenium + ChromeDriver）
- 處理網站登錄認證
- 解析新聞列表和詳細信息
- 提取新聞標題、摘要、時間、來源、股票代碼等
- 支持按股票代碼搜索和獲取最新新聞

**使用場景**: 
- 需要直接爬取新聞數據
- 作為其他模組的底層數據獲取工具

**獨立使用示例**:
```python
from news_spider import NewsSpider

spider = NewsSpider()
news = spider.search_symbol("AAPL")  # 搜索 Apple 股票相關新聞
```

---

### 3. `scrape_newsfilter.py` - 新聞掃描工具
**功能**: 提供新聞掃描的高級封裝，包含自動化掃描和通知功能

**主要特點**:
- 封裝了新聞爬取的完整流程
- 支持按股票代碼掃描特定新聞
- 支持掃描所有最新新聞
- 集成了新聞處理和分析功能
- 可配置通知功能（如 Telegram 通知）

**使用場景**:
- 定時自動掃描新聞
- 批量處理多個股票代碼
- 需要掃描結果通知時

**使用示例**:
```python
from scrape_newsfilter import NewScanner

# 掃描特定股票新聞
NewScanner.scan_symbol_news("TSLA")

# 掃描所有最新新聞
NewScanner.run_scan()
```

---

### 4. `utils/` - 工具模組目錄

#### `news_handler.py`
- 處理新聞數據的格式化和轉換
- 調用翻譯和分析功能
- 統一的新聞數據處理接口

#### `translator.py`
- 提供中英文翻譯功能
- 支持標題和摘要的翻譯

#### `news_analyzer.py`
- 使用 AI（如 GPT）分析新聞重要性
- 提取關鍵詞
- 為新聞評分

#### `chatgpt_connect.py`
- 連接 OpenAI API
- 處理 GPT 請求和響應

#### `mongodb_handler.py`
- MongoDB 數據庫操作
- 新聞數據的存儲和檢索

---

## 🔧 環境配置

### Conda 環境
本項目使用 Conda 環境管理依賴，環境名稱：`Newsfilter_FastApi`

**查看所有 Conda 環境**:
```bash
conda env list
```

**創建環境**（如果還未創建）:
```bash
conda create -n Newsfilter_FastApi python=3.10
conda activate Newsfilter_FastApi
pip install -r requirements.txt
```

---

## 📦 依賴安裝

本項目依賴以下主要套件：
- **FastAPI**: Web 框架
- **Uvicorn**: ASGI 服務器
- **Selenium**: 網頁自動化工具
- **python-dotenv**: 環境變量管理
- **pymongo**: MongoDB 數據庫驅動
- **translate**: 翻譯工具
- **pytz**: 時區處理

安裝所有依賴:
```bash
pip install -r requirements.txt
```

4. Set up environment variables:
```bash
cp env.example .env
```
Edit `.env` and fill in your credentials:
```
NewsFilter_ID=your_email
NewsFilter_PW=your_password
OPENAI_API_KEY=sk-your-openai-api-key  # 可選，用於 AI 分析
```

---

## 🚀 啟動方式

### 方式一：使用批處理文件一鍵啟動（推薦）
```bash
.\start_api.bat
```

### 方式二：手動啟動
```bash
# 激活 Conda 環境
conda activate Newsfilter_FastApi

# 啟動 API 服務
python newsfilter_api.py
```

### 方式三：使用完整路徑啟動（不需要激活環境）
```bash
C:\Users\admin\anaconda3\envs\Newsfilter_FastApi\python.exe newsfilter_api.py
```

啟動成功後，訪問 `http://localhost:8000` 查看 API 文檔

---

## 📖 API 使用說明

### 1. 根路徑
```http
GET http://localhost:8000/
```
**響應**: 歡迎消息

### 2. 按股票代碼查詢新聞
```http
GET http://localhost:8000/news/symbol/{symbol}
```

**示例**:
```bash
curl http://localhost:8000/news/symbol/AAPL
```

**響應格式**:
```json
[
  {
    "title": "Apple Announces New Product Line",
    "title_cn": "蘋果宣布新產品線",
    "summary": "Apple unveiled its latest innovations...",
    "summary_cn": "蘋果公司發布了最新的創新產品...",
    "timestamp": 1702729380,
    "original_time": "12/16/2025, 10:23 AM",
    "source": "Reuters",
    "link": "https://newsfilter.io/articles/...",
    "tickers": ["AAPL"],
    "type": "latest",
    "score": 8.5,
    "keywords": ["產品發布", "創新", "收益"]
  }
]
```

### 3. API 文檔
FastAPI 自動生成的交互式文檔：
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

---

## 🛠️ 使用場景示例

### 場景 1: 監控特定股票新聞
```python
# 使用 API
import requests
response = requests.get("http://localhost:8000/news/symbol/TSLA")
news_list = response.json()

for news in news_list:
    print(f"標題: {news['title_cn']}")
    print(f"評分: {news['score']}")
    print(f"關鍵詞: {news['keywords']}")
    print("---")
```

### 場景 2: 批量掃描多個股票
```python
from scrape_newsfilter import NewScanner

symbols = ["AAPL", "TSLA", "NVDA", "MSFT"]
for symbol in symbols:
    NewScanner.scan_symbol_news(symbol)
```

### 場景 3: 直接使用爬蟲獲取數據
```python
from news_spider import NewsSpider

spider = NewsSpider()
news = spider.search_symbol("AAPL")

for item in news:
    print(item['title'])
    print(item['summary'])
```

---

## 📝 注意事項

1. **Chrome 瀏覽器**: 確保已安裝 Chrome 瀏覽器，Selenium 需要使用 ChromeDriver
2. **NewsFilter.io 帳號**: 需要有效的 NewsFilter.io 帳號才能爬取數據
3. **API Key**: 如需使用 AI 分析功能，需配置 OpenAI API Key
4. **網絡連接**: 爬取過程需要穩定的網絡連接
5. **速率限制**: 注意 NewsFilter.io 的訪問頻率限制，避免被封禁

---

## 🐛 常見問題

### 1. ModuleNotFoundError
**解決方案**: 確保已激活正確的 Conda 環境並安裝所有依賴
```bash
conda activate Newsfilter_FastApi
pip install -r requirements.txt
```

### 2. ChromeDriver 錯誤
**解決方案**: webdriver-manager 會自動下載適配的 ChromeDriver，確保網絡暢通

### 3. 登錄失敗
**解決方案**: 檢查 `.env` 文件中的 NewsFilter.io 帳號密碼是否正確

---

## 📄 授權

本項目僅供學習和研究使用，請遵守 NewsFilter.io 的使用條款。

---

## 👨‍💻 開發者信息

如有問題或建議，歡迎提交 Issue 或 Pull Request。

---

**最後更新**: 2025-12-16

## Contributing

1. Fork the repository
2. Create your feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

---

# Newsfilter Application

## English

### Overview
This project is a Python-based application designed to run in a Docker container on TrueNAS SCALE. It uses FastAPI for the backend and integrates Chrome for web scraping tasks.

### Prerequisites
- TrueNAS SCALE installed
- Docker and Docker Compose installed on TrueNAS SCALE

### Setup Instructions
1. Clone this repository to your TrueNAS SCALE system.
2. Navigate to the project directory.
3. Build and run the Docker container:
   ```bash
   docker-compose up --build -d
   ```
4. Access the application at `http://<your-truenas-ip>:8000`.

### Files
- `Dockerfile`: Defines the Docker image.
- `docker-compose.yml`: Manages the Docker container.
- `requirements.txt`: Lists Python dependencies.
- `newsfilter_api.py`: Main application entry point.

---

## 中文

### 概述
此專案是一個基於 Python 的應用程式，設計為在 TrueNAS SCALE 上的 Docker 容器中運行。它使用 FastAPI 作為後端，並整合 Chrome 進行網頁抓取任務。

### 前置需求
- 已安裝 TrueNAS SCALE
- 在 TrueNAS SCALE 上安裝 Docker 和 Docker Compose

### 設置說明
1. 將此專案克隆到您的 TrueNAS SCALE 系統。
2. 進入專案目錄。
3. 建立並運行 Docker 容器：
   ```bash
   docker-compose up --build -d
   ```
4. 通過 `http://<your-truenas-ip>:8000` 訪問應用程式。

### 文件
- `Dockerfile`：定義 Docker 映像檔。
- `docker-compose.yml`：管理 Docker 容器。
- `requirements.txt`：列出 Python 依賴項。
- `newsfilter_api.py`：應用程式的主要入口點。