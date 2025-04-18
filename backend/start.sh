#!/bin/bash
playwright install chromium

# Build frontend
cd ../frontend
npm install
npm run build
cd ../backend

# Start scraper in background
nohup python3 kijiji_scraper.py &

# Start Flask
python3 app.py