# Base image with Python and Playwright browsers installed
FROM mcr.microsoft.com/playwright/python:v1.40.0-jammy

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install browsers (ensure they are available)
RUN playwright install chromium
RUN playwright install-deps

# Copy application code
COPY . .

# Expose the C2 API port
EXPOSE 8000

# Start the C2 server
CMD ["python", "c2_server_v3.py"]
