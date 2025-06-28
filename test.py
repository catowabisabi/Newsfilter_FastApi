import pytest
from fastapi.testclient import TestClient
from newsfilter_api import app

client = TestClient(app)

def test_read_root():
    """
    Test the root endpoint
    """
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Welcome to NewsFilter API"}

def test_get_latest_news():
    """
    Test the latest news endpoint
    """
    response = client.get("/news/latest")
    assert response.status_code == 200
    assert isinstance(response.json(), list)
    
    # If there are news items, check their structure
    if len(response.json()) > 0:
        news_item = response.json()[0]
        assert "title" in news_item
        assert "summary" in news_item
        assert "timestamp" in news_item
        assert "source" in news_item
        assert "link" in news_item
        assert "tickers" in news_item
        assert isinstance(news_item["tickers"], list)

def test_get_news_by_symbol():
    """
    Test the symbol-specific news endpoint
    """
    test_symbol = "META"  # Using META as a test symbol
    response = client.get(f"/news/symbol/{test_symbol}")
    assert response.status_code == 200
    assert isinstance(response.json(), list)
    
    # If there are news items, check their structure and symbol
    if len(response.json()) > 0:
        news_item = response.json()[0]
        assert "title" in news_item
        assert "summary" in news_item
        assert "timestamp" in news_item
        assert "source" in news_item
        assert "link" in news_item
        assert "tickers" in news_item
        assert isinstance(news_item["tickers"], list)
        # Check if the test symbol is in the tickers list (case-insensitive)
        assert any(ticker.upper() == test_symbol.upper() for ticker in news_item["tickers"])

def test_invalid_symbol():
    """
    Test the response for an invalid symbol
    """
    invalid_symbol = "INVALID123456"
    response = client.get(f"/news/symbol/{invalid_symbol}")
    # Should either return an empty list or a 404 status
    assert response.status_code in [200, 404]
    if response.status_code == 200:
        assert len(response.json()) == 0

if __name__ == "__main__":
    pytest.main(["-v", "test.py"]) 