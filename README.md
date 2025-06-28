# NewsFilter FastAPI

[English](README.md) | [中文](README_zh.md)

A FastAPI-based service that scrapes and filters financial news from newsfilter.io. The service provides real-time stock-related news with Chinese translations and importance scoring.

## Features

- Real-time news scraping from newsfilter.io
- Stock symbol-based news filtering
- Chinese translation of news titles and summaries
- News importance scoring system
- RESTful API endpoints
- Error handling and logging

## Prerequisites

- Python 3.8+
- Chrome browser (for Selenium)
- NewsFilter.io account
- OpenAI API key (optional, for GPT analysis)

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd newsfilter_fast_api
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
# Windows
venv\Scripts\activate
# Linux/Mac
source venv/bin/activate
```

3. Install dependencies:
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
OPENAI_API_KEY=your_openai_api_key  # Optional
```

## Usage

### Starting the API Server

Run the FastAPI server:
```bash
python newsfilter_api.py
```
The API will be available at `http://localhost:8000`

### API Endpoints

#### Get News by Symbol
```http
GET /news/symbol/{symbol}
```
Example:
```bash
curl http://localhost:8000/news/symbol/AAPL
```

Response format:
```json
[
  {
    "title": "News Title",
    "title_cn": "中文标题",
    "summary": "News Summary",
    "summary_cn": "中文摘要",
    "timestamp": 1234567890,
    "original_time": "6/19/2025, 4:23 AM",
    "source": "Reuters",
    "link": "https://example.com/news",
    "tickers": ["AAPL", "TSLA"],
    "type": "latest",
    "score": 5,
    "keywords": ["Earnings", "Growth"]
  }
]
```

### Running the News Spider Directly

To scrape news without the API:
```bash
python news_spider.py
```

## Project Structure

```
newsfilter_fast_api/
├── newsfilter_api.py    # FastAPI application
├── news_spider.py       # News scraping logic
├── requirements.txt     # Project dependencies
├── utils/
│   ├── news_analyzer.py    # News analysis
│   ├── news_handler.py     # News processing
│   ├── chatgpt_connect.py  # GPT integration
│   └── translator.py       # Translation utilities
```

## Error Handling

The API includes comprehensive error handling:
- Invalid symbols return an empty list
- Server errors return 500 with error details
- Translation failures fallback to original text
- Date parsing errors use current timestamp

## Contributing

1. Fork the repository
2. Create your feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details. 