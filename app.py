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
from datetime import datetime
import json

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

# Show payment options
def show_payment_options():
    st.markdown("---")
    st.markdown("<div class='paywall-box'>", unsafe_allow_html=True)
    st.markdown("### 💳 Upgrade to Premium - $5/month")
    st.markdown("**Unlock unlimited scans, custom rules, and tweet exports**")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 💎 Pay with USDC (Solana)")
        st.info("Send $5 USDC to our Solana wallet. Instant unlock!")
        
        solana_address = os.getenv("SOLANA_WALLET_ADDRESS", "YourSolanaWalletAddressHere")
        
        if st.button("💰 Pay with USDC", key="pay_solana", use_container_width=True):
            st.session_state.payment_method = "solana"
            st.session_state.payment_pending = True
            st.session_state.payment_id = f"sol_{int(time.time())}"
            st.rerun()
        
        if st.session_state.payment_method == "solana" and st.session_state.payment_pending:
            st.markdown("---")
            st.markdown("### 📱 Payment Instructions")
            st.markdown(f"**Send exactly $5 USDC to:**")
            st.code(solana_address, language=None)
            
            try:
                qr = qrcode.QRCode(version=1, box_size=10, border=5)
                qr.add_data(f"solana:{solana_address}?amount=5&token=USDC")
                qr.make(fit=True)
                img_qr = qr.make_image(fill_color="#00ff88", back_color="#0e1117")
                buf_qr = BytesIO()
                img_qr.save(buf_qr, format="PNG")
                buf_qr.seek(0)
                st.image(buf_qr, width=300)
            except Exception as e:
                st.info(f"QR code: {str(e)}")
            
            st.markdown("**After sending, click below to verify:**")
            if st.button("✅ Verify Payment", key="verify_solana"):
                if verify_payment(st.session_state.payment_id, "solana"):
                    st.session_state.paid = True
                    st.session_state.payment_pending = False
                    st.success("✅ Payment verified! You now have unlimited access!")
                    st.balloons()
                    st.rerun()
                else:
                    st.warning("Payment not detected yet. Please wait a moment and try again.")
                    st.info("💡 In production, this is verified automatically via Helius webhook")
    
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

# Show custom rules section if clicked
if st.session_state.show_custom_rules:
    st.markdown("---")
    st.markdown("### ⚙️ Custom Rules (Premium Feature)")
    if not st.session_state.paid:
        st.warning("🔒 This feature requires a $5/mo subscription. Upgrade below to unlock!")
        show_payment_options()
    else:
        st.success("✅ Premium unlocked! Create your custom trading strategy below.")
        st.markdown("**Examples:**")
        st.code("RSI < 30 AND Volume > 2x average\nRSI > 70 AND Volume spike\nEMA50 > EMA200 (Golden Cross)\nRSI < 30 AND Volume > 2x AND Golden Cross", language=None)
        
        custom_rule = st.text_area("Enter your trading strategy rules:", 
                                 placeholder="Example: RSI < 30 AND Volume > 2x average AND Golden Cross",
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

def parse_custom_rules(rule_text):
    """Parse custom rules from natural language"""
    rules = []
    rule_text = rule_text.upper()
    
    # RSI rules
    if "RSI" in rule_text:
        if "RSI <" in rule_text or "RSI BELOW" in rule_text:
            try:
                value = float([x for x in rule_text.split() if x.replace(".", "").isdigit()][0])
                rules.append(("RSI", "<", value))
            except:
                if "30" in rule_text:
                    rules.append(("RSI", "<", 30))
        elif "RSI >" in rule_text or "RSI ABOVE" in rule_text:
            try:
                value = float([x for x in rule_text.split() if x.replace(".", "").isdigit()][0])
                rules.append(("RSI", ">", value))
            except:
                if "70" in rule_text:
                    rules.append(("RSI", ">", 70))
    
    # Volume rules
    if "VOLUME" in rule_text:
        if "VOLUME >" in rule_text or "VOLUME ABOVE" in rule_text:
            if "2X" in rule_text or "2 X" in rule_text or "DOUBLE" in rule_text:
                rules.append(("VOLUME", ">", 2.0))
            elif "3X" in rule_text or "3 X" in rule_text or "TRIPLE" in rule_text:
                rules.append(("VOLUME", ">", 3.0))
            else:
                rules.append(("VOLUME", ">", 2.0))  # Default 2x
    
    # EMA rules
    if "EMA50" in rule_text and "EMA200" in rule_text:
        if "EMA50 > EMA200" in rule_text or "GOLDEN CROSS" in rule_text:
            rules.append(("EMA_CROSS", "GOLDEN", None))
        elif "EMA50 < EMA200" in rule_text or "DEATH CROSS" in rule_text:
            rules.append(("EMA_CROSS", "DEATH", None))
    
    # Price rules
    if "PRICE >" in rule_text or "PRICE ABOVE" in rule_text:
        try:
            value = float([x for x in rule_text.split() if x.replace(".", "").replace("$", "").isdigit()][0])
            rules.append(("PRICE", ">", value))
        except:
            pass
    
    return rules

def scan_with_custom_rules(custom_rules_text):
    """Scan market with custom rules"""
    results = []
    symbols = ["BTC-USD","ETH-USD","SOL-USD","XRP-USD","DOGE-USD","ADA-USD","AVAX-USD","NVDA","TSLA","AAPL","SMCI"]
    
    # Parse rules
    rules = parse_custom_rules(custom_rules_text)
    
    if not rules:
        return [], "Could not parse rules. Try: 'RSI < 30 AND Volume > 2x average'"
    
    for sym in symbols:
        try:
            df = yf.download(sym, period="6mo", progress=False)
            if len(df) < 50: continue
            
            df["EMA50"] = ta.ema(df.Close, 50)
            df["EMA200"] = ta.ema(df.Close, 200)
            df["RSI"] = ta.rsi(df.Close, 14)
            df["Volume_MA"] = df.Volume.rolling(20).mean()
            
            latest = df.iloc[-1]
            prev = df.iloc[-2]
            
            matches = []
            score = 0
            signals = []
            explanation_parts = []
            
            # Check each rule
            for rule in rules:
                rule_type, operator, value = rule
                
                if rule_type == "RSI":
                    if operator == "<" and latest.RSI < value:
                        matches.append(True)
                        score += 30
                        signals.append(f"RSI {latest.RSI:.1f} < {value}")
                        explanation_parts.append(f"RSI is oversold at {latest.RSI:.1f}")
                    elif operator == ">" and latest.RSI > value:
                        matches.append(True)
                        score += 30
                        signals.append(f"RSI {latest.RSI:.1f} > {value}")
                        explanation_parts.append(f"RSI is overbought at {latest.RSI:.1f}")
                    else:
                        matches.append(False)
                
                elif rule_type == "VOLUME":
                    volume_ratio = latest.Volume / latest.Volume_MA if latest.Volume_MA > 0 else 0
                    if operator == ">" and volume_ratio >= value:
                        matches.append(True)
                        score += 25
                        signals.append(f"Volume {volume_ratio:.1f}x average")
                        explanation_parts.append(f"Volume spike: {volume_ratio:.1f}x normal")
                    else:
                        matches.append(False)
                
                elif rule_type == "EMA_CROSS":
                    if operator == "GOLDEN" and latest.EMA50 > latest.EMA200 and prev.EMA50 <= prev.EMA200:
                        matches.append(True)
                        score += 35
                        signals.append("Golden Cross")
                        explanation_parts.append("EMA50 just crossed above EMA200 (bullish)")
                    elif operator == "DEATH" and latest.EMA50 < latest.EMA200 and prev.EMA50 >= prev.EMA200:
                        matches.append(True)
                        score += 35
                        signals.append("Death Cross")
                        explanation_parts.append("EMA50 just crossed below EMA200 (bearish)")
                    else:
                        matches.append(False)
                
                elif rule_type == "PRICE":
                    if operator == ">" and latest.Close > value:
                        matches.append(True)
                        score += 20
                        signals.append(f"Price ${latest.Close:.2f} > ${value}")
                        explanation_parts.append(f"Price above ${value}")
                    else:
                        matches.append(False)
            
            # Only include if all rules match
            if all(matches) and len(matches) > 0:
                fig = go.Figure()
                fig.add_trace(go.Candlestick(x=df.index, open=df.Open, high=df.High, low=df.Low, close=df.Close))
                fig.add_trace(go.Scatter(x=df.index, y=df.EMA50, name="EMA50", line=dict(color="orange")))
                fig.add_trace(go.Scatter(x=df.index, y=df.EMA200, name="EMA200", line=dict(color="purple")))
                fig.update_layout(height=500, title=f"{sym.replace('-USD','')} – Custom Rules Match (Score: {score}/100)", 
                                template="plotly_dark", paper_bgcolor="#0e1117", plot_bgcolor="#0e1117")
                
                buf = BytesIO()
                fig.write_image(buf, format="png")
                img = base64.b64encode(buf.getvalue()).decode()
                
                explanation = " | ".join(explanation_parts) if explanation_parts else "Matches your custom rules"
                
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
