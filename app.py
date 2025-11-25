import streamlit as st
import yfinance as yf
import pandas as pd
import pandas_ta as ta
import plotly.graph_objects as go
from io import BytesIO
import base64
import html
import os
import qrcode
import time
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

try:
    import stripe
    STRIPE_AVAILABLE = True
except ImportError:
    STRIPE_AVAILABLE = False
    stripe = None

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

if 'solana_reference' not in st.session_state:
    st.session_state.solana_reference = None

if 'solana_pay_url' not in st.session_state:
    st.session_state.solana_pay_url = None

if 'solana_signature' not in st.session_state:
    st.session_state.solana_signature = ""

if 'user_email' not in st.session_state:
    st.session_state.user_email = ""

if 'user_wallet' not in st.session_state:
    st.session_state.user_wallet = ""

if 'subscription_lookup' not in st.session_state:
    st.session_state.subscription_lookup = ""

if 'free_scans' not in st.session_state:
    st.session_state.free_scans = 0


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

logo_svg = """
<svg width="320" height="320" viewBox="0 0 320 320" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <radialGradient id="pulseFill" cx="50%" cy="50%" r="70%">
      <stop offset="0%" stop-color="#1dffb0" stop-opacity="0.95"/>
      <stop offset="45%" stop-color="#06cfff" stop-opacity="0.65"/>
      <stop offset="100%" stop-color="#090015" stop-opacity="0"/>
    </radialGradient>
    <linearGradient id="arcStroke" x1="0%" y1="0%" x2="100%" y2="0%">
      <stop offset="0%" stop-color="#00ff88"/>
      <stop offset="50%" stop-color="#19d9ff"/>
      <stop offset="100%" stop-color="#b44bff"/>
    </linearGradient>
  </defs>
  <circle cx="160" cy="160" r="140" fill="url(#pulseFill)" stroke="url(#arcStroke)" stroke-width="4"/>
  <path d="M60 200 C90 120, 140 110, 160 150" stroke="#19d9ff" stroke-width="5" fill="none" stroke-linecap="round"/>
  <path d="M260 200 C230 120, 180 110, 160 150" stroke="#ff4081" stroke-width="5" fill="none" stroke-linecap="round"/>
  <path d="M90 190 L130 170 L150 210 L210 150 L250 160" stroke="url(#arcStroke)" stroke-width="6" fill="none" stroke-linecap="round"/>
  <path d="M125 120 L200 120" stroke="#00ff88" stroke-width="5" stroke-linecap="round"/>
  <path d="M200 120 L190 105" stroke="#00ff88" stroke-width="5" stroke-linecap="round"/>
  <path d="M200 120 L190 135" stroke="#00ff88" stroke-width="5" stroke-linecap="round"/>
  <circle cx="160" cy="160" r="30" stroke="#ffffff" stroke-opacity="0.8" stroke-width="2" fill="none"/>
  <circle cx="160" cy="160" r="4" fill="#ffffff"/>
</svg>
"""
NEON_LOGO = "data:image/svg+xml;base64," + base64.b64encode(logo_svg.encode("utf-8")).decode("utf-8")


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

SnipeVision LLC (“SnipeVision”, “we”, “us”) provides the SnipeVision scanner platform. By using the service you agree to the terms below.

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


def render_pricing_page():
    content = """
# Pricing – SnipeVision

Last updated: 24 November 2025

<div class='static-card'>
<h3>Free Tier</h3>
<ul>
<li>3 Quick Snipe scans (tracked per email)</li>
<li>Preview tweet exports</li>
<li>No credit card required</li>
</ul>
</div>

<div class='static-card'>
<h3>Premium – $5/month</h3>
<ul>
<li>Unlimited Quick Snipe scans</li>
<li>Custom rule engine (50+ indicators)</li>
<li>Full-resolution charts + tweet exports</li>
<li>Pay with Solana USDC via connected wallet</li>
</ul>
</div>

<div class='static-card'>
<h3>What You Get with Premium</h3>
<ul>
<li>Real-time access to the SnipeVision scanner and live chart visualizations</li>
<li>Ability to save/share tweet-ready breakdowns for every signal</li>
<li>Custom strategy builder with up to 5 technical rules per scan</li>
<li>Unlimited exports for social content or trade journals</li>
</ul>
</div>

<div class='static-card'>
<h3>How Billing Works</h3>
<ul>
<li>Subscription renews every 30 days</li>
<li>Cancel anytime — access remains until renewal date</li>
<li>Questions? Email <a href="mailto:hello@snipevision.xyz">hello@snipevision.xyz</a></li>
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
        if candidate in ("terms", "privacy", "refund", "pricing"):
            target = candidate
            break
    if target == "terms":
        render_terms_page()
    elif target == "privacy":
        render_privacy_page()
    elif target == "refund":
        render_refund_page()
    elif target == "pricing":
        render_pricing_page()


handle_static_routes()

# === BEAUTIFUL LANDING PAGE ===

# Custom CSS — dark, sexy, crypto-native
st.markdown("""
<style>
:root {
    --neon-green: #00ff88;
    --neon-cyan: #19d9ff;
    --neon-purple: #b44bff;
    --charcoal: #04040d;
}

header[data-testid="stHeader"], div[data-testid="stToolbar"], .stAppDeployButton {display: none !important;}
.stApp {background-color: var(--charcoal); color: #e6f8ff; font-family: 'Space Grotesk', 'Oxanium', 'Segoe UI', sans-serif;}

.sniper-bg, .sniper-bg * {pointer-events: none;}
.sniper-bg {position: fixed; inset: 0; z-index: -4; background: radial-gradient(circle at 20% 20%, rgba(0,255,136,0.15), transparent 50%), radial-gradient(circle at 80% 10%, rgba(25,217,255,0.2), transparent 50%);}
.ambient-candles {position: absolute; inset: 0; background-image: linear-gradient(180deg, rgba(0,255,136,0.25) 10%, transparent 60%), linear-gradient(180deg, rgba(25,217,255,0.2) 10%, transparent 70%); background-size: 4px 120px, 2px 90px; animation: floatCandles 12s linear infinite;}
.ambient-candles--alt {opacity: 0.3; filter: blur(1px); animation-duration: 18s; mix-blend-mode: screen;}
.silhouette {position: absolute; width: 40vw; height: 40vw; opacity: 0.14; filter: blur(2px);}
.silhouette-bull {left: -10vw; bottom: 5vh; background: radial-gradient(circle, rgba(0,255,136,0.35), transparent 70%); clip-path: polygon(7% 63%, 20% 55%, 35% 58%, 48% 42%, 58% 37%, 68% 31%, 82% 24%, 94% 32%, 86% 48%, 90% 63%, 78% 74%, 64% 88%, 40% 90%, 22% 80%); animation: floatBull 14s ease-in-out infinite;}
.silhouette-bear {right: -8vw; top: 10vh; background: radial-gradient(circle, rgba(180,75,255,0.3), transparent 70%); clip-path: polygon(15% 20%, 28% 26%, 44% 23%, 58% 28%, 72% 33%, 82% 46%, 78% 62%, 64% 74%, 48% 70%, 36% 62%, 28% 54%, 18% 40%); animation: floatBear 18s ease-in-out infinite;}
.scanlines {position: absolute; inset: 0; background: repeating-linear-gradient(transparent 0 6px, rgba(0,0,0,0.15) 6px 12px); mix-blend-mode: screen; opacity: 0.35; animation: scanSweep 9s linear infinite;}

.hero-header {display: flex; gap: 1.5rem; align-items: center; margin-top: 1rem;}
.sniper-logo {width: 180px; max-width: 40vw; filter: drop-shadow(0 0 25px rgba(0,255,136,0.5)); animation: logoPulse 4s ease-in-out infinite;}
.hero-copy {flex: 1;}
.eyebrow {text-transform: uppercase; letter-spacing: 0.45rem; font-size: 0.85rem; color: rgba(25,217,255,0.9);}
.hyper-title {font-size: clamp(3rem, 6vw, 5.4rem); font-weight: 900; margin: 0.2rem 0; background: linear-gradient(120deg, #00ff88, #19d9ff, #b44bff); background-size: 250% auto; -webkit-background-clip: text; -webkit-text-fill-color: transparent; animation: gradientShift 6s linear infinite; text-shadow: 0 0 35px rgba(0,255,136,0.4);}
.subtitle {font-size: 1.2rem; color: #aee9ff; margin-bottom: 1.5rem;}

.hero-stats {display: grid; grid-template-columns: repeat(auto-fit, minmax(160px, 1fr)); gap: 1.1rem; margin-top: 1.5rem;}
.hero-stat {background: rgba(255,255,255,0.03); border: 1px solid rgba(0,255,136,0.3); border-radius: 18px; padding: 1rem 1.2rem; box-shadow: 0 10px 40px rgba(0,0,0,0.4);}
.hero-stat span {display: block; font-size: 0.8rem; letter-spacing: 0.2rem; color: rgba(255,255,255,0.6);}
.hero-stat strong {display: block; margin-top: 0.35rem; font-size: 1.5rem;}

.hero-hud {background: rgba(7,12,24,0.85); border: 1px solid rgba(25,217,255,0.3); border-radius: 28px; padding: 1.8rem; box-shadow: 0 20px 60px rgba(0,0,0,0.55);}
.hero-hud h3 {margin-top: 0; color: #fff;}
.hero-hud ul {padding-left: 0; list-style: none; color: #cfeaff;}
.hero-hud li {margin-bottom: 0.4rem; display: flex; align-items: center; gap: 0.4rem;}
.hero-hud li::before {content: "◆"; color: var(--neon-green); font-size: 0.8rem;}

.nav-menu {position: fixed; top: 1rem; right: 1.5rem; z-index: 10;}
.nav-menu summary {list-style: none; cursor: pointer; background: rgba(0,0,0,0.6); border: 1px solid rgba(0,255,136,0.6); color: var(--neon-green); font-size: 1.5rem; padding: 0.35rem 0.9rem; border-radius: 999px; box-shadow: 0 0 20px rgba(0,255,136,0.4);}
.nav-menu summary::-webkit-details-marker {display: none;}
.nav-menu[open] summary {background: linear-gradient(120deg, #00ff88, #19d9ff); color: #05070e;}
.nav-menu .nav-links {margin-top: 0.5rem; background: rgba(4,6,18,0.92); border: 1px solid rgba(0,255,136,0.3); border-radius: 16px; padding: 0.6rem 0; min-width: 240px; backdrop-filter: blur(10px);}
.nav-menu .nav-links a {display: block; padding: 0.5rem 1rem; color: #daf7ff; text-decoration: none; font-size: 0.95rem;}
.nav-menu .nav-links a:hover {background: rgba(0,255,136,0.12); color: var(--neon-green);}

.feature-grid {margin-top: 1.5rem;}
.feature-caption {color: rgba(255,255,255,0.7); font-size: 0.95rem; margin-top: 0.6rem;}
.stButton>button {background: linear-gradient(120deg, #00ff88, #19d9ff, #b44bff); background-size: 200% auto; border: none; border-radius: 999px; color: #03100c; font-weight: 700; text-transform: uppercase; letter-spacing: 0.08rem; min-height: 3.4rem; box-shadow: 0 15px 40px rgba(0,255,136,0.3); transition: transform 0.25s ease, box-shadow 0.25s ease; animation: buttonPulse 4s ease-in-out infinite;}
.stButton>button:hover {transform: translateY(-3px) scale(1.01); box-shadow: 0 25px 45px rgba(0,255,136,0.4);}
.stButton>button:focus {outline: none; box-shadow: 0 0 0 2px rgba(0,255,136,0.6);}

.scan-counter {font-size: 1rem; text-align: center; padding: 1rem; background: rgba(255,255,255,0.03); border: 1px solid rgba(0,255,136,0.3); border-radius: 16px; margin: 1.2rem 0; box-shadow: inset 0 0 25px rgba(0,255,136,0.08);}

.paywall {background: linear-gradient(120deg, #ff00aa, #ffaa00); -webkit-background-clip: text; -webkit-text-fill-color: transparent; font-size: 2.2rem; font-weight: 800; text-align: center; padding: 1rem 0; margin: 1rem 0;}
.neon-paywall-hint {background: rgba(255,255,255,0.02); border-left: 4px solid rgba(0,255,136,0.8); padding: 1rem 1.4rem; border-radius: 16px; margin-bottom: 1rem; box-shadow: 0 10px 30px rgba(0,0,0,0.35);}
.paywall-box {background: rgba(5,6,18,0.9); border: 1px solid rgba(255,0,170,0.35); border-radius: 28px; padding: 2.5rem; margin: 2rem 0; box-shadow: 0 25px 80px rgba(0,0,0,0.6);}
.paywall-overlay {background: radial-gradient(circle at 30% 20%, rgba(255,0,170,0.2), rgba(0,0,0,0.85)); border: 2px solid rgba(255,0,170,0.45); border-radius: 28px; padding: 2.5rem; text-align: center; box-shadow: 0 25px 80px rgba(255,0,170,0.25);}
.paywall-overlay h2 {font-size: 2.1rem; margin-bottom: 0.3rem;}
.paywall-overlay .price-tag {font-size: 3rem; font-weight: 900; color: #fff;}
.paywall-overlay .price-tag span {font-size: 1rem; text-transform: uppercase; letter-spacing: 0.35rem; display: block; color: rgba(255,255,255,0.6);}

.premium-note {font-size: 0.9rem; color: rgba(255,255,255,0.65);}

.hero-hud .pill, .paywall-overlay .pill {display: inline-flex; align-items: center; gap: 0.4rem; padding: 0.3rem 0.8rem; border-radius: 999px; font-size: 0.75rem; text-transform: uppercase; background: rgba(255,255,255,0.08); border: 1px solid rgba(255,255,255,0.2);}

.stMetric {background: rgba(255,255,255,0.03); border-radius: 18px; padding: 1rem;}
.stMetric > div {color: #fff;}

.matrix-hint {font-size: 0.85rem; letter-spacing: 0.2rem; color: rgba(255,255,255,0.5); text-transform: uppercase; text-align: center; margin-top: 1rem;}

.silky-card {background: rgba(255,255,255,0.025); border-radius: 24px; padding: 1.5rem; border: 1px solid rgba(255,255,255,0.04); box-shadow: 0 15px 40px rgba(0,0,0,0.4);}
.copy-wrapper {margin-top: 0.4rem;}
.copy-hidden {position: absolute; left: -9999px; top: -9999px; opacity: 0;}
.copy-tweet-btn {width: 100%; padding: 0.75rem 1rem; border-radius: 12px; border: 1px solid rgba(0,255,136,0.5); background: linear-gradient(120deg, rgba(0,255,136,0.25), rgba(25,217,255,0.25)); color: #e6f8ff; font-weight: 600; cursor: pointer; transition: all 0.2s ease;}
.copy-tweet-btn:hover {background: linear-gradient(120deg, rgba(0,255,136,0.45), rgba(25,217,255,0.45)); box-shadow: 0 10px 30px rgba(0,255,136,0.25);}

@keyframes logoPulse {0% {filter: drop-shadow(0 0 15px rgba(0,255,136,0.3));} 50% {filter: drop-shadow(0 0 35px rgba(25,217,255,0.6));} 100% {filter: drop-shadow(0 0 15px rgba(0,255,136,0.3));}}
@keyframes gradientShift {0% {background-position: 0% 50%;} 100% {background-position: 200% 50%;}}
@keyframes buttonPulse {0%,100% {box-shadow: 0 20px 40px rgba(0,255,136,0.35);} 50% {box-shadow: 0 30px 60px rgba(25,217,255,0.45);}}
@keyframes floatCandles {0% {background-position: 0 0, 0 0;} 100% {background-position: 0 -400px, 0 -240px;}}
@keyframes floatBull {0% {transform: translateY(0) scale(1);} 50% {transform: translateY(-20px) scale(1.05);} 100% {transform: translateY(0) scale(1);}}
@keyframes floatBear {0% {transform: translateY(0) scale(1);} 50% {transform: translateY(25px) scale(0.95);} 100% {transform: translateY(0) scale(1);}}
@keyframes scanSweep {0% {background-position: 0 0;} 100% {background-position: 0 100px;}}

@media (max-width: 768px) {
    .hero-header {flex-direction: column; text-align: center;}
    .sniper-logo {width: 150px;}
    .nav-menu {right: 0.8rem;}
    .paywall-overlay {padding: 1.5rem;}
}
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="sniper-bg">
    <div class="ambient-candles"></div>
    <div class="ambient-candles ambient-candles--alt"></div>
    <div class="silhouette silhouette-bull"></div>
    <div class="silhouette silhouette-bear"></div>
    <div class="scanlines"></div>
</div>
""", unsafe_allow_html=True)

st.markdown("""
<details class='nav-menu'>
    <summary>&#8942;</summary>
    <div class='nav-links'>
        <a href='https://snipevision.xyz/terms?page=terms'>Terms & Conditions</a>
        <a href='https://snipevision.xyz/privacy?page=privacy'>Privacy Policy</a>
        <a href='https://snipevision.xyz/refund?page=refund'>Refund Policy</a>
        <a href='https://snipevision.xyz/pricing?page=pricing'>Pricing</a>
        <a href='mailto:hello@snipevision.xyz'>Contact</a>
    </div>
</details>
""", unsafe_allow_html=True)

# Hero Section
hero_left, hero_right = st.columns([3, 2])

with hero_left:
    st.markdown(f"""
    <div class='hero-header'>
        <img src="{NEON_LOGO}" alt="SnipeVision neon logo" class="sniper-logo" />
        <div class='hero-copy'>
            <p class='eyebrow'>AUTOMATED 24/7 ALPHA RADAR</p>
            <h1 class='hyper-title'>SNIPEVISION</h1>
            <p class='subtitle'>Neon-grade liquidity optics that surface sniper-ready entries before the herd even yawns.</p>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div class='hero-stats'>
        <div class='hero-stat'>
            <span>ASSETS WATCHED</span>
            <strong>500+</strong>
        </div>
        <div class='hero-stat'>
            <span>FREE SNIPES</span>
            <strong>3 / session</strong>
        </div>
        <div class='hero-stat'>
            <span>ALGO SIGNALS</span>
            <strong>50+</strong>
        </div>
        <div class='hero-stat'>
            <span>PREMIUM</span>
            <strong>$5/mo</strong>
        </div>
    </div>
    """, unsafe_allow_html=True)

with hero_right:
    st.markdown("""
    <div class='hero-hud'>
        <div class='pill'>LIVE HUD</div>
        <h3>SnipeVision console</h3>
        <ul>
            <li>Animated candlestick radar with matrix scanlines</li>
            <li>AI breakdown: buy / sell / hedge bias on every hit</li>
            <li>Tweet-ready copy + premium charts exported instantly</li>
            <li>USDC (Solana) wallet payment unlocks in seconds</li>
        </ul>
        <p class='matrix-hint'>tap a module below and violate resistance</p>
    </div>
    """, unsafe_allow_html=True)

st.markdown("---")

# Scan counter for free users
if not st.session_state.paid:
    remaining = max(0, 3 - st.session_state.scans)
    st.markdown(f"<div class='scan-counter'>📊 Free Scans Remaining: <strong>{remaining}/3</strong></div>", unsafe_allow_html=True)

# Feature Grid
feature_cols = st.columns(3)

with feature_cols[0]:
    st.markdown("""
    <div class='silky-card'>
        <h3>🚀 Quick Snipe</h3>
        <p class='feature-caption'>Instantly sweep top crypto + AI equities for golden crosses, oversold bounces & volume nukes.</p>
    </div>
    """, unsafe_allow_html=True)
    if st.button("Pulse the radar", use_container_width=True, key="feature1"):
        st.session_state.show_scanner = True
        st.rerun()

with feature_cols[1]:
    st.markdown("""
    <div class='silky-card'>
        <h3>⚙️ Custom Rules</h3>
        <p class='feature-caption'>Chain up to five TA conditions (50+ indicators) and fire only when every clause hits.</p>
    </div>
    """, unsafe_allow_html=True)
    if st.button("Program a hunt", use_container_width=True, key="feature2"):
        st.session_state.show_custom_rules = True
        st.rerun()

with feature_cols[2]:
    st.markdown("""
    <div class='silky-card'>
        <h3>🐦 Viral Output</h3>
        <p class='feature-caption'>Auto-generate neon chart art + tweet thread bullets so you look like a $99/mo analyst.</p>
    </div>
    """, unsafe_allow_html=True)
    if st.button("Prime tweet mode", use_container_width=True, key="feature3"):
        st.session_state.show_tweet_info = True
        st.rerun()

# Tweet copy helper
def render_copy_button(tweet_text, element_id):
    """Render a client-side copy-to-clipboard button without rerunning Streamlit."""
    safe_id = re.sub(r'[^0-9a-zA-Z_-]', '', element_id) or f"copy_{secrets.token_hex(4)}"
    escaped_text = html.escape(tweet_text).replace("\n", "&#10;")
    st.markdown(
        f"""
        <div class="copy-wrapper">
            <textarea id="{safe_id}" class="copy-hidden">{escaped_text}</textarea>
            <button class="copy-tweet-btn" onclick="const el=document.getElementById('{safe_id}'); el.select(); document.execCommand('copy'); alert('Tweet copied to clipboard!');">📋 Copy Tweet</button>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _extract_usdc_received(meta, recipient_wallet):
    """Return the USDC amount (in tokens) received by recipient in this transaction."""
    def _read_balance(entries):
        if not entries:
            return 0.0
        for entry in entries:
            owner = entry.get("owner") or entry.get("accountOwner")
            if owner == recipient_wallet and entry.get("mint") == SOLANA_USDC_MINT:
                token_info = entry.get("uiTokenAmount") or {}
                ui_amount = token_info.get("uiAmount")
                if ui_amount is not None:
                    try:
                        return float(ui_amount)
                    except (TypeError, ValueError):
                        return 0.0
                raw_amount = token_info.get("amount")
                decimals = token_info.get("decimals", 0)
                if raw_amount is not None:
                    try:
                        return float(raw_amount) / (10 ** decimals)
                    except (TypeError, ValueError):
                        return 0.0
        return 0.0

    pre_amount = _read_balance(meta.get("preTokenBalances"))
    post_amount = _read_balance(meta.get("postTokenBalances"))
    delta = post_amount - pre_amount

    # Fallback to tokenBalanceChanges (Helius extension) if delta is zero
    if delta <= 0:
        for change in meta.get("tokenBalanceChanges", []) or []:
            if change.get("userAccount") == recipient_wallet and change.get("mint") == SOLANA_USDC_MINT:
                raw = change.get("rawTokenAmount") or {}
                if "tokens" in raw:
                    try:
                        return float(raw["tokens"])
                    except (TypeError, ValueError):
                        continue
                amount = raw.get("amount")
                decimals = raw.get("decimals", 0)
                if amount is not None:
                    try:
                        return float(amount) / (10 ** decimals)
                    except (TypeError, ValueError):
                        continue
    return delta


# Payment verification function
def verify_payment(identifier, method):
    """Verify payment status by checking the on-chain transaction."""
    if method != "solana":
        return False, "Unsupported payment method."

    signature = (identifier or "").strip()
    if not signature:
        return False, "Paste the Solana transaction signature from your wallet."

    helius_api = os.getenv("HELIUS_API_KEY", "")
    recipient = os.getenv("SOLANA_WALLET_ADDRESS", "YourSolanaWalletAddressHere")
    if not helius_api:
        return False, "Helius API key is missing on the server."
    if not recipient:
        return False, "Recipient wallet address is not configured."

    endpoint = f"https://mainnet.helius-rpc.com/?api-key={helius_api}"
    payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "getTransaction",
        "params": [signature, {"encoding": "jsonParsed", "maxSupportedTransactionVersion": 0}],
    }

    try:
        response = requests.post(endpoint, json=payload, timeout=15)
        response.raise_for_status()
        data = response.json()
    except requests.RequestException as exc:
        return False, f"Unable to reach Helius RPC ({exc})."
    except ValueError:
        return False, "Unexpected response from Helius RPC."

    tx = data.get("result")
    if not tx:
        return False, "Transaction not found yet. Give it 5-10 seconds and try again."

    meta = tx.get("meta") or {}
    if meta.get("err") is not None:
        return False, "Transaction failed on-chain."

    received_amount = _extract_usdc_received(meta, recipient)
    if received_amount >= SOLANA_DEFAULT_AMOUNT - 0.01:
        return True, f"Detected {received_amount:.2f} USDC sent to SnipeVision."

    return False, f"Found only {received_amount:.2f} USDC routed to the recipient. Double-check the signature."

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


def get_free_scan_count(email):
    client = get_supabase_client()
    if not client or not email:
        return 0
    try:
        result = client.table("free_usage").select("email, free_count").eq("email", email).limit(1).execute()
        data = result.data
        if not data:
            return 0
        return data[0].get("free_count", 0)
    except Exception:
        return 0


def increment_free_scan_count(email):
    client = get_supabase_client()
    if not client or not email:
        return
    try:
        current = get_free_scan_count(email)
        payload = {
            "email": email,
            "free_count": current + 1,
            "updated_at": datetime.utcnow().isoformat(),
        }
        client.table("free_usage").upsert(payload, on_conflict="email").execute()
    except Exception:
        pass


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


def create_wallet_connection_script():
    """Generate JavaScript for wallet connection"""
    return """
    <script src="https://unpkg.com/@solana/web3.js@latest/lib/index.iife.min.js"></script>
    <script>
    window.connectWallet = async function(walletType) {
        try {
            let provider = null;
            
            if (walletType === 'phantom') {
                if (window.solana && window.solana.isPhantom) {
                    provider = window.solana;
                } else {
                    alert('Phantom wallet not found! Please install Phantom extension.');
                    return null;
                }
            } else if (walletType === 'solflare') {
                if (window.solflare) {
                    provider = window.solflare;
                } else {
                    alert('Solflare wallet not found! Please install Solflare extension.');
                    return null;
                }
            }
            
            if (!provider) {
                alert('Wallet not found!');
                return null;
            }
            
            // Connect to wallet
            const response = await provider.connect();
            const address = response.publicKey.toString();
            
            // Store in Streamlit
            window.parent.postMessage({
                type: 'streamlit:setComponentValue',
                value: {connected: true, address: address, wallet: walletType}
            }, '*');
            
            return address;
        } catch (err) {
            console.error('Wallet connection error:', err);
            alert('Failed to connect wallet: ' + err.message);
            return null;
        }
    };
    
    window.sendPayment = async function(recipient, amount, tokenMint) {
        try {
            let provider = null;
            if (window.solana && window.solana.isPhantom) {
                provider = window.solana;
            } else if (window.solflare) {
                provider = window.solflare;
            }
            
            if (!provider || !provider.publicKey) {
                alert('Please connect your wallet first!');
                return false;
            }
            
            const { Connection, PublicKey, Transaction, SystemProgram, LAMPORTS_PER_SOL } = window.solanaWeb3;
            
            // For USDC (SPL token), we need to use SPL Token program
            // This is a simplified version - in production, use @solana/spl-token
            const connection = new Connection('https://api.mainnet-beta.solana.com', 'confirmed');
            const fromPubkey = provider.publicKey;
            const toPubkey = new PublicKey(recipient);
            
            // For now, send SOL as a simple transaction
            // For USDC, you'd need to use SPL Token transfer
            const transaction = new Transaction().add(
                SystemProgram.transfer({
                    fromPubkey: fromPubkey,
                    toPubkey: toPubkey,
                    lamports: amount * LAMPORTS_PER_SOL, // Convert to lamports
                })
            );
            
            const signature = await provider.sendTransaction(transaction, connection);
            await connection.confirmTransaction(signature, 'confirmed');
            
            window.parent.postMessage({
                type: 'streamlit:setComponentValue',
                value: {paymentSent: true, signature: signature}
            }, '*');
            
            return signature;
        } catch (err) {
            console.error('Payment error:', err);
            alert('Payment failed: ' + err.message);
            return null;
        }
    };
    </script>
    """


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
                rules.append(("PRICE_ABOVE_EMA", ">", ema_length))
            elif "BELOW" in part or "<" in part:
                rules.append(("PRICE_BELOW_EMA", "<", ema_length))
        
        # PRICE ABOVE/BELOW SMA
        elif ("PRICE" in part and "SMA" in part) or ("ABOVE" in part and "SMA" in part):
            sma_length = 200
            if numbers:
                for num in numbers:
                    if int(float(num)) in [20, 50, 100, 200]:
                        sma_length = int(float(num))
                        break
            if "ABOVE" in part or ">" in part:
                rules.append(("PRICE_ABOVE_SMA", ">", sma_length))
            elif "BELOW" in part or "<" in part:
                rules.append(("PRICE_BELOW_SMA", "<", sma_length))
        
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


def rule_to_label(rule):
    rule_type, operator, value = rule
    if rule_type == "PRICE_ABOVE_EMA":
        return f"Price > EMA{value}"
    if rule_type == "PRICE_BELOW_EMA":
        return f"Price < EMA{value}"
    if rule_type == "PRICE_ABOVE_SMA":
        return f"Price > SMA{value}"
    if rule_type == "PRICE_BELOW_SMA":
        return f"Price < SMA{value}"
    if rule_type == "RSI":
        return f"RSI {operator} {value}"
    if rule_type == "VOLUME":
        return f"Volume {operator} {value}x avg"
    if rule_type == "MACD_CROSS":
        return f"MACD {operator} cross"
    if rule_type == "EMA_CROSS":
        return f"{operator.title()} Cross"
    if rule_type == "BB_TOUCH":
        return f"Bollinger {operator} touch"
    if rule_type == "STOCH":
        return f"Stochastic {operator} {value}"
    if rule_type == "ADX":
        return f"ADX {operator} {value}"
    if rule_type == "ATR":
        return f"ATR {operator} {value}"
    if rule_type == "CCI":
        return f"CCI {operator} {value}"
    if rule_type == "WILLR":
        return f"Williams %R {operator} {value}"
    if rule_type == "OBV_DIVERGENCE":
        return "OBV divergence"
    if rule_type == "PRICE_ABOVE_VWAP":
        return "Price > VWAP"
    if rule_type == "PRICE_BELOW_VWAP":
        return "Price < VWAP"
    if rule_type == "SUPERTREND":
        return f"SuperTrend {operator}"
    if rule_type == "PSAR":
        return f"Parabolic SAR {operator}"
    if rule_type == "AROON_UP":
        return f"Aroon Up {operator} {value}"
    if rule_type == "AROON_DOWN":
        return f"Aroon Down {operator} {value}"
    if rule_type == "MFI":
        return f"MFI {operator} {value}"
    if rule_type == "ROC":
        return f"ROC {operator} {value}"
    if rule_type == "PRICE":
        return f"Price {operator} {value}"
    return rule_type


def classify_bias(signals):
    """Rudimentary sentiment classifier driven by signal wording."""
    if not signals:
        return "Neutral"
    bull_keywords = ["above", "bull", "golden", "oversold", "support", "spike", "breakout", "accumulation"]
    bear_keywords = ["below", "bear", "death", "overbought", "resistance", "sell", "short", "breakdown"]
    bull_hits = sum(any(keyword in signal.lower() for keyword in bull_keywords) for signal in signals)
    bear_hits = sum(any(keyword in signal.lower() for keyword in bear_keywords) for signal in signals)
    if bull_hits > bear_hits:
        return "Bullish"
    if bear_hits > bull_hits:
        return "Bearish"
    return "Neutral"


def action_from_bias(bias, score):
    """Map bias + score to a plain-English trading action."""
    if bias == "Bullish":
        return "Potential BUY setup" if score >= 60 else "Bullish but wait for confirmation"
    if bias == "Bearish":
        return "Potential SELL / hedge setup" if score >= 60 else "Bearish but patience is advised"
    return "Indecisive - stay on watch"


def build_ai_summary(symbol, timeframe, score, price, change_pct, bias, signals, action, extra_context=None):
    """Generate a human-readable narrative for the scan result."""
    key_signals = ", ".join(signals[:3]) if signals else "no major signals"
    change_str = f"{change_pct:+.2f}%" if change_pct is not None else "0.00%"
    bias_text = bias.lower() if bias != "Neutral" else "mixed"
    context = ""
    if extra_context:
        context_bits = [part for part in extra_context if part]
        if context_bits:
            context = f" Notables: {', '.join(context_bits[:2])}."
    return (
        f"{symbol} on the {timeframe} chart looks {bias_text} (score {score}/100). "
        f"Price is near ${price:,.2f} ({change_str} today) with signals such as {key_signals}. "
        f"{action}.{context}"
    ).strip()

def scan_with_custom_rules(custom_rules_text):
    """Scan market with custom rules - supports 50+ indicators, 5-rule limit"""
    results = []
    # Expanded symbol list (up to 500 for speed)
    symbols = ["BTC-USD","ETH-USD","SOL-USD","XRP-USD","DOGE-USD","ADA-USD","AVAX-USD","MATIC-USD","LINK-USD","BNB-USD",
               "DOT-USD","UNI-USD","LTC-USD","ATOM-USD","ETC-USD","ALGO-USD","FIL-USD","TRX-USD","XLM-USD","VET-USD",
               "NVDA","TSLA","AAPL","MSFT","GOOGL","AMZN","META","NFLX","AMD","SMCI","COIN","MARA","RIOT"]
    
    # Parse rules
    rules = parse_custom_rules(custom_rules_text)
    rule_labels = [rule_to_label(r) for r in rules]
    rule_tally = [0] * len(rules)
    processed = 0
    
    # Check 5-rule limit
    if len(rules) > 5:
        return [], f"Maximum 5 rules allowed. You entered {len(rules)} rules. Please reduce to 5 or fewer.", {"rule_labels": rule_labels, "rule_tally": rule_tally, "total_symbols": processed}
    
    if not rules:
        return [], "Could not parse rules. Try: 'RSI < 30 AND Volume > 2x average AND Price above 200 EMA'", {"rule_labels": [], "rule_tally": [], "total_symbols": processed}
    
    for sym in symbols[:500]:  # Limit to 500 for speed
        try:
            # Download data - use up to 2 years to ensure EMA/indicator coverage
            df = yf.download(sym, period="2y", interval="1d", progress=False, auto_adjust=False)
            if len(df) < 60:
                continue
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = df.columns.droplevel(1)
            df = df.dropna(subset=["Close", "High", "Low", "Volume"])
            
            # Calculate all indicators
            indicators = calculate_all_indicators(df)
            
            latest = df.iloc[-1]
            prev = df.iloc[-2] if len(df) > 1 else latest
            
            matches = []
            score = 0
            signals = []
            explanation_parts = []
            
            # Check each rule
            for idx, rule in enumerate(rules):
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
                if matched:
                    rule_tally[idx] += 1
            
            # Only include if ALL rules match
            if all(matches) and len(matches) == len(rules) and len(matches) > 0:
                sym_clean = sym.replace("-USD","")
                timeframe_label = "1D (Daily)"
                change_pct = float(((latest.Close - prev.Close) / prev.Close) * 100) if prev.Close != 0 else 0.0
                price_val = float(latest.Close)

                # Create enhanced chart with overlays + volume
                fig = go.Figure()
                fig.add_trace(
                    go.Candlestick(
                        x=df.index,
                        open=df.Open,
                        high=df.High,
                        low=df.Low,
                        close=df.Close,
                        name="Price",
                        increasing_line_color="#00ff88",
                        decreasing_line_color="#ff4d4d",
                    )
                )
                
                # Add EMAs
                if indicators.get('EMA_50') is not None:
                    fig.add_trace(go.Scatter(x=df.index, y=indicators['EMA_50'], name="EMA50", line=dict(color="#ffb347", width=1)))
                if indicators.get('EMA_200') is not None:
                    fig.add_trace(go.Scatter(x=df.index, y=indicators['EMA_200'], name="EMA200", line=dict(color="#9b59b6", width=1)))
                
                # Add Bollinger Bands if used
                if any(r[0] == "BB_TOUCH" for r in rules):
                    if indicators.get('BB_Upper') is not None:
                        fig.add_trace(go.Scatter(x=df.index, y=indicators['BB_Upper'], name="BB Upper", line=dict(color="#2980b9", dash="dash", width=1)))
                    if indicators.get('BB_Lower') is not None:
                        fig.add_trace(go.Scatter(x=df.index, y=indicators['BB_Lower'], name="BB Lower", line=dict(color="#2980b9", dash="dash", width=1)))
                
                # Add VWAP if used
                if any(r[0] in ["PRICE_ABOVE_VWAP", "PRICE_BELOW_VWAP"] for r in rules):
                    if indicators.get('VWAP') is not None:
                        fig.add_trace(go.Scatter(x=df.index, y=indicators['VWAP'], name="VWAP", line=dict(color="#f1c40f", width=1)))

                # Volume overlay on secondary axis
                if "Volume" in df.columns and not df["Volume"].isna().all():
                    fig.add_trace(
                        go.Bar(
                            x=df.index,
                            y=df["Volume"],
                            name="Volume",
                            marker=dict(color="rgba(0,255,136,0.25)"),
                            yaxis="y2",
                            opacity=0.35,
                        )
                    )
                
                fig.update_layout(
                    height=520,
                    title=f"{sym_clean} – Custom Rules Match (Score: {score}/100)",
                    template="plotly_dark",
                    paper_bgcolor="#0e1117",
                    plot_bgcolor="#0e1117",
                    xaxis_rangeslider_visible=False,
                    hovermode="x unified",
                    margin=dict(l=40, r=20, t=60, b=40),
                    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
                    yaxis=dict(title=dict(text="Price")),
                    yaxis2=dict(
                        title=dict(text="Volume", font=dict(color="#00ff88")),
                        overlaying="y",
                        side="right",
                        showgrid=False,
                        rangemode="tozero",
                        tickfont=dict(color="#00ff88"),
                    ),
                )
                
                figure_dict = fig.to_dict()
                explanation = " | ".join(explanation_parts) if explanation_parts else "Matches all your custom rules"
                bias = classify_bias(signals)
                action = action_from_bias(bias, score)
                narrative = build_ai_summary(
                    sym_clean,
                    timeframe_label,
                    score,
                    price_val,
                    change_pct,
                    bias,
                    signals,
                    action,
                    explanation_parts,
                )
                
                results.append({
                    "sym": sym_clean,
                    "score": score,
                    "signals": signals,
                    "figure": figure_dict,
                    "explanation": explanation,
                    "timeframe": timeframe_label,
                    "bias": bias,
                    "action": action,
                    "narrative": narrative,
                    "price": price_val,
                    "change_pct": change_pct,
                })
            processed += 1
        except Exception as e:
            pass
    
    debug_summary = {"rule_labels": rule_labels, "rule_tally": rule_tally, "total_symbols": processed}
    return sorted(results, key=lambda x: x["score"], reverse=True), None, debug_summary

# Show payment options
def show_payment_options():
    st.markdown("---")
    st.markdown("<div class='paywall-box'>", unsafe_allow_html=True)
    st.markdown("### 💳 Unlock Premium – $5/month")
    st.markdown("**Send $5 USDC on Solana to unlock unlimited scans, custom rules, and tweet exports.**")

    recipient = os.getenv("SOLANA_WALLET_ADDRESS", "YourSolanaWalletAddressHere")
    amount_usdc = SOLANA_DEFAULT_AMOUNT

    if not st.session_state.user_email.strip():
        st.warning("Enter your email above so we can tie the unlock to your account.")
        st.markdown("</div>", unsafe_allow_html=True)
        return

    if st.session_state.solana_pay_url is None or st.session_state.solana_reference is None:
        sol_url, reference = generate_solana_pay_request()
        st.session_state.solana_pay_url = sol_url
        st.session_state.solana_reference = reference

    sol_pay_url = st.session_state.solana_pay_url
    reference = st.session_state.solana_reference

    st.markdown("#### 1. Send the $5 USDC payment")
    info_cols = st.columns([1, 1])
    with info_cols[0]:
        st.write(f"**Recipient wallet:** `{recipient}`")
        st.write(f"**Memo / reference:** `{reference}`")
        st.write(f"**Amount:** {amount_usdc} USDC (SPL)")
        st.markdown("Scan the QR with Phantom/Solflare **or** paste the Solana Pay URL below into your wallet.")
    with info_cols[1]:
        try:
            qr = qrcode.QRCode(version=1, box_size=7, border=4)
            qr.add_data(sol_pay_url)
            qr.make(fit=True)
            img_qr = qr.make_image(fill_color="#00ff88", back_color="#05060c")
            buf_qr = BytesIO()
            img_qr.save(buf_qr, format="PNG")
            buf_qr.seek(0)
            st.image(buf_qr, width=220, caption="Scan with Phantom / Solflare")
        except Exception as err:
            st.info(f"QR code unavailable ({err}). Copy the URL below instead.")

    st.markdown("**Solana Pay URL:**")
    st.code(sol_pay_url, language=None)
    st.caption("Tip: Copy this URL, open Phantom/Solflare → Settings → Solana Pay → Paste URL.")

    st.markdown("#### 2. Paste the transaction signature")
    st.session_state.solana_signature = st.text_input(
        "Transaction signature",
        value=st.session_state.solana_signature,
        placeholder="5YkK3d... (found in your wallet after sending USDC)",
    )

    st.markdown("#### 3. Verify on-chain")
    verify_col, refresh_col = st.columns([2, 1])
    with verify_col:
        if st.button("✅ I've paid – verify USDC", key="verify_solana", use_container_width=True):
            ok, message = verify_payment(st.session_state.solana_signature, "solana")
            if ok:
                st.session_state.paid = True
                save_subscription_record(
                    st.session_state.user_email.strip(),
                    st.session_state.user_wallet.strip(),
                    st.session_state.solana_signature.strip(),
                    amount_usdc,
                )
                st.session_state.solana_signature = ""
                st.session_state.solana_pay_url = None
                st.session_state.solana_reference = None
                st.success("✅ Premium unlocked! Create your custom trading strategy below.")
                st.balloons()
            else:
                st.warning(message)
    with refresh_col:
        if st.button("↻ New payment QR/link", key="refresh_solana_link", use_container_width=True):
            st.session_state.solana_pay_url = None
            st.session_state.solana_reference = None
            st.rerun()

    st.markdown("</div>", unsafe_allow_html=True)
    st.markdown("---")

# Paywall glow
if not st.session_state.paid:
    st.markdown("<p class='paywall'>3 FREE LOCKS • UNLIMITED SNIPES FOR $5/MO</p>", unsafe_allow_html=True)
    st.markdown("""
    <div class='neon-paywall-hint'>
        <strong>Sync your arsenal</strong>
        <p>We tie free scans + premium access to your email so you can bounce between devices without losing progress.</p>
    </div>
    """, unsafe_allow_html=True)
    st.session_state.user_email = st.text_input("Command console email", value=st.session_state.user_email, placeholder="you@alpha.xyz")
    st.session_state.user_wallet = st.text_input("Primary Solana wallet (optional, unlock sync)", value=st.session_state.user_wallet, placeholder="e.g. 9xQeWv...Phantom")

    # Allow free scans only after email is provided
    email_identifier = st.session_state.user_email.strip()
    if email_identifier:
        success, message = check_subscription_status(email_identifier)
        if success and not st.session_state.paid:
            st.session_state.paid = True
            st.success(message)
    else:
        st.info("Enter your email above to use free scans or restore a subscription.")

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
                    results, error, debug_info = scan_with_custom_rules(custom_rule)
                    debug_info = debug_info or {}
                
                if error:
                    st.error(error)
                elif results:
                    st.success(f"✅ Found {len(results)} assets matching your custom rules!")
                    
                    for r in results:
                        c1, c2 = st.columns([3, 1])
                        
                        with c1:
                            fig_obj = r.get("figure")
                            if isinstance(fig_obj, dict):
                                fig_obj = go.Figure(fig_obj)
                            if fig_obj is not None:
                                st.plotly_chart(fig_obj, use_container_width=True)
                        
                        with c2:
                            delta_text = f"{r.get('change_pct', 0.0):+.2f}% 24h"
                            st.metric(
                                f"{r['sym']} • {r.get('timeframe', '1D (Daily)')}",
                                f"Score: {r['score']}/100",
                                delta=delta_text,
                            )
                            st.write(f"**Last Price:** ${r.get('price', 0):,.2f}")
                            st.write(f"**Bias:** {r.get('bias', 'Neutral')} • **Call:** {r.get('action', 'Monitor')}")
                            st.markdown(f"**AI read:** {r.get('narrative', 'Matches your custom rules.')}")                        
                            st.write("**Signals:**")
                            for signal in r["signals"]:
                                st.write(f"• {signal}")
                            st.markdown(f"**💡 Signal details:** {r['explanation']}")
                            
                            # Tweet export
                            tweet = f"🏹 SnipeVision Custom Rules found {r['sym']} → {', '.join(r['signals'])} | {r['explanation']}\nhttps://snipevision.xyz"
                            st.code(tweet, language=None)
                            render_copy_button(tweet, f"custom_copy_{r['sym']}")
                else:
                    st.warning("No assets found matching your custom rules. Try adjusting your criteria.")
                
                if debug_info.get("rule_labels"):
                    st.markdown("#### Rule Coverage Across Universe")
                    total = debug_info.get("total_symbols", 0)
                    coverage_cols = st.columns(2)
                    labels = debug_info.get("rule_labels", [])
                    tallies = debug_info.get("rule_tally", [])
                    for i, (label, count) in enumerate(zip(labels, tallies)):
                        col = coverage_cols[i % 2]
                        with col:
                            st.write(f"• **{label}** → {count}/{total} symbols match")
            else:
                st.info("Please enter your custom rules above.")
    st.markdown("---")

# Show tweet info if clicked
if st.session_state.show_tweet_info:
    st.markdown("---")
    st.markdown("### 🐦 One-Click Post to X")
    st.info("Use the template below for ad-hoc posts or copy the auto-generated tweets attached to every scan result.")
    tweet_col1, tweet_col2 = st.columns(2)
    with tweet_col1:
        template_symbol = st.text_input("Symbol", value="NVDA", key="tweet_template_symbol").upper()
        template_timeframe = st.selectbox("Timeframe", ["1D", "4H", "1H", "15m"], key="tweet_timeframe")
    with tweet_col2:
        template_bias = st.selectbox("Bias / Call", ["Bullish", "Bearish", "Neutral"], key="tweet_bias")
        template_flavor = st.selectbox(
            "Voice",
            ["classic alpha", "degen hype", "institutional", "newsflash"],
            key="tweet_voice",
        )

    template_map = {
        "classic alpha": "flagged early momentum",
        "degen hype": "primed for a face-melting squeeze",
        "institutional": "printing a clean structure break",
        "newsflash": "dropping a high-confidence signal",
    }
    template_line = template_map.get(template_flavor, "flagged early momentum")
    tweet_preview = (
        f"🏹 SnipeVision just {template_line} on {template_symbol} ({template_timeframe}) — "
        f"{template_bias} bias with confluence across liquidity / momentum.\n"
        f"https://snipevision.xyz"
    )
    st.code(tweet_preview, language=None)
    render_copy_button(tweet_preview, f"tweet_mode_{template_symbol}")
    st.caption("Tip: Run a scan to get symbol-specific tweets with actual signals & context.")
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
            if len(df) < 50:
                continue
            
            df["EMA50"] = ta.ema(df.Close, 50)
            df["EMA200"] = ta.ema(df.Close, 200)
            df["RSI"] = ta.rsi(df.Close, 14)
            
            latest = df.iloc[-1]
            prev = df.iloc[-2] if len(df) > 1 else latest
            score = 0
            signals = []
            
            if latest.EMA50 > latest.EMA200 and df.EMA50.iloc[-2] <= df.EMA200.iloc[-2]:
                signals.append("Golden Cross"); score += 35
            
            if latest.RSI < 30:
                signals.append("Oversold"); score += 25
            
            if latest.Volume > df.Volume.rolling(20).mean().iloc[-1]*2:
                signals.append("Volume Spike"); score += 20
            
            if score >= 50:
                sym_clean = sym.replace("-USD","")
                timeframe_label = "1D (Daily)"
                change_pct = float(((latest.Close - prev.Close) / prev.Close) * 100) if prev.Close != 0 else 0.0
                price_val = float(latest.Close)
                
                fig = go.Figure()
                fig.add_trace(
                    go.Candlestick(
                        x=df.index,
                        open=df.Open,
                        high=df.High,
                        low=df.Low,
                        close=df.Close,
                        name="Price",
                        increasing_line_color="#00ff88",
                        decreasing_line_color="#ff4d4d",
                    )
                )
                fig.add_trace(go.Scatter(x=df.index, y=df.EMA50, name="EMA50", line=dict(color="#ffb347")))
                fig.add_trace(go.Scatter(x=df.index, y=df.EMA200, name="EMA200", line=dict(color="#9b59b6")))
                
                if "Volume" in df.columns and not df["Volume"].isna().all():
                    fig.add_trace(
                        go.Bar(
                            x=df.index,
                            y=df["Volume"],
                            name="Volume",
                            marker=dict(color="rgba(0,255,136,0.25)"),
                            yaxis="y2",
                            opacity=0.35,
                        )
                    )
                
                fig.update_layout(
                    height=520,
                    title=f"{sym_clean} – Score {score}/100",
                    template="plotly_dark",
                    paper_bgcolor="#0e1117",
                    plot_bgcolor="#0e1117",
                    xaxis_rangeslider_visible=False,
                    hovermode="x unified",
                    margin=dict(l=40, r=20, t=60, b=40),
                    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
                    yaxis=dict(title=dict(text="Price")),
                    yaxis2=dict(
                        title=dict(text="Volume", font=dict(color="#00ff88")),
                        overlaying="y",
                        side="right",
                        showgrid=False,
                        rangemode="tozero",
                        tickfont=dict(color="#00ff88"),
                    ),
                )
                
                bias = classify_bias(signals)
                action = action_from_bias(bias, score)
                narrative = build_ai_summary(
                    sym_clean,
                    timeframe_label,
                    score,
                    price_val,
                    change_pct,
                    bias,
                    signals,
                    action,
                )
                
                results.append({
                    "sym": sym_clean,
                    "score": score,
                    "signals": signals,
                    "figure": fig.to_dict(),
                    "timeframe": timeframe_label,
                    "price": price_val,
                    "change_pct": change_pct,
                    "bias": bias,
                    "action": action,
                    "narrative": narrative,
                })
        except:
            pass
    
    return sorted(results, key=lambda x: x["score"], reverse=True)[:10]

st.markdown("---")

if st.button("🔥 RUN SNIPE SCAN", use_container_width=True):
    email_identifier = st.session_state.user_email.strip()
    free_count = get_free_scan_count(email_identifier) if email_identifier else st.session_state.scans
    if not st.session_state.paid and (free_count >= 3 or not email_identifier):
        st.markdown("---")
        if not email_identifier:
            st.markdown("""
            <div class='paywall-overlay'>
                <div class='pill'>identify yourself</div>
                <h2>Secure your free shots</h2>
                <p class='premium-note'>Enter an email above to sync allocations and unlock the complimentary scans across every device.</p>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown("""
            <div class='paywall-overlay'>
                <div class='pill'>snipe pass</div>
                <h2>Reload the chamber</h2>
                <div class='price-tag'>$5<span>per month</span></div>
                <p class='premium-note'>Unlimited quick snipes, custom playbooks, neon chart exports & instant Solana wallet unlock.</p>
            </div>
            """, unsafe_allow_html=True)
        show_payment_options()
    else:
        if not st.session_state.paid and email_identifier:
            increment_free_scan_count(email_identifier)
        st.session_state.scans += 1
        
        with st.spinner("🔍 Scanning the entire market..."):
            top = scan()
        
        st.success(f"✅ Found {len(top)} hot setups!")
        
        for r in top:
            c1, c2 = st.columns([3, 1])
            
            with c1: 
                fig_obj = r.get("figure")
                if isinstance(fig_obj, dict):
                    fig_obj = go.Figure(fig_obj)
                if fig_obj is not None:
                    st.plotly_chart(fig_obj, use_container_width=True)
            
            with c2:
                delta_text = f"{r.get('change_pct', 0.0):+.2f}% 24h"
                st.metric(
                    f"{r['sym']} • {r.get('timeframe', '1D (Daily)')}",
                    f"{r['score']}/100",
                    delta=delta_text,
                )
                st.write(f"**Last Price:** ${r.get('price', 0):,.2f}")
                st.write(f"**Bias:** {r.get('bias', 'Neutral')} • **Call:** {r.get('action', 'Monitor')}")
                st.markdown(f"**AI read:** {r.get('narrative', 'High-probability setup spotted.')}")                
                if r["signals"]:
                    st.write("**Signals:**")
                    for sig in r["signals"]:
                        st.write(f"• {sig}")
                else:
                    st.write("No individual signals provided.")
                
                # Tweet export (unlocked for paid users or first 3 scans)
                if st.session_state.paid or st.session_state.scans <= 3:
                    tweet = f"🏹 SnipeVision just found {r['sym']} ({r.get('timeframe','1D')}) → {' • '.join(r['signals'])} | Score {r['score']}/100\nhttps://snipevision.xyz"
                    st.code(tweet, language=None)
                    render_copy_button(tweet, f"copy_{r['sym']}")
                else:
                    st.info("🔒 Tweet export locked. Upgrade to unlock!")

st.caption("SnipeVision • Built with Cursor • Manual TA is dead 2025")
st.markdown(
    "<div class='footer-links'>"
    "<a href='https://snipevision.xyz/terms?page=terms'>Terms</a>"
    "<a href='https://snipevision.xyz/privacy?page=privacy'>Privacy</a>"
    "<a href='https://snipevision.xyz/refund?page=refund'>Refunds</a>"
    "<a href='https://snipevision.xyz/pricing?page=pricing'>Pricing</a>"
    "<a href='mailto:hello@snipevision.xyz'>Contact</a>"
    "</div>",
    unsafe_allow_html=True,
)
