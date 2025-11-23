# SnipeVision

Never Miss Another 10x - Live trading scanner with real charts and tweet-ready signals.

## Features

- 🔍 **Live Scanner**: Real-time technical analysis scanning
- 📊 **Real Charts**: Candlestick charts with EMA indicators
- 🐦 **Tweet-Ready**: Auto-generated tweet content for sharing
- 💰 **Freemium Model**: 5 free scans, $5/mo for unlimited

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Run the app:
```bash
streamlit run app.py
```

## How It Works

The scanner analyzes multiple cryptocurrencies and stocks for:
- **Golden Cross**: EMA50 crosses above EMA200 (35 points)
- **Oversold**: RSI below 30 (25 points)
- **Volume Spike**: Volume 2x above 20-day average (20 points)

Assets with a score of 50+ are displayed as hot setups.


