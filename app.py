import streamlit as st

import yfinance as yf

import pandas as pd

import pandas_ta as ta

import plotly.graph_objects as go

import base64

from io import BytesIO



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

# === BEAUTIFUL LANDING PAGE (put right after st.set_page_config) ===

# Custom CSS — dark, sexy, crypto-native
st.markdown("""
<style>
    .big-title {font-size: 4.5rem !important; font-weight: 900; background: linear-gradient(90deg, #00ff88, #00d0ff); -webkit-background-clip: text; -webkit-text-fill-color: transparent;}
    .subtitle {font-size: 1.8rem; color: #00ff88; margin-bottom: 2rem;}
    .feature-box {background: rgba(0, 255, 136, 0.1); border-left: 5px solid #00ff88; padding: 1.5rem; border-radius: 10px; margin: 1rem 0;}
    .stButton>button {background: linear-gradient(45deg, #00ff88, #00d0ff); color: black; font-weight: bold; border-radius: 12px; height: auto; min-height: 3.5rem; width: 100%; font-size: 1rem; padding: 1rem; white-space: pre-line; transition: all 0.3s ease;}
    .stButton>button:hover {transform: scale(1.02); box-shadow: 0 0 20px rgba(0, 255, 136, 0.5);}
    .paywall {background: linear-gradient(45deg, #ff00aa, #ffaa00); -webkit-background-clip: text; -webkit-text-fill-color: transparent; font-size: 2rem; font-weight: 900;}
    .chart-container {border: 2px solid #00ff88; border-radius: 15px; padding: 10px; background: #111;}
</style>
""", unsafe_allow_html=True)

# Hero Section
col1, col2 = st.columns([2, 1])

with col1:
    st.markdown("<h1 class='big-title'>SNIPERVISION</h1>", unsafe_allow_html=True)
    st.markdown("<p class='subtitle'>Never stare at charts like a peasant again</p>", unsafe_allow_html=True)
    
with col2:
    # Removed broken image - add your logo here later if needed
    st.markdown("<div style='height: 200px;'></div>", unsafe_allow_html=True)

st.markdown("---")

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


# Paywall glow
if not st.session_state.paid:
    st.markdown("<p class='paywall'>Unlock Custom Rules + Unlimited Exports → $5/mo</p>", unsafe_allow_html=True)

# Show custom rules section if clicked
if st.session_state.show_custom_rules:
    st.markdown("---")
    st.markdown("### ⚙️ Custom Rules (Premium Feature)")
    if not st.session_state.paid:
        st.warning("🔒 This feature requires a $5/mo subscription. Upgrade below to unlock!")
        if st.button("💳 Upgrade to Premium ($5/mo)"):
            st.session_state.paid = True
            st.success("Unlocked! You can now use custom rules.")
            st.rerun()
    else:
        custom_rule = st.text_area("Enter your trading strategy rules:", placeholder="Example: RSI < 30 AND Volume > 2x average AND Price above EMA50")
        if st.button("🔍 Scan with Custom Rules"):
            st.info("Custom rules scanning coming soon! For now, use Quick Snipe above.")
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

                fig.update_layout(height=500, title=f"{sym.replace('-USD','')} – Score {score}/100")

                buf = BytesIO(); fig.write_image(buf, format="png")

                img = base64.b64encode(buf.getvalue()).decode()

                results.append({"sym":sym.replace("-USD",""),"score":score,"signals":signals,"chart":f"data:image/png;base64,{img}"})

        except: pass

    return sorted(results, key=lambda x: x["score"], reverse=True)[:10]



st.markdown("---")

if st.button("🔥 RUN SNIPE SCAN", use_container_width=True):

    if st.session_state.scans >= 5 and not st.session_state.paid:

        st.error("Free limit hit – $5/mo for unlimited")

        if st.button("Unlock Unlimited ($5)"):

            st.session_state.paid = True; st.success("Unlocked!")

    else:

        st.session_state.scans += 1

        with st.spinner("Scanning..."):

            top = scan()

        st.success(f"Found {len(top)} hot setups!")

        for r in top:

            c1,c2 = st.columns([3,1])

            with c1: st.image(r["chart"])

            with c2:

                st.metric(r["sym"], f"{r['score']}/100")

                st.write(" • ".join(r["signals"]))

                tweet = f"SnipeVision just found {r['sym']} → {' • '.join(r['signals'])} | Score {r['score']}/100\nhttps://snipevision.xyz"

                st.code(tweet)

                if st.button("Copy Tweet", key=r["sym"]): st.toast("Copied!")



st.caption("SnipeVision • Built with Cursor • Manual TA is dead 2025")


