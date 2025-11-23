import streamlit as st
import yfinance as yf
import pandas as pd
import pandas_ta as ta
import plotly.graph_objects as go
from datetime import datetime, timedelta
import base64
from io import BytesIO

st.set_page_config(page_title="SnipeVision", layout="wide")
st.title("🏹 SnipeVision – Never Miss Another 10x Again")
st.markdown("**Live AI scanner for crypto & stocks** • Free: 5 scans/day • $5/mo = unlimited + tweet exports")

# Session state for free limits
if 'scans' not in st.session_state:
    st.session_state.scans = 0
if 'paid' not in st.session_state:
    st.session_state.paid = False

@st.cache_data(ttl=900)  # refresh every 15 min
def scan_market(market):
    results = []
    symbols = {
        "Crypto": ["BTC-USD","ETH-USD","SOL-USD","XRP-USD","ADA-USD","DOGE-USD","BNB-USD","AVAX-USD","LINK-USD","MATIC-USD"],
        "Stocks": ["AAPL","NVDA","TSLA","AMD","META","AMZN","GOOGL","MSFT","SMCI","COIN"]
    }[market]

    for sym in symbols:
        try:
            data = yf.download(sym, period="6mo", interval="1d", progress=False)
            if len(data) < 50: continue

            data['EMA50'] = ta.ema(data.Close, 50)
            data['EMA200'] = ta.ema(data.Close, 200)
            data['RSI'] = ta.rsi(data.Close, 14)
            data['Volume_MA'] = data.Volume.rolling(20).mean()

            latest = data.iloc[-1]
            prev = data.iloc[-2]

            score = 0
            signals = []

            if latest.EMA50 > latest.EMA200 and prev.EMA50 <= prev.EMA200:
                signals.append("Golden Cross"); score += 35
            if latest.RSI < 30:
                signals.append("Oversold RSI"); score += 25
            if latest.Volume > latest.Volume_MA * 2:
                signals.append("Volume Explosion"); score += 20
            if latest.Close > data.High.iloc[-10:-1].max():
                signals.append("Breaking Out"); score += 20

            if score >= 50:
                # Chart
                fig = go.Figure()
                fig.add_trace(go.Candlestick(x=data.index, open=data.Open, high=data.High, low=data.Low, close=data.Close, name=sym))
                fig.add_trace(go.Scatter(x=data.index, y=data.EMA50, name="EMA50", line=dict(color="#f7931a")))
                fig.add_trace(go.Scatter(x=data.index, y=data.EMA200, name="EMA200", line=dict(color="red")))
                fig.update_layout(height=500, title=f"{sym} → Score {score}/100")
                
                buf = BytesIO()
                fig.write_image(buf, format="png")
                img_base64 = base64.b64encode(buf.getvalue()).decode()

                results.append({
                    "sym": sym,
                    "score": score,
                    "signals": signals,
                    "chart": f"data:image/png;base64,{img_base64}",
                    "explanation": f"{sym} just triggered: {', '.join(signals)}. Strong momentum setting up."
                })
        except:
            continue
    return sorted(results, key=lambda x: x["score"], reverse=True)[:10]

market = st.selectbox("Choose market", ["Crypto", "Stocks"])

if st.button("🔥 RUN SNIPE SCAN (Live right now)"):
    if st.session_state.scans >= 5 and not st.session_state.paid:
        st.error("Free limit reached → $5/mo for unlimited scans!")
        st.info("DM me on X @yourhandle for access today")
    else:
        with st.spinner("Sniping the entire market..."):
            st.session_state.scans += 1
            top = scan_market(market)
        
        st.success(f"Found {len(top)} screaming setups!")
        for r in top:
            c1, c2 = st.columns([2, 1])
            with c1:
                st.image(r["chart"], use_column_width=True)
            with c2:
                st.metric(r["sym"], f"Score: {r['score']}/100")
                st.write("**Signals:** " + " • ".join(r["signals"]))
                st.write(r["explanation"])
                if st.session_state.paid or st.session_state.scans <= 3:
                    tweet = f"🏹 SnipeVision just found {r['sym']} → {', '.join(r['signals'])} | Score {r['score']}/100\nhttps://snipevision.xyz"
                    st.code(tweet, language="text")
                    if st.button("Copy Tweet", key=r["sym"]):
                        st.success("Copied! Post it and watch the raid")
                else:
                    st.info("Tweet export paywalled – upgrade below!")

# Mock upgrade button (real Stripe later)
if st.button("💳 Upgrade to $5/mo (Unlimited)"):
    st.session_state.paid = True
    st.success("Unlocked! Reload to see unlimited scans + tweets. (Real payments coming soon)")

st.markdown("---")
st.caption("SnipeVision • Launch day • Built in one afternoon because manual charting is dead")
