# Use Python 3.12 slim image as base
FROM python:3.12-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV DEBIAN_FRONTEND=noninteractive

# Install system dependencies
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    ca-certificates \
    procps \
    libxss1 \
    libxrandr2 \
    libasound2 \
    libpangocairo-1.0-0 \
    libatk1.0-0 \
    libcairo-gobject2 \
    libgtk-3-0 \
    libgdk-pixbuf-2.0-0 \
    libxcomposite1 \
    libxcursor1 \
    libxdamage1 \
    libxext6 \
    libxfixes3 \
    libxi6 \
    libxrender1 \
    libxtst6 \
    libnss3 \
    libcups2 \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements and install Python dependencies
COPY pyproject.toml uv.lock ./
RUN pip install uv && uv sync

# Activate the virtual environment
ENV PATH="/app/.venv/bin:$PATH"

# Install Playwright browsers in the virtual environment
RUN uv run playwright install chromium
RUN uv run playwright install-deps chromium

# Set Playwright browser path to the user's home directory
ENV PLAYWRIGHT_BROWSERS_PATH="/root/.cache/ms-playwright"

# Copy application code
COPY . .

# Create directories for logs and temporary files
RUN mkdir -p /app/logs /app/tmp

# Set permissions
RUN chmod +x /app/sample.py

# Expose port (if needed for web interface)
EXPOSE 8000

# Default command
CMD ["python", "sample.py"]
