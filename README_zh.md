# NewsFilter FastAPI

[English](README.md) | [中文](README_zh.md)

基于 FastAPI 的金融新闻爬取和过滤服务，从 newsfilter.io 获取实时股票相关新闻，提供中文翻译和重要性评分。

## 功能特点

- 从 newsfilter.io 实时爬取新闻
- 基于股票代码的新闻过滤
- 新闻标题和摘要的中文翻译
- 新闻重要性评分系统
- RESTful API 接口
- 完善的错误处理和日志记录

## 环境要求

- Python 3.8+
- Chrome 浏览器（用于 Selenium）
- NewsFilter.io 账号
- OpenAI API 密钥（可选，用于 GPT 分析）

## 安装步骤

1. 克隆仓库：
```bash
git clone <repository-url>
cd newsfilter_fast_api
```

2. 创建并激活虚拟环境：
```bash
python -m venv venv
# Windows
venv\Scripts\activate
# Linux/Mac
source venv/bin/activate
```

3. 安装依赖：
```bash
pip install -r requirements.txt
```

4. 设置环境变量：
```bash
cp env.example .env
```
编辑 `.env` 并填入你的凭证：
```
NewsFilter_ID=你的邮箱
NewsFilter_PW=你的密码
OPENAI_API_KEY=你的OpenAI密钥  # 可选
```

## 使用说明

### 启动 API 服务器

运行 FastAPI 服务器：
```bash
python newsfilter_api.py
```
API 将在 `http://localhost:8000` 上可用

### API 接口

#### 按股票代码获取新闻
```http
GET /news/symbol/{symbol}
```
示例：
```bash
curl http://localhost:8000/news/symbol/AAPL
```

响应格式：
```json
[
  {
    "title": "新闻标题",
    "title_cn": "中文标题",
    "summary": "新闻摘要",
    "summary_cn": "中文摘要",
    "timestamp": 1234567890,
    "original_time": "6/19/2025, 4:23 AM",
    "source": "Reuters",
    "link": "https://example.com/news",
    "tickers": ["AAPL", "TSLA"],
    "type": "latest",
    "score": 5,
    "keywords": ["财报", "增长"]
  }
]
```

### 直接运行新闻爬虫

不使用 API 直接爬取新闻：
```bash
python news_spider.py
```

## 项目结构

```
newsfilter_fast_api/
├── newsfilter_api.py    # FastAPI 应用
├── news_spider.py       # 新闻爬取逻辑
├── requirements.txt     # 项目依赖
├── utils/
│   ├── news_analyzer.py    # 新闻分析
│   ├── news_handler.py     # 新闻处理
│   ├── chatgpt_connect.py  # GPT 集成
│   └── translator.py       # 翻译工具
```

## 错误处理

API 包含全面的错误处理：
- 无效的股票代码返回空列表
- 服务器错误返回 500 状态码和错误详情
- 翻译失败时返回原文
- 日期解析错误使用当前时间戳

## 贡献指南

1. Fork 本仓库
2. 创建特性分支
3. 提交更改
4. 推送到分支
5. 创建 Pull Request

## 许可证

本项目采用 MIT 许可证 - 详见 LICENSE 文件 