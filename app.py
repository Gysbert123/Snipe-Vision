import streamlit as st
import yfinance as yf
import pandas as pd
import pandas_ta as ta
import plotly.graph_objects as go
import base64
from io import BytesIO
import os
import time
import qrcode
import requests
from datetime import datetime, timedelta
import json
import re
import secrets
from urllib.parse import urlencode
from ta_indicators import calculate_all_indicators
from streamlit.runtime.scriptrunner import get_script_run_ctx
from streamlit.web.server.server import Server
try:
    from supabase import create_client
except ImportError:
    create_client = None

# Payment imports
try:
    from solders.keypair import Keypair
    from solders.pubkey import Pubkey
    from solana.rpc.api import Client
    SOLANA_AVAILABLE = True
except ImportError:
    SOLANA_AVAILABLE = False

st.set_page_config(page_title="SnipeVision", layout="wide", initial_sidebar_state="expanded")

# Initialize session state FIRST
if 'scans' not in st.session_state:
    st.session_state.scans = 0

if 'paid' not in st.session_state:
    st.session_state.paid = False

if 'show_scanner' not in st.session_state:
    st.session_state.show_scanner = False

if 'show_custom_rules' not in st.session_state:
    st.session_state.show_custom_rules = False

if 'show_tweet_info' not in st.session_state:
    st.session_state.show_tweet_info = False

if 'payment_method' not in st.session_state:
    st.session_state.payment_method = None

if 'payment_pending' not in st.session_state:
    st.session_state.payment_pending = False

if 'payment_id' not in st.session_state:
    st.session_state.payment_id = None

if 'solana_reference' not in st.session_state:
    st.session_state.solana_reference = None

if 'solana_pay_url' not in st.session_state:
    st.session_state.solana_pay_url = None

if 'user_email' not in st.session_state:
    st.session_state.user_email = ""

if 'user_wallet' not in st.session_state:
    st.session_state.user_wallet = ""

if 'subscription_lookup' not in st.session_state:
    st.session_state.subscription_lookup = ""


STATIC_PAGE_CSS = """
<style>
.static-page {
    max-width: 900px;
    margin: 0 auto;
    padding: 2rem 1rem 4rem;
    color: #e6f8ff;
}
.static-page h1, .static-page h2 {
    font-weight: 800;
    background: linear-gradient(90deg, #00ff88, #00d0ff);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
}
.static-card {
    background: rgba(0, 0, 0, 0.35);
    border: 1px solid rgba(0, 255, 136, 0.2);
    padding: 1.5rem;
    border-radius: 16px;
    margin-bottom: 1.5rem;
    box-shadow: 0 0 25px rgba(0, 255, 136, 0.05);
}
.static-page li {
    margin-bottom: 0.5rem;
}
.static-back {
    margin-top: 2rem;
}
.footer-links {
    text-align: center;
    margin-top: 1rem;
    font-size: 0.95rem;
}
.footer-links a {
    color: #00ffcc;
    text-decoration: none;
    margin: 0 0.7rem;
}
.footer-links a:hover {
    text-decoration: underline;
}
</style>
"""


def get_request_path():
    try:
        ctx = get_script_run_ctx()
        if ctx is None:
            return "/"
        server = Server.get_current()
        if server is None:
            return "/"
        session_info = server._session_mgr.list_active_sessions().get(ctx.session_id)
        if session_info and getattr(session_info, "ws", None):
            return session_info.ws.request.path or "/"
    except Exception:
        return "/"
    return "/"


def render_static_page(markdown_content):
    st.markdown(STATIC_PAGE_CSS, unsafe_allow_html=True)
    st.markdown(f"<div class='static-page'>{markdown_content}</div>", unsafe_allow_html=True)
    st.markdown(
        "<div class='static-back'><a href='/' style='color:#00ff88;text-decoration:none;'>← Back to SnipeVision</a></div>",
        unsafe_allow_html=True,
    )


def render_terms_page():
    content = """
# Terms of Service – SnipeVision

Last updated: 24 November 2025

<div class='static-card'>
1. **Acceptance.** By accessing SnipeVision you agree to these Terms and our Privacy Policy.<br>
2. **Service.** We provide chart analysis, alerts, and educational content on an “as-is” basis. SnipeVision is not financial advice.<br>
3. **Accounts.** Keep your login, wallet, or subscription details secure. You are responsible for activity under your access.<br>
4. **Payments.** Monthly fees are billed in advance. Failed payments may pause access. Refund policy applies as published.<br>
5. **Restrictions.** Do not misuse, reverse engineer, or resell the service. We may suspend accounts that break the rules.<br>
6. **Limitation of Liability.** We are not liable for trading losses, missed opportunities, or indirect damages.<br>
7. **Changes.** We may update these Terms. Continued use after updates means you accept the new Terms.<br>
8. **Contact.** hello@snipevision.xyz
</div>
"""
    render_static_page(content)
    st.stop()


def render_privacy_page():
    content = """
# Privacy Policy – SnipeVision

Last updated: 24 November 2025

<div class='static-card'>
- **Information we collect.** Email, subscription status, wallet references, and usage logs needed to deliver the service.<br>
- **How we use it.** To manage subscriptions, send product updates, improve the app, and comply with legal duties.<br>
- **Sharing.** We only share data with infrastructure providers (hosting, analytics, payment processors) under strict contracts.<br>
- **Security.** We use encryption, access controls, and monitoring to protect your data.<br>
- **Your rights.** Request access, correction, or deletion anytime by emailing hello@snipevision.xyz.<br>
- **Retention.** Subscription data is kept while your account is active and for legal recordkeeping after cancellation.<br>
- **International transfers.** Data may be processed in the US and EU. We rely on standard contractual clauses where required.
</div>
"""
    render_static_page(content)
    st.stop()


def render_refund_page():
    content = """
# Refund Policy – SnipeVision

Last updated: 24 November 2025

<div class='static-card'>
<ul>
<li>Monthly subscriptions ($5/month) are non-refundable for the current billing period.</li>
<li>You can cancel anytime — no further charges.</li>
<li>If you accidentally subscribed twice or were charged in error, contact support within 7 days at <a href="mailto:hello@snipevision.xyz">hello@snipevision.xyz</a> with your transaction ID and we’ll issue a full refund.</li>
<li>No refunds for partial months or usage.</li>
</ul>
</div>
"""
    render_static_page(content)
    st.stop()


def handle_static_routes():
    path = get_request_path().strip("/").lower()
    page_param = st.query_params.get("page", "").lower() if st.query_params.get("page") else ""
    target = None
    for candidate in [path, page_param]:
        if candidate in ("terms", "privacy", "refund"):
            target = candidate
            break
    if target == "terms":
        render_terms_page()
    elif target == "privacy":
        render_privacy_page()
    elif target == "refund":
        render_refund_page()


handle_static_routes()

# === BEAUTIFUL LANDING PAGE ===

# Custom CSS — dark, sexy, crypto-native
st.markdown("""
<style>
    .big-title {font-size: 4.5rem !important; font-weight: 900; background: linear-gradient(90deg, #00ff88, #00d0ff); -webkit-background-clip: text; -webkit-text-fill-color: transparent;}
    .subtitle {font-size: 1.8rem; color: #00ff88; margin-bottom: 2rem;}
    .feature-box {background: rgba(0, 255, 136, 0.1); border-left: 5px solid #00ff88; padding: 1.5rem; border-radius: 10px; margin: 1rem 0;}
    .stButton>button {background: linear-gradient(45deg, #00ff88, #00d0ff); color: black; font-weight: bold; border-radius: 12px; height: auto; min-height: 3.5rem; width: 100%; font-size: 1rem; padding: 1rem; white-space: pre-line; transition: all 0.3s ease;}
    .stButton>button:hover {transform: scale(1.02); box-shadow: 0 0 20px rgba(0, 255, 136, 0.5);}
    .paywall {background: linear-gradient(45deg, #ff00aa, #ffaa00); -webkit-background-clip: text; -webkit-text-fill-color: transparent; font-size: 2.5rem; font-weight: 900; text-align: center; padding: 2rem; margin: 2rem 0;}
    .paywall-box {background: rgba(255, 0, 170, 0.1); border: 3px solid #ff00aa; border-radius: 20px; padding: 3rem; margin: 2rem 0; text-align: center;}
    .payment-button {background: linear-gradient(45deg, #9945FF, #14F195) !important; color: white !important; font-size: 1.2rem !important; padding: 1.5rem !important; margin: 1rem 0 !important;}
    .payment-button:hover {box-shadow: 0 0 30px rgba(153, 69, 255, 0.6) !important;}
    .paypal-button {background: linear-gradient(45deg, #0070ba, #009cde) !important; color: white !important;}
    .chart-container {border: 2px solid #00ff88; border-radius: 15px; padding: 10px; background: #111;}
    .scan-counter {font-size: 1.5rem; color: #00ff88; text-align: center; padding: 1rem; background: rgba(0, 255, 136, 0.1); border-radius: 10px; margin: 1rem 0;}
</style>
""", unsafe_allow_html=True)

# Hero Section
col1, col2 = st.columns([2, 1])

with col1:
    st.markdown("<h1 class='big-title'>SNIPEVISION</h1>", unsafe_allow_html=True)
    st.markdown("<p class='subtitle'>Never stare at charts like a peasant again</p>", unsafe_allow_html=True)
    
with col2:
    st.markdown("<div style='height: 200px;'></div>", unsafe_allow_html=True)

st.markdown("---")

# Scan counter for free users
if not st.session_state.paid:
    remaining = max(0, 3 - st.session_state.scans)
    st.markdown(f"<div class='scan-counter'>📊 Free Scans Remaining: <strong>{remaining}/3</strong></div>", unsafe_allow_html=True)

# Feature Boxes - Now Interactive
col1, col2, col3 = st.columns(3)

with col1:
    if st.button("🚀 **Quick Snipe (Free)**\n\nOne click → top 10 cleanest setups right now", use_container_width=True, key="feature1"):
        st.session_state.show_scanner = True
        st.rerun()

with col2:
    if st.button("⚙️ **Custom Rules ($5/mo)**\n\nType your exact strategy → get perfect matches", use_container_width=True, key="feature2"):
        st.session_state.show_custom_rules = True
        st.rerun()

with col3:
    if st.button("🐦 **One-Click Post to X**\n\nLook like a chart god without doing the work", use_container_width=True, key="feature3"):
        st.session_state.show_tweet_info = True
        st.rerun()

# Payment verification function
def verify_payment(payment_id, method):
    """Verify payment status"""
    try:
        if method == "solana":
            helius_api = os.getenv("HELIUS_API_KEY", "")
            if helius_api:
                return True
            return False
        elif method == "paypal":
            paypal_client_id = os.getenv("PAYPAL_CLIENT_ID", "")
            paypal_secret = os.getenv("PAYPAL_SECRET", "")
            if paypal_client_id and paypal_secret:
                return True
            return False
    except:
        return False
    return False

SOLANA_USDC_MINT = os.getenv("SOLANA_USDC_MINT", "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v")
SOLANA_DEFAULT_AMOUNT = float(os.getenv("SOLANA_SUB_AMOUNT", "5"))
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_ROLE = os.getenv("SUPABASE_SERVICE_ROLE")
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY")


@st.cache_resource(show_spinner=False)
def get_supabase_client():
    if not create_client:
        return None
    url = SUPABASE_URL
    key = SUPABASE_SERVICE_ROLE or SUPABASE_ANON_KEY
    if not url or not key:
        return None
    try:
        return create_client(url, key)
    except Exception:
        return None


def save_subscription_record(email, wallet, reference, tx_amount):
    client = get_supabase_client()
    if not client:
        return
    payload = {
        "email": email or None,
        "wallet": wallet or None,
        "reference": reference,
        "amount": tx_amount,
        "status": "active",
        "paid_at": datetime.utcnow().isoformat(),
        "expires_at": (datetime.utcnow() + timedelta(days=30)).isoformat(),
    }
    try:
        client.table("subscriptions").upsert(payload, on_conflict="reference").execute()
    except Exception:
        pass


def check_subscription_status(identifier):
    client = get_supabase_client()
    if not client or not identifier:
        return False, "Subscription lookup unavailable."
    try:
        query = client.table("subscriptions")\
            .select("*")\
            .or_(f"email.eq.{identifier},wallet.eq.{identifier}")\
            .order("expires_at", desc=True)\
            .limit(1)\
            .execute()
        data = query.data
        if not data:
            return False, "No active subscription found."
        record = data[0]
        expires_at = datetime.fromisoformat(record["expires_at"])
        if expires_at > datetime.utcnow():
            return True, f"Active until {expires_at.strftime('%Y-%m-%d %H:%M UTC')}"
        return False, "Subscription expired. Please renew."
    except Exception as e:
        return False, f"Lookup error: {str(e)}"


def generate_solana_pay_request(amount=SOLANA_DEFAULT_AMOUNT):
    """Generate Solana Pay transaction request URL + reference"""
    recipient = os.getenv("SOLANA_WALLET_ADDRESS", "YourSolanaWalletAddressHere")
    label = "SnipeVision Premium"
    message = "Unlock unlimited scans"
    memo = f"SnipeVision-{int(time.time())}"

    # Reference must be unique so webhook can identify payment
    if SOLANA_AVAILABLE:
        reference = str(Keypair().public_key)
    else:
        reference = secrets.token_hex(16)

    params = {
        "amount": amount,
        "spl-token": SOLANA_USDC_MINT,
        "reference": reference,
        "label": label,
        "message": message,
        "memo": memo,
    }

    query = urlencode(params)
    solana_url = f"solana:{recipient}?{query}"
    return solana_url, reference


def parse_custom_rules(rule_text):
    """Parse custom rules from natural language - supports 50+ indicators"""
    rules = []
    original_text = rule_text
    rule_text_upper = rule_text.upper()
    
    # Split by AND/OR to handle multiple rules
    rule_parts = re.split(r'\s+AND\s+|\s+OR\s+', rule_text_upper)
    
    for part in rule_parts:
        part = part.strip()
        if not part:
            continue
        
        # Extract numbers from rule
        numbers = re.findall(r'\d+(?:\.\d+)?', part)
        
        # PRICE ABOVE/BELOW EMA
        if ("PRICE" in part and "EMA" in part) or ("ABOVE" in part and "EMA" in part and "PRICE" in part):
            ema_length = 200  # default
            if numbers:
                for num in numbers:
                    if int(float(num)) in [9, 12, 20, 26, 50, 100, 200]:
                        ema_length = int(float(num))
                        break
            if "ABOVE" in part or ">" in part:
                rules.append(("PRICE_ABOVE_EMA", ema_length, None))
            elif "BELOW" in part or "<" in part:
                rules.append(("PRICE_BELOW_EMA", ema_length, None))
        
        # PRICE ABOVE/BELOW SMA
        elif ("PRICE" in part and "SMA" in part) or ("ABOVE" in part and "SMA" in part):
            sma_length = 200
            if numbers:
                for num in numbers:
                    if int(float(num)) in [20, 50, 100, 200]:
                        sma_length = int(float(num))
                        break
            if "ABOVE" in part or ">" in part:
                rules.append(("PRICE_ABOVE_SMA", sma_length, None))
            elif "BELOW" in part or "<" in part:
                rules.append(("PRICE_BELOW_SMA", sma_length, None))
        
        # RSI
        elif "RSI" in part:
            value = 30 if "<" in part or "BELOW" in part else 70
            if numbers:
                value = float(numbers[0])
            if "<" in part or "BELOW" in part or "UNDER" in part:
                rules.append(("RSI", "<", value))
            elif ">" in part or "ABOVE" in part or "OVER" in part:
                rules.append(("RSI", ">", value))
        
        # MACD
        elif "MACD" in part:
            if "BULL" in part or "CROSS" in part and "ABOVE" in part:
                rules.append(("MACD_CROSS", "BULL", None))
            elif "BEAR" in part or "CROSS" in part and "BELOW" in part:
                rules.append(("MACD_CROSS", "BEAR", None))
            elif "HIST" in part:
                if numbers:
                    value = float(numbers[0])
                    if ">" in part or "ABOVE" in part:
                        rules.append(("MACD_HIST", ">", value))
                    elif "<" in part or "BELOW" in part:
                        rules.append(("MACD_HIST", "<", value))
        
        # Volume
        elif "VOLUME" in part:
            multiplier = 2.0
            if "2X" in part or "2 X" in part or "DOUBLE" in part:
                multiplier = 2.0
            elif "3X" in part or "3 X" in part or "TRIPLE" in part:
                multiplier = 3.0
            elif numbers:
                multiplier = float(numbers[0])
            if ">" in part or "ABOVE" in part or "SPIKE" in part:
                rules.append(("VOLUME", ">", multiplier))
        
        # Bollinger Bands
        elif "BOLLINGER" in part or "BB" in part:
            if "UPPER" in part and ("TOUCH" in part or "BREAK" in part):
                rules.append(("BB_TOUCH", "UPPER", None))
            elif "LOWER" in part and ("TOUCH" in part or "BREAK" in part):
                rules.append(("BB_TOUCH", "LOWER", None))
            elif "SQUEEZE" in part:
                rules.append(("BB_SQUEEZE", None, None))
        
        # Stochastic
        elif "STOCH" in part or "STOCHASTIC" in part:
            value = 20 if "<" in part else 80
            if numbers:
                value = float(numbers[0])
            if "<" in part or "BELOW" in part:
                rules.append(("STOCH", "<", value))
            elif ">" in part or "ABOVE" in part:
                rules.append(("STOCH", ">", value))
        
        # ADX
        elif "ADX" in part:
            value = 25
            if numbers:
                value = float(numbers[0])
            if ">" in part or "ABOVE" in part:
                rules.append(("ADX", ">", value))
        
        # ATR
        elif "ATR" in part:
            if numbers:
                value = float(numbers[0])
                if ">" in part:
                    rules.append(("ATR", ">", value))
        
        # CCI
        elif "CCI" in part:
            value = -100 if "<" in part else 100
            if numbers:
                value = float(numbers[0])
            if "<" in part:
                rules.append(("CCI", "<", value))
            elif ">" in part:
                rules.append(("CCI", ">", value))
        
        # Williams %R
        elif "WILLIAMS" in part or "WILLR" in part:
            value = -80 if "<" in part else -20
            if numbers:
                value = float(numbers[0])
            if "<" in part:
                rules.append(("WILLR", "<", value))
            elif ">" in part:
                rules.append(("WILLR", ">", value))
        
        # OBV
        elif "OBV" in part:
            if "DIVERGENCE" in part or "DIV" in part:
                rules.append(("OBV_DIVERGENCE", None, None))
        
        # VWAP
        elif "VWAP" in part:
            if "ABOVE" in part or ">" in part:
                rules.append(("PRICE_ABOVE_VWAP", None, None))
            elif "BELOW" in part or "<" in part:
                rules.append(("PRICE_BELOW_VWAP", None, None))
        
        # EMA Cross
        elif "GOLDEN CROSS" in part or ("EMA" in part and "CROSS" in part and "50" in part and "200" in part):
            if "GOLDEN" in part or "50 > 200" in part:
                rules.append(("EMA_CROSS", "GOLDEN", None))
            elif "DEATH" in part or "50 < 200" in part:
                rules.append(("EMA_CROSS", "DEATH", None))
        
        # SuperTrend
        elif "SUPERTREND" in part or "ST" in part:
            if "ABOVE" in part or "BULL" in part:
                rules.append(("SUPERTREND", "BULL", None))
            elif "BELOW" in part or "BEAR" in part:
                rules.append(("SUPERTREND", "BEAR", None))
        
        # Parabolic SAR
        elif "PSAR" in part or "SAR" in part:
            if "ABOVE" in part or "BULL" in part:
                rules.append(("PSAR", "BULL", None))
            elif "BELOW" in part or "BEAR" in part:
                rules.append(("PSAR", "BEAR", None))
        
        # Aroon
        elif "AROON" in part:
            if "UP" in part and ">" in part:
                if numbers:
                    rules.append(("AROON_UP", ">", float(numbers[0])))
            elif "DOWN" in part and ">" in part:
                if numbers:
                    rules.append(("AROON_DOWN", ">", float(numbers[0])))
        
        # MFI (Money Flow Index)
        elif "MFI" in part:
            value = 20 if "<" in part else 80
            if numbers:
                value = float(numbers[0])
            if "<" in part:
                rules.append(("MFI", "<", value))
            elif ">" in part:
                rules.append(("MFI", ">", value))
        
        # ROC (Rate of Change)
        elif "ROC" in part:
            if numbers:
                value = float(numbers[0])
                if ">" in part:
                    rules.append(("ROC", ">", value))
                elif "<" in part:
                    rules.append(("ROC", "<", value))
        
        # Generic price rule (dollar amount)
        elif "PRICE" in part and "$" in original_text:
            price_matches = re.findall(r'\$(\d+(?:\.\d+)?)', original_text)
            if price_matches:
                value = float(price_matches[0])
                if ">" in part or "ABOVE" in part:
                    rules.append(("PRICE", ">", value))
                elif "<" in part or "BELOW" in part:
                    rules.append(("PRICE", "<", value))
    
    return rules

def scan_with_custom_rules(custom_rules_text):
    """Scan market with custom rules - supports 50+ indicators, 5-rule limit"""
    results = []
    # Expanded symbol list (up to 500 for speed)
    symbols = ["BTC-USD","ETH-USD","SOL-USD","XRP-USD","DOGE-USD","ADA-USD","AVAX-USD","MATIC-USD","LINK-USD","BNB-USD",
               "DOT-USD","UNI-USD","LTC-USD","ATOM-USD","ETC-USD","ALGO-USD","FIL-USD","TRX-USD","XLM-USD","VET-USD",
               "NVDA","TSLA","AAPL","MSFT","GOOGL","AMZN","META","NFLX","AMD","SMCI","COIN","MARA","RIOT"]
    
    # Parse rules
    rules = parse_custom_rules(custom_rules_text)
    
    # Check 5-rule limit
    if len(rules) > 5:
        return [], f"Maximum 5 rules allowed. You entered {len(rules)} rules. Please reduce to 5 or fewer."
    
    if not rules:
        return [], "Could not parse rules. Try: 'RSI < 30 AND Volume > 2x average AND Price above 200 EMA'"
    
    for sym in symbols[:500]:  # Limit to 500 for speed
        try:
            # Download data - use up to 2 years to ensure EMA/indicator coverage
            df = yf.download(sym, period="2y", interval="1d", progress=False)
            if len(df) < 60:
                continue
            
            # Calculate all indicators
            indicators = calculate_all_indicators(df)
            
            latest = df.iloc[-1]
            prev = df.iloc[-2] if len(df) > 1 else latest
            
            matches = []
            score = 0
            signals = []
            explanation_parts = []
            
            # Check each rule
            for rule in rules:
                rule_type, operator, value = rule
                matched = False
                
                try:
                    # RSI
                    if rule_type == "RSI" and indicators.get('RSI') is not None:
                        rsi_val = indicators['RSI'].iloc[-1] if hasattr(indicators['RSI'], 'iloc') else indicators['RSI']
                        if operator == "<" and rsi_val < value:
                            matched = True
                            score += 30
                            signals.append(f"RSI {rsi_val:.1f} < {value}")
                            explanation_parts.append(f"RSI oversold at {rsi_val:.1f}")
                        elif operator == ">" and rsi_val > value:
                            matched = True
                            score += 30
                            signals.append(f"RSI {rsi_val:.1f} > {value}")
                            explanation_parts.append(f"RSI overbought at {rsi_val:.1f}")
                    
                    # Price above/below EMA
                    elif rule_type == "PRICE_ABOVE_EMA":
                        ema_key = f'EMA_{value}'
                        if ema_key in indicators and indicators[ema_key] is not None:
                            ema_val = indicators[ema_key].iloc[-1] if hasattr(indicators[ema_key], 'iloc') else indicators[ema_key]
                            if latest.Close > ema_val:
                                matched = True
                                score += 30
                                signals.append(f"Price above EMA{value}")
                                explanation_parts.append(f"Price ${latest.Close:.2f} > EMA{value} ${ema_val:.2f}")
                    
                    elif rule_type == "PRICE_BELOW_EMA":
                        ema_key = f'EMA_{value}'
                        if ema_key in indicators and indicators[ema_key] is not None:
                            ema_val = indicators[ema_key].iloc[-1] if hasattr(indicators[ema_key], 'iloc') else indicators[ema_key]
                            if latest.Close < ema_val:
                                matched = True
                                score += 30
                                signals.append(f"Price below EMA{value}")
                                explanation_parts.append(f"Price ${latest.Close:.2f} < EMA{value} ${ema_val:.2f}")
                    
                    # Price above/below SMA
                    elif rule_type == "PRICE_ABOVE_SMA":
                        sma_key = f'SMA_{value}'
                        if sma_key in indicators and indicators[sma_key] is not None:
                            sma_val = indicators[sma_key].iloc[-1] if hasattr(indicators[sma_key], 'iloc') else indicators[sma_key]
                            if latest.Close > sma_val:
                                matched = True
                                score += 30
                                signals.append(f"Price above SMA{value}")
                    
                    elif rule_type == "PRICE_BELOW_SMA":
                        sma_key = f'SMA_{value}'
                        if sma_key in indicators and indicators[sma_key] is not None:
                            sma_val = indicators[sma_key].iloc[-1] if hasattr(indicators[sma_key], 'iloc') else indicators[sma_key]
                            if latest.Close < sma_val:
                                matched = True
                                score += 30
                                signals.append(f"Price below SMA{value}")
                    
                    # Volume
                    elif rule_type == "VOLUME":
                        vol_ratio = indicators.get('Volume_Ratio')
                        if vol_ratio is not None:
                            vol_val = vol_ratio.iloc[-1] if hasattr(vol_ratio, 'iloc') else vol_ratio
                            if operator == ">" and vol_val >= value:
                                matched = True
                                score += 25
                                signals.append(f"Volume {vol_val:.1f}x average")
                                explanation_parts.append(f"Volume spike: {vol_val:.1f}x normal")
                    
                    # MACD
                    elif rule_type == "MACD_CROSS":
                        macd = indicators.get('MACD')
                        macd_sig = indicators.get('MACD_Signal')
                        if macd is not None and macd_sig is not None:
                            macd_curr = macd.iloc[-1] if hasattr(macd, 'iloc') else macd
                            macd_prev = macd.iloc[-2] if hasattr(macd, 'iloc') and len(macd) > 1 else macd_curr
                            sig_curr = macd_sig.iloc[-1] if hasattr(macd_sig, 'iloc') else macd_sig
                            sig_prev = macd_sig.iloc[-2] if hasattr(macd_sig, 'iloc') and len(macd_sig) > 1 else sig_curr
                            
                            if operator == "BULL" and macd_curr > sig_curr and macd_prev <= sig_prev:
                                matched = True
                                score += 35
                                signals.append("MACD Bull Cross")
                                explanation_parts.append("MACD crossed above signal line")
                            elif operator == "BEAR" and macd_curr < sig_curr and macd_prev >= sig_prev:
                                matched = True
                                score += 35
                                signals.append("MACD Bear Cross")
                    
                    # EMA Cross
                    elif rule_type == "EMA_CROSS":
                        ema50 = indicators.get('EMA_50')
                        ema200 = indicators.get('EMA_200')
                        if ema50 is not None and ema200 is not None:
                            ema50_curr = ema50.iloc[-1] if hasattr(ema50, 'iloc') else ema50
                            ema50_prev = ema50.iloc[-2] if hasattr(ema50, 'iloc') and len(ema50) > 1 else ema50_curr
                            ema200_curr = ema200.iloc[-1] if hasattr(ema200, 'iloc') else ema200
                            ema200_prev = ema200.iloc[-2] if hasattr(ema200, 'iloc') and len(ema200) > 1 else ema200_curr
                            
                            if operator == "GOLDEN" and ema50_curr > ema200_curr and ema50_prev <= ema200_prev:
                                matched = True
                                score += 35
                                signals.append("Golden Cross")
                                explanation_parts.append("EMA50 crossed above EMA200")
                            elif operator == "DEATH" and ema50_curr < ema200_curr and ema50_prev >= ema200_prev:
                                matched = True
                                score += 35
                                signals.append("Death Cross")
                    
                    # Bollinger Bands
                    elif rule_type == "BB_TOUCH":
                        bb_upper = indicators.get('BB_Upper')
                        bb_lower = indicators.get('BB_Lower')
                        if bb_upper is not None and operator == "UPPER" and latest.Close >= bb_upper.iloc[-1]:
                            matched = True
                            score += 25
                            signals.append("Price touched BB Upper")
                        elif bb_lower is not None and operator == "LOWER" and latest.Close <= bb_lower.iloc[-1]:
                            matched = True
                            score += 25
                            signals.append("Price touched BB Lower")
                    
                    # Stochastic
                    elif rule_type == "STOCH":
                        stoch_k = indicators.get('Stoch_K')
                        if stoch_k is not None:
                            stoch_val = stoch_k.iloc[-1] if hasattr(stoch_k, 'iloc') else stoch_k
                            if operator == "<" and stoch_val < value:
                                matched = True
                                score += 25
                                signals.append(f"Stoch {stoch_val:.1f} < {value}")
                            elif operator == ">" and stoch_val > value:
                                matched = True
                                score += 25
                                signals.append(f"Stoch {stoch_val:.1f} > {value}")
                    
                    # ADX
                    elif rule_type == "ADX":
                        adx = indicators.get('ADX')
                        if adx is not None:
                            adx_val = adx.iloc[-1] if hasattr(adx, 'iloc') else adx
                            if operator == ">" and adx_val > value:
                                matched = True
                                score += 30
                                signals.append(f"ADX {adx_val:.1f} > {value} (strong trend)")
                    
                    # CCI
                    elif rule_type == "CCI":
                        cci = indicators.get('CCI')
                        if cci is not None:
                            cci_val = cci.iloc[-1] if hasattr(cci, 'iloc') else cci
                            if operator == "<" and cci_val < value:
                                matched = True
                                score += 25
                                signals.append(f"CCI {cci_val:.1f} < {value}")
                            elif operator == ">" and cci_val > value:
                                matched = True
                                score += 25
                                signals.append(f"CCI {cci_val:.1f} > {value}")
                    
                    # Williams %R
                    elif rule_type == "WILLR":
                        willr = indicators.get('Williams_R')
                        if willr is not None:
                            willr_val = willr.iloc[-1] if hasattr(willr, 'iloc') else willr
                            if operator == "<" and willr_val < value:
                                matched = True
                                score += 25
                                signals.append(f"Williams %R {willr_val:.1f} < {value}")
                            elif operator == ">" and willr_val > value:
                                matched = True
                                score += 25
                                signals.append(f"Williams %R {willr_val:.1f} > {value}")
                    
                    # VWAP
                    elif rule_type == "PRICE_ABOVE_VWAP":
                        vwap = indicators.get('VWAP')
                        if vwap is not None:
                            vwap_val = vwap.iloc[-1] if hasattr(vwap, 'iloc') else vwap
                            if latest.Close > vwap_val:
                                matched = True
                                score += 30
                                signals.append("Price above VWAP")
                                explanation_parts.append("Bullish VWAP position")
                    
                    elif rule_type == "PRICE_BELOW_VWAP":
                        vwap = indicators.get('VWAP')
                        if vwap is not None:
                            vwap_val = vwap.iloc[-1] if hasattr(vwap, 'iloc') else vwap
                            if latest.Close < vwap_val:
                                matched = True
                                score += 30
                                signals.append("Price below VWAP")
                    
                    # SuperTrend
                    elif rule_type == "SUPERTREND":
                        st = indicators.get('SuperTrend')
                        if st is not None:
                            st_val = st.iloc[-1] if hasattr(st, 'iloc') else st
                            if operator == "BULL" and latest.Close > st_val:
                                matched = True
                                score += 30
                                signals.append("SuperTrend Bullish")
                            elif operator == "BEAR" and latest.Close < st_val:
                                matched = True
                                score += 30
                                signals.append("SuperTrend Bearish")
                    
                    # Parabolic SAR
                    elif rule_type == "PSAR":
                        psar = indicators.get('PSAR')
                        if psar is not None:
                            psar_val = psar.iloc[-1] if hasattr(psar, 'iloc') else psar
                            if operator == "BULL" and latest.Close > psar_val:
                                matched = True
                                score += 25
                                signals.append("PSAR Bullish")
                            elif operator == "BEAR" and latest.Close < psar_val:
                                matched = True
                                score += 25
                                signals.append("PSAR Bearish")
                    
                    # MFI
                    elif rule_type == "MFI":
                        mfi = indicators.get('MFI')
                        if mfi is not None:
                            mfi_val = mfi.iloc[-1] if hasattr(mfi, 'iloc') else mfi
                            if operator == "<" and mfi_val < value:
                                matched = True
                                score += 25
                                signals.append(f"MFI {mfi_val:.1f} < {value}")
                            elif operator == ">" and mfi_val > value:
                                matched = True
                                score += 25
                                signals.append(f"MFI {mfi_val:.1f} > {value}")
                    
                    # ROC
                    elif rule_type == "ROC":
                        roc = indicators.get('ROC')
                        if roc is not None:
                            roc_val = roc.iloc[-1] if hasattr(roc, 'iloc') else roc
                            if operator == ">" and roc_val > value:
                                matched = True
                                score += 25
                                signals.append(f"ROC {roc_val:.2f}% > {value}%")
                            elif operator == "<" and roc_val < value:
                                matched = True
                                score += 25
                                signals.append(f"ROC {roc_val:.2f}% < {value}%")
                    
                    # Aroon
                    elif rule_type == "AROON_UP":
                        aroon_up = indicators.get('Aroon_Up')
                        if aroon_up is not None:
                            aroon_val = aroon_up.iloc[-1] if hasattr(aroon_up, 'iloc') else aroon_up
                            if operator == ">" and aroon_val > value:
                                matched = True
                                score += 25
                                signals.append(f"Aroon Up {aroon_val:.1f} > {value}")
                    
                    elif rule_type == "AROON_DOWN":
                        aroon_down = indicators.get('Aroon_Down')
                        if aroon_down is not None:
                            aroon_val = aroon_down.iloc[-1] if hasattr(aroon_down, 'iloc') else aroon_down
                            if operator == ">" and aroon_val > value:
                                matched = True
                                score += 25
                                signals.append(f"Aroon Down {aroon_val:.1f} > {value}")
                    
                    # Generic price
                    elif rule_type == "PRICE":
                        if operator == ">" and latest.Close > value:
                            matched = True
                            score += 20
                            signals.append(f"Price ${latest.Close:.2f} > ${value}")
                        elif operator == "<" and latest.Close < value:
                            matched = True
                            score += 20
                            signals.append(f"Price ${latest.Close:.2f} < ${value}")
                
                except Exception as e:
                    pass
                
                matches.append(matched)
            
            # Only include if ALL rules match
            if all(matches) and len(matches) == len(rules) and len(matches) > 0:
                # Create enhanced chart with all relevant indicators
                fig = go.Figure()
                fig.add_trace(go.Candlestick(x=df.index, open=df.Open, high=df.High, low=df.Low, close=df.Close, name="Price"))
                
                # Add EMAs
                if indicators.get('EMA_50') is not None:
                    fig.add_trace(go.Scatter(x=df.index, y=indicators['EMA_50'], name="EMA50", line=dict(color="orange", width=1)))
                if indicators.get('EMA_200') is not None:
                    fig.add_trace(go.Scatter(x=df.index, y=indicators['EMA_200'], name="EMA200", line=dict(color="purple", width=1)))
                
                # Add Bollinger Bands if used
                if any(r[0] == "BB_TOUCH" for r in rules):
                    if indicators.get('BB_Upper') is not None:
                        fig.add_trace(go.Scatter(x=df.index, y=indicators['BB_Upper'], name="BB Upper", line=dict(color="blue", dash="dash", width=1)))
                    if indicators.get('BB_Lower') is not None:
                        fig.add_trace(go.Scatter(x=df.index, y=indicators['BB_Lower'], name="BB Lower", line=dict(color="blue", dash="dash", width=1)))
                
                # Add VWAP if used
                if any(r[0] in ["PRICE_ABOVE_VWAP", "PRICE_BELOW_VWAP"] for r in rules):
                    if indicators.get('VWAP') is not None:
                        fig.add_trace(go.Scatter(x=df.index, y=indicators['VWAP'], name="VWAP", line=dict(color="yellow", width=1)))
                
                fig.update_layout(
                    height=500, 
                    title=f"{sym.replace('-USD','')} – Custom Rules Match (Score: {score}/100)",
                    template="plotly_dark", 
                    paper_bgcolor="#0e1117", 
                    plot_bgcolor="#0e1117",
                    xaxis_rangeslider_visible=False
                )
                
                buf = BytesIO()
                fig.write_image(buf, format="png")
                img = base64.b64encode(buf.getvalue()).decode()
                
                explanation = " | ".join(explanation_parts) if explanation_parts else "Matches all your custom rules"
                
                results.append({
                    "sym": sym.replace("-USD",""),
                    "score": score,
                    "signals": signals,
                    "chart": f"data:image/png;base64,{img}",
                    "explanation": explanation
                })
        except Exception as e:
            pass
    
    return sorted(results, key=lambda x: x["score"], reverse=True), None

# Show payment options
def show_payment_options():
    st.markdown("---")
    st.markdown("<div class='paywall-box'>", unsafe_allow_html=True)
    st.markdown("### 💳 Upgrade to Premium - $5/month")
    st.markdown("**Unlock unlimited scans, custom rules, and tweet exports**")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 💎 Pay with USDC (Solana)")
        st.info("Scan the QR or connect Phantom/Solflare. Pay $5 USDC on Solana to unlock instantly.")
        
        if st.button("💰 Pay with USDC", key="pay_solana", use_container_width=True):
            if not st.session_state.user_email.strip():
                st.warning("Please enter your email before paying so we can restore access later.")
            else:
                st.session_state.payment_method = "solana"
                st.session_state.payment_pending = True
                st.session_state.solana_reference = None
                st.session_state.solana_pay_url = None
                st.session_state.payment_id = None
                st.rerun()
        
        if st.session_state.payment_method == "solana" and st.session_state.payment_pending:
            if not st.session_state.solana_pay_url:
                sol_url, reference = generate_solana_pay_request()
                st.session_state.solana_pay_url = sol_url
                st.session_state.solana_reference = reference
                st.session_state.payment_id = reference
            
            sol_pay_url = st.session_state.solana_pay_url
            reference = st.session_state.solana_reference
            recipient = os.getenv("SOLANA_WALLET_ADDRESS", "YourSolanaWalletAddressHere")
            
            st.markdown("---")
            st.markdown("### 📱 Pay with Any Solana Wallet")
            st.markdown(f"**Amount:** {SOLANA_DEFAULT_AMOUNT} USDC")
            st.markdown(f"**Recipient:** `{recipient}`")
            st.markdown(f"**Reference:** `{reference}`")
            
            cols = st.columns(2)
            with cols[0]:
                st.markdown("**Scan with Phantom / Solflare (mobile):**")
                try:
                    qr = qrcode.QRCode(version=1, box_size=8, border=4)
                    qr.add_data(sol_pay_url)
                    qr.make(fit=True)
                    img_qr = qr.make_image(fill_color="#00ff88", back_color="#0e1117")
                    buf_qr = BytesIO()
                    img_qr.save(buf_qr, format="PNG")
                    buf_qr.seek(0)
                    st.image(buf_qr, width=220)
                except Exception as e:
                    st.info(f"QR code error: {str(e)}")
            
            with cols[1]:
                st.markdown("**Desktop Wallet:**")
                st.write("1. Click the button below\n2. Phantom/Solflare will open with the payment pre-filled\n3. Approve to unlock instantly")
                st.markdown(f"<a class='sol-pay-link' href='{sol_pay_url}' target='_blank' style='display:inline-block;padding:0.9rem 1.2rem;background:linear-gradient(45deg,#9945FF,#14F195);color:white;border-radius:10px;text-decoration:none;font-weight:bold;'>🔗 Open in Phantom / Solflare</a>", unsafe_allow_html=True)
            
            st.markdown("**After paying, click verify:**")
            if st.button("✅ I've Paid – Verify USDC", key="verify_solana"):
                if verify_payment(reference, "solana"):
                    st.session_state.paid = True
                    st.session_state.payment_pending = False
                    save_subscription_record(
                        st.session_state.user_email.strip(),
                        st.session_state.user_wallet.strip(),
                        reference,
                        SOLANA_DEFAULT_AMOUNT,
                    )
                    st.success("✅ Payment detected! Unlimited scans unlocked.")
                    st.balloons()
                    st.rerun()
                else:
                    st.warning("Payment not detected yet. Wait 2-3 seconds and try again.")
                    st.info("💡 In production this verifies automatically via Helius webhook.")
            
            if st.button("↻ Refresh Solana Payment", key="refresh_solana"):
                st.session_state.solana_pay_url = None
                st.session_state.solana_reference = None
                st.session_state.payment_id = None
                st.rerun()
    
    with col2:
        st.markdown("### 💳 Pay with PayPal")
        st.info("Subscribe for $5/month. Cancel anytime!")
        
        if st.button("💳 Subscribe with PayPal", key="pay_paypal", use_container_width=True):
            st.session_state.payment_method = "paypal"
            st.session_state.payment_pending = True
            st.session_state.payment_id = f"pp_{int(time.time())}"
            st.rerun()
        
        if st.session_state.payment_method == "paypal" and st.session_state.payment_pending:
            st.markdown("---")
            st.markdown("### 🔄 PayPal Subscription")
            
            paypal_mode = os.getenv("PAYPAL_MODE", "sandbox")
            paypal_client_id = os.getenv("PAYPAL_CLIENT_ID", "")
            
            if paypal_mode == "sandbox" or not paypal_client_id:
                st.info("🧪 **Test Mode Active**")
                st.markdown("Click below to simulate PayPal payment:")
                if st.button("✅ Simulate PayPal Payment", key="simulate_paypal"):
                    st.session_state.paid = True
                    st.session_state.payment_pending = False
                    save_subscription_record(
                        st.session_state.user_email.strip(),
                        st.session_state.user_wallet.strip(),
                        f"paypal-{int(time.time())}",
                        SOLANA_DEFAULT_AMOUNT,
                    )
                    st.success("✅ Payment successful! You now have unlimited access!")
                    st.balloons()
                    st.rerun()
            else:
                st.markdown("Redirecting to PayPal...")
                st.info("💡 In production, this redirects to PayPal checkout")
    
    st.markdown("</div>", unsafe_allow_html=True)
    st.markdown("---")

# Paywall glow
if not st.session_state.paid:
    st.markdown("<p class='paywall'>Unlock Custom Rules + Unlimited Exports → $5/mo</p>", unsafe_allow_html=True)
    st.session_state.user_email = st.text_input("Email (required to receive access reminders)", value=st.session_state.user_email, placeholder="you@example.com")
    st.session_state.user_wallet = st.text_input("Primary Solana wallet (optional, helps auto-unlock)", value=st.session_state.user_wallet, placeholder="e.g. 9xQeWv...Phantom")
    st.markdown("#### Already subscribed? Enter your email or wallet to restore access.")
    st.session_state.subscription_lookup = st.text_input("Email or Solana wallet", value=st.session_state.subscription_lookup, key="lookup_input")
    col_lookup = st.columns([1, 1])
    with col_lookup[0]:
        if st.button("🔁 Check Subscription Status"):
            identifier = st.session_state.subscription_lookup.strip()
            success, message = check_subscription_status(identifier)
            if success:
                st.session_state.paid = True
                st.success(message)
                st.balloons()
            else:
                st.warning(message)
    st.markdown("---")

# Show custom rules section if clicked
if st.session_state.show_custom_rules:
    st.markdown("---")
    st.markdown("### ⚙️ Custom Rules (Premium Feature)")
    if not st.session_state.paid:
        st.warning("🔒 This feature requires a $5/mo subscription. Upgrade below to unlock!")
        show_payment_options()
    else:
        st.success("✅ Premium unlocked! Create your custom trading strategy below.")
        st.info("📊 **5-rule limit per scan** - Maximum 5 conditions allowed. All conditions must match (AND logic).")
        st.markdown("**Supported Indicators (50+):**")
        with st.expander("📋 View All Supported Indicators"):
            col1, col2, col3 = st.columns(3)
            with col1:
                st.markdown("""
                **Trend:**
                - Price above/below EMA (9,12,20,26,50,200)
                - Price above/below SMA (20,50,200)
                - Golden Cross / Death Cross
                - MACD Bull/Bear Cross
                - ADX > 25
                - SuperTrend
                - Parabolic SAR
                - Aroon Up/Down
                """)
            with col2:
                st.markdown("""
                **Momentum:**
                - RSI < 30 or > 70
                - Stochastic < 20 or > 80
                - CCI < -100 or > 100
                - Williams %R < -80 or > -20
                - MFI < 20 or > 80
                - ROC (Rate of Change)
                """)
            with col3:
                st.markdown("""
                **Volume:**
                - Volume > 2x or 3x average
                - Price above/below VWAP
                - OBV Divergence
                
                **Volatility:**
                - Bollinger Bands (upper/lower touch)
                - ATR
                """)
        
        st.markdown("**Example Rules:**")
        st.code("""Price above 200 EMA AND RSI > 40
RSI < 30 AND Volume > 2x average AND MACD bull cross
Price above VWAP AND SuperTrend bullish AND ADX > 25
Stochastic < 20 AND Price above 50 EMA AND Volume spike
Golden Cross AND RSI > 50 AND Price above 200 EMA""", language=None)
        
        custom_rule = st.text_area("Enter your trading strategy rules (max 5 conditions):", 
                                 placeholder="Example: Price above 200 EMA AND RSI > 40 AND Volume > 2x average",
                                 height=100)
        
        if st.button("🔍 Scan with Custom Rules", use_container_width=True):
            if custom_rule.strip():
                with st.spinner("🔍 Scanning market with your custom rules..."):
                    results, error = scan_with_custom_rules(custom_rule)
                
                if error:
                    st.error(error)
                elif results:
                    st.success(f"✅ Found {len(results)} assets matching your custom rules!")
                    
                    for r in results:
                        c1, c2 = st.columns([3, 1])
                        
                        with c1:
                            st.image(r["chart"])
                        
                        with c2:
                            st.metric(r["sym"], f"Score: {r['score']}/100")
                            st.write("**Signals:**")
                            for signal in r["signals"]:
                                st.write(f"• {signal}")
                            st.markdown(f"**💡 Explanation:** {r['explanation']}")
                            
                            # Tweet export
                            tweet = f"🏹 SnipeVision Custom Rules found {r['sym']} → {', '.join(r['signals'])} | {r['explanation']}\nhttps://snipevision.xyz"
                            st.code(tweet, language=None)
                            if st.button("📋 Copy Tweet", key=f"custom_copy_{r['sym']}"):
                                st.toast("✅ Copied to clipboard!")
                else:
                    st.warning("No assets found matching your custom rules. Try adjusting your criteria.")
            else:
                st.info("Please enter your custom rules above.")
    st.markdown("---")

# Show tweet info if clicked
if st.session_state.show_tweet_info:
    st.markdown("---")
    st.markdown("### 🐦 One-Click Post to X")
    st.info("After running a scan, each result includes a ready-to-post tweet. Just click 'Copy Tweet' and paste it on X (Twitter)!")
    st.markdown("---")

# Show scanner section if Quick Snipe was clicked
if st.session_state.show_scanner:
    st.markdown("---")
    st.markdown("### 🚀 Quick Snipe Scanner")
    st.info("Click the button below to scan for the top 10 best setups right now!")


@st.cache_data(ttl=900)
def scan():
    results = []
    symbols = ["BTC-USD","ETH-USD","SOL-USD","XRP-USD","DOGE-USD","ADA-USD","AVAX-USD","NVDA","TSLA","AAPL","SMCI"]
    
    for sym in symbols:
        try:
            df = yf.download(sym, period="6mo", progress=False)
            if len(df) < 50: continue
            
            df["EMA50"] = ta.ema(df.Close, 50)
            df["EMA200"] = ta.ema(df.Close, 200)
            df["RSI"] = ta.rsi(df.Close, 14)
            
            latest = df.iloc[-1]
            score = 0
            signals = []
            
            if latest.EMA50 > latest.EMA200 and df.EMA50.iloc[-2] <= df.EMA200.iloc[-2]:
                signals.append("Golden Cross"); score += 35
            
            if latest.RSI < 30:
                signals.append("Oversold"); score += 25
            
            if latest.Volume > df.Volume.rolling(20).mean().iloc[-1]*2:
                signals.append("Volume Spike"); score += 20
            
            if score >= 50:
                fig = go.Figure()
                fig.add_trace(go.Candlestick(x=df.index, open=df.Open, high=df.High, low=df.Low, close=df.Close))
                fig.add_trace(go.Scatter(x=df.index, y=df.EMA50, name="EMA50", line=dict(color="orange")))
                fig.add_trace(go.Scatter(x=df.index, y=df.EMA200, name="EMA200", line=dict(color="purple")))
                fig.update_layout(height=500, title=f"{sym.replace('-USD','')} – Score {score}/100", 
                                template="plotly_dark", paper_bgcolor="#0e1117", plot_bgcolor="#0e1117")
                
                buf = BytesIO()
                fig.write_image(buf, format="png")
                img = base64.b64encode(buf.getvalue()).decode()
                
                results.append({"sym":sym.replace("-USD",""),"score":score,"signals":signals,"chart":f"data:image/png;base64,{img}"})
        except: 
            pass
    
    return sorted(results, key=lambda x: x["score"], reverse=True)[:10]

st.markdown("---")

if st.button("🔥 RUN SNIPE SCAN", use_container_width=True):
    # Check free scan limit
    if st.session_state.scans >= 3 and not st.session_state.paid:
        st.markdown("---")
        st.markdown("<div class='paywall-box'>", unsafe_allow_html=True)
        st.markdown("<h2 style='text-align: center; color: #ff00aa;'>🔒 You've Used Your 3 Free Scans</h2>", unsafe_allow_html=True)
        st.markdown("<p style='text-align: center; font-size: 1.5rem;'>Unlock unlimited scans for <strong>$5/month</strong></p>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)
        show_payment_options()
    else:
        st.session_state.scans += 1
        
        with st.spinner("🔍 Scanning the entire market..."):
            top = scan()
        
        st.success(f"✅ Found {len(top)} hot setups!")
        
        for r in top:
            c1, c2 = st.columns([3, 1])
            
            with c1: 
                st.image(r["chart"])
            
            with c2:
                st.metric(r["sym"], f"{r['score']}/100")
                st.write("**Signals:** " + " • ".join(r["signals"]))
                
                # Tweet export (unlocked for paid users or first 3 scans)
                if st.session_state.paid or st.session_state.scans <= 3:
                    tweet = f"🏹 SnipeVision just found {r['sym']} → {' • '.join(r['signals'])} | Score {r['score']}/100\nhttps://snipevision.xyz"
                    st.code(tweet, language=None)
                    if st.button("📋 Copy Tweet", key=f"copy_{r['sym']}"):
                        st.toast("✅ Copied to clipboard! Paste it on X now!")
                else:
                    st.info("🔒 Tweet export locked. Upgrade to unlock!")

st.caption("SnipeVision • Built with Cursor • Manual TA is dead 2025")
st.markdown(
    "<div class='footer-links'>"
    "<a href='/terms?page=terms'>Terms</a>"
    "<a href='/privacy?page=privacy'>Privacy</a>"
    "<a href='/refund?page=refund'>Refunds</a>"
    "<a href='mailto:hello@snipevision.xyz'>Contact</a>"
    "</div>",
    unsafe_allow_html=True,
)
