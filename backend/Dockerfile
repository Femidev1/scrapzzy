FROM python:3.10-slim

# Install dependencies for Playwright Chromium
RUN apt-get update && apt-get install -y \
    wget gnupg curl unzip fonts-liberation libappindicator3-1 libasound2 \
    libatk-bridge2.0-0 libnss3 libxss1 libxcomposite1 libxrandr2 \
    libxdamage1 libgtk-3-0 libgbm1 xvfb

# Set working directory
WORKDIR /app

# Copy everything
COPY . .

# Install Python packages
RUN pip install --upgrade pip && pip install -r requirements.txt

# Install Playwright browsers
RUN playwright install --with-deps

# Expose Flask port
EXPOSE 5001

# Start server
CMD ["./start.sh"]