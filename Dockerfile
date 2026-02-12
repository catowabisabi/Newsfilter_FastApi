# NewsFilter Pro API - Lightweight Python Image
FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt /app/

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . /app

# Expose port
EXPOSE 8001

# Run application
CMD ["python", "newsfilter_api_pro.py"]
