# SnipeVision

Never Miss Another 10x - Live trading scanner with real charts and tweet-ready signals.

## Features

- 🔍 **Live Scanner**: Real-time technical analysis scanning
- 📊 **Real Charts**: Candlestick charts with EMA indicators
- 🐦 **Tweet-Ready**: Auto-generated tweet content for sharing
- 💰 **Freemium Model**: 3 free scans, $5/mo for unlimited
- 💎 **Dual Payment**: Pay with USDC (Solana) or PayPal subscription

## Payment System

### Free Tier
- **3 free scans** per user (tracked in session state)
- After 3 scans → paywall appears

### Premium ($5/month)
- Unlimited scans
- Custom rules engine
- Tweet exports
- Two payment options:
  - **USDC on Solana**: Instant unlock via QR code
  - **PayPal**: Monthly subscription

## Deployment on Render.com

### Step 1: Prepare Your Repository
1. Push all files to GitHub
2. Make sure `requirements.txt` is up to date
3. Copy `env.example` to `.env` and fill in your keys

### Step 2: Deploy on Render

1. Go to [Render Dashboard](https://dashboard.render.com)
2. Click **"New +"** → **"Web Service"**
3. Connect your GitHub repository: `Gysbert123/Snipe-Vision`
4. Configure settings:
   - **Name**: `snipevision` (or your choice)
   - **Environment**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `streamlit run app.py --server.port=$PORT --server.address=0.0.0.0`
5. Add Environment Variables (in Render dashboard):
   ```
   SOLANA_WALLET_ADDRESS=your_wallet_address
   HELIUS_API_KEY=your_helius_key
   PAYPAL_CLIENT_ID=your_paypal_client_id
   PAYPAL_SECRET=your_paypal_secret
   PAYPAL_MODE=sandbox
   ```
6. Click **"Create Web Service"**

### Step 3: Set Up Webhooks (Optional)

For automatic payment verification, deploy the webhook service:

1. Create a new **Web Service** on Render
2. Use the same repo
3. **Start Command**: `python webhook.py`
4. **Port**: `5000`
5. Add webhook URLs to:
   - **Helius Dashboard**: `https://your-app.onrender.com/webhook/solana`
   - **PayPal Developer Dashboard**: `https://your-app.onrender.com/webhook/paypal`

### Step 4: Custom Domain (Optional)

1. In Render dashboard → Your service → **Settings** → **Custom Domains**
2. Add: `snipevision.xyz`
3. Update Namecheap DNS:
   - **Type**: A Record
   - **Host**: @
   - **Value**: `216.24.57.1` (Render's IP)
   - **Type**: CNAME
   - **Host**: www
   - **Value**: `snipe-vision.onrender.com`

## Local Development

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Copy environment variables:
```bash
cp env.example .env
# Edit .env with your keys
```

3. Run the app:
```bash
streamlit run app.py
```

## Payment Integration Setup

### Solana (USDC) Setup

1. Create a Solana wallet (Phantom, Solflare, etc.)
2. Get your wallet address
3. Sign up for [Helius API](https://helius.dev) (free tier available)
4. Add webhook in Helius dashboard pointing to your Render webhook URL
5. Set `SOLANA_WALLET_ADDRESS` and `HELIUS_API_KEY` in Render environment variables

### PayPal Setup

1. Go to [PayPal Developer Dashboard](https://developer.paypal.com)
2. Create a new app (Sandbox for testing, Live for production)
3. Get your `CLIENT_ID` and `SECRET`
4. Set up webhook in PayPal dashboard:
   - URL: `https://your-app.onrender.com/webhook/paypal`
   - Events: `BILLING.SUBSCRIPTION.*`
5. Add credentials to Render environment variables

## How It Works

The scanner analyzes multiple cryptocurrencies and stocks for:
- **Golden Cross**: EMA50 crosses above EMA200 (35 points)
- **Oversold**: RSI below 30 (25 points)
- **Volume Spike**: Volume 2x above 20-day average (20 points)

Assets with a score of 50+ are displayed as hot setups.

## Test Mode

By default, the app runs in **test/sandbox mode**:
- PayPal: Uses sandbox credentials (no real charges)
- Solana: Manual verification (auto-approve in test mode)

To enable production:
1. Set `PAYPAL_MODE=live` in environment variables
2. Use real PayPal credentials
3. Set up Helius webhook for automatic Solana verification

## Support

Built with Streamlit, Plotly, and Python. Manual TA is dead 2025.
