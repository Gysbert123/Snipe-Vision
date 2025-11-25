# SnipeVision

Never Miss Another 10x - Live trading scanner with real charts and tweet-ready signals.

## Features

- 🔍 **Live Scanner**: Real-time technical analysis scanning
- 📊 **Real Charts**: Candlestick charts with EMA indicators
- 🐦 **Tweet-Ready**: Auto-generated tweet content for sharing
- 💰 **Freemium Model**: 3 free scans, $5/mo for unlimited
- 💎 **Dual Payment**: Pay with USDC (Solana) or Lemon Squeezy checkout

## Payment System

### Free Tier
- **3 free scans** per user (tracked in session state)
- After 3 scans → paywall appears

### Premium ($5/month)
- Unlimited scans
- Custom rules engine
- Tweet exports
- Two payment options:
  - **USDC on Solana**: Instant unlock via QR code + on-chain verification
  - **Lemon Squeezy**: Hosted checkout (cards, Apple Pay, PayPal) with API verification

## Deployment on Render.com

### Step 1: Prepare Your Repository
1. Push all files to GitHub
2. Make sure `requirements.txt` is up to date
3. Copy `env.example` to `.env` and fill in your keys

### Step 1.5: Create Supabase table for subscriptions
1. Create a Supabase project (free tier is fine)
2. Add table `subscriptions` with columns:
   - `id` (uuid, default)
   - `email` (text)
   - `wallet` (text)
   - `reference` (text, unique)
   - `amount` (numeric)
   - `status` (text)
   - `paid_at` (timestamp)
   - `expires_at` (timestamp)
3. Copy `SUPABASE_URL`, `SUPABASE_SERVICE_ROLE`, `SUPABASE_ANON_KEY` into `.env`

### Step 1.6: Create Supabase table for free scan tracking
1. In the same Supabase project, add table `free_usage` with columns:
   - `email` (text, primary key)
   - `free_count` (int4, default 0)
   - `updated_at` (timestamp)
2. This tracks the total number of free scans per email across devices and refreshes.

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
   LEMON_CHECKOUT_URL=https://checkout.lemonsqueezy.com/buy/your-checkout-id
   LEMON_API_KEY=ls_sk_xxx
   LEMON_VARIANT_ID=123456
   SUPABASE_URL=...
   SUPABASE_SERVICE_ROLE=...
   SUPABASE_ANON_KEY=...
   ```
6. Click **"Create Web Service"**

### Step 3: Set Up Webhooks (Optional)

Solana payments are already verified on-chain from the UI. If you prefer to offload verification to a webhook, deploy `webhook.py` as a separate Render service and point Helius to `https://your-app.onrender.com/webhook/solana`.

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

### Lemon Squeezy Setup

1. Create a product/variant in [Lemon Squeezy](https://www.lemonsqueezy.com/) for the $5/mo subscription.
2. Copy the hosted checkout link (format: `https://checkout.lemonsqueezy.com/buy/<checkout-id>`).
3. In the Lemon Squeezy dashboard, generate an API key (Settings → API).
4. Optional: note the variant ID from the URL (`.../variants/<id>`); use it to ensure only the correct product unlocks premium.
5. Add the following to your environment variables:
   ```
   LEMON_CHECKOUT_URL=https://checkout.lemonsqueezy.com/buy/<checkout-id>
   LEMON_API_KEY=ls_sk_xxx
   LEMON_VARIANT_ID=123456
   ```
6. (Optional) Configure success/cancel URLs in Lemon if you want automatic redirects after checkout.

## How It Works

The scanner analyzes multiple cryptocurrencies and stocks for:
- **Golden Cross**: EMA50 crosses above EMA200 (35 points)
- **Oversold**: RSI below 30 (25 points)
- **Volume Spike**: Volume 2x above 20-day average (20 points)

Assets with a score of 50+ are displayed as hot setups.

## Test Mode

By default, the app runs in **manual verification mode**:
- Solana payments are checked via the Helius RPC using the transaction signature you paste.
- Lemon Squeezy orders are verified through the Lemon API when you paste your order ID.

To go live:
1. Use a real Solana wallet + Helius API key.
2. Point `LEMON_CHECKOUT_URL` at your live Lemon checkout URL and use a production API key.
3. (Optional) Deploy the webhook service for automated Solana verification.

## Support

Built with Streamlit, Plotly, and Python. Manual TA is dead 2025.
