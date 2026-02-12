# NewsFilter Pro API

高速金融新聞 API - 使用 NewsFilter API + MongoDB + ChatGPT 翻譯

---

## 📋 項目概述

本項目提供高速的金融新聞 API 服務：

- **直接調用 NewsFilter API** - 不使用 Selenium，速度大幅提升
- **10 個 Worker 並行處理** - 支持高併發請求
- **多層緩存機制** - SQLite (1小時) + MongoDB (持久存儲)
- **ChatGPT 翻譯** - 高質量中英文翻譯
- **JWT 自動管理** - Token 自動保存和刷新

---

## 🚀 快速開始

### 本地運行

```bash
# 1. 安裝依賴
pip install -r requirements.txt

# 2. 配置環境變量
cp .env.example .env
# 編輯 .env 填入你的憑證

# 3. 啟動服務
python newsfilter_api_pro.py
```

服務將在 `http://localhost:8001` 啟動

### Docker 運行

```bash
# 包含 MongoDB
docker-compose up -d
```

---

## 📁 項目結構

```
newsfilter_fastapi/
├── newsfilter_api_pro.py      # 主入口
├── app/
│   ├── services/
│   │   ├── news_service.py        # 核心新聞服務
│   │   ├── newsfilter_auth.py     # JWT 認證管理
│   │   └── worker_manager.py      # 10 Worker 排隊系統
│   ├── database/
│   │   ├── sqlite_cache.py        # SQLite 緩存 (JWT + 1小時新聞)
│   │   └── mongodb_manager.py     # MongoDB 持久存儲
│   └── utils/
│       ├── chatgpt_translator.py  # ChatGPT 翻譯器
│       └── news_analyzer.py       # 關鍵字評分
├── requirements.txt
├── docker-compose.yml
├── Dockerfile
└── .env
```

---

## 🔌 API 端點

### 獲取股票新聞
```
GET /news/symbol/{symbol}
```

**範例：**
```bash
curl http://localhost:8001/news/symbol/TSLA
```

**響應：**
```json
[
  {
    "title": "Tesla Stock Rises...",
    "title_cn": "特斯拉股價上漲...",
    "summary": "Tesla reported...",
    "summary_cn": "特斯拉報告...",
    "timestamp": 1770872706,
    "source": "CNBC",
    "link": "https://...",
    "tickers": ["TSLA"],
    "score": 6,
    "keywords": ["Positive", "Increase"]
  }
]
```

### 健康檢查
```
GET /health
```

### 服務狀態
```
GET /stats
```

返回 JWT 狀態、緩存統計、MongoDB 連接狀態

---

## ⚙️ 環境變量

在 `.env` 文件中配置：

```env
# MongoDB (可選 - 如果不連接會使用 SQLite)
MONGODB_CONNECTION_STRING=mongodb://localhost:27017/newsfilter

# NewsFilter 憑證 (必填)
NEWSFILTER_USERNAME=your_email@example.com
NEWSFILTER_PASSWORD=your_password
NEWSFILTER_CLIENT_ID=SjBbF4rTwWSXp9zuFmLsAc6tu3eYXUUD

# OpenAI API Key (可選 - 用於 ChatGPT 翻譯)
OPENAI_API_KEY=sk-your-key-here

# API 設置
API_HOST=0.0.0.0
API_PORT=8001
```

---

## 🔄 數據流程

```
請求 → Worker 排隊 → 檢查 SQLite 緩存 (1小時)
                         ↓ (沒有)
                    檢查 MongoDB
                         ↓ (沒有)
                    調用 NewsFilter API
                         ↓
                    ChatGPT 翻譯
                         ↓
                    保存到 SQLite + MongoDB
                         ↓
                    返回結果
```

---

## 🔐 JWT Token 管理

- **自動保存** - Token 保存在 SQLite 中
- **自動刷新** - 過期前 1 分鐘自動刷新
- **失敗保護** - 登錄失敗後 30 分鐘冷卻期
- **手動重置** - `POST /admin/reset-auth` 清除失敗狀態

---

## 📊 緩存策略

| 存儲 | 保留時間 | 用途 |
|------|----------|------|
| SQLite | 1 小時 | 快速緩存、JWT Token |
| MongoDB | 永久 | 歷史數據、去重 |

---

## 🐳 Docker 部署

`docker-compose.yml` 包含：
- **newsfilter** - API 服務 (port 8001)
- **mongodb** - 數據庫 (port 27017)

```bash
# 啟動
docker-compose up -d

# 查看日誌
docker-compose logs -f newsfilter

# 停止
docker-compose down
```

---

## ⚠️ 注意事項

1. **NewsFilter 帳號** - 需要有效的 NewsFilter.io 訂閱帳號
2. **Rate Limiting** - API 有請求頻率限制，系統已內置 500ms 延遲
3. **MongoDB 可選** - 如果 MongoDB 未運行，系統會顯示警告但繼續使用 SQLite
4. **ChatGPT 可選** - 如果未設置 OPENAI_API_KEY，翻譯功能將返回原文

---

## 📈 性能特點

- **10 Worker 並行** - 支持同時處理多個股票請求
- **非阻塞 I/O** - 使用 asyncio + ThreadPoolExecutor
- **智能緩存** - 1 小時內相同請求直接返回緩存
- **優雅降級** - MongoDB/ChatGPT 不可用時自動降級

---

## 📝 License

MIT License
