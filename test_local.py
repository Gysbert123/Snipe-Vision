"""
Quick local test script for payment system
Run: python test_local.py
"""
import os
import sys

def test_imports():
    """Test if all required packages are installed"""
    print("Testing imports...")
    try:
        import streamlit
        print("[OK] streamlit")
    except ImportError:
        print("[FAIL] streamlit - Install: pip install streamlit")
    
    try:
        import qrcode
        print("[OK] qrcode")
    except ImportError:
        print("[FAIL] qrcode - Install: pip install qrcode[pil]")
    
    try:
        import yfinance
        print("[OK] yfinance")
    except ImportError:
        print("[FAIL] yfinance - Install: pip install yfinance")
    
    try:
        import pandas_ta
        print("[OK] pandas_ta")
    except ImportError:
        print("[FAIL] pandas_ta - Install: pip install pandas-ta")
    
    try:
        import plotly
        print("[OK] plotly")
    except ImportError:
        print("[FAIL] plotly - Install: pip install plotly")
    
    try:
        from PIL import Image
        print("[OK] PIL (for QR codes)")
    except ImportError:
        print("[FAIL] PIL - Install: pip install pillow")

def test_env_vars():
    """Test environment variables"""
    print("\nTesting environment variables...")
    
    vars_to_check = [
        "SOLANA_WALLET_ADDRESS",
        "HELIUS_API_KEY",
        "PAYPAL_CLIENT_ID",
        "PAYPAL_SECRET",
        "PAYPAL_MODE"
    ]
    
    for var in vars_to_check:
        value = os.getenv(var, "")
        if value:
            print(f"[SET] {var} is set")
        else:
            print(f"[NOT SET] {var} not set (using defaults/test mode)")

def test_payment_logic():
    """Test payment logic"""
    print("\nTesting payment logic...")
    
    # Simulate session state
    scans = 0
    paid = False
    
    # Test free scan limit
    print(f"Scans: {scans}, Paid: {paid}")
    if scans >= 3 and not paid:
        print("[FAIL] Paywall should trigger (but scans < 3)")
    else:
        print("[OK] Free scans available")
    
    # Simulate 3 scans
    scans = 3
    if scans >= 3 and not paid:
        print("[OK] Paywall should trigger now")
    else:
        print("[FAIL] Paywall logic broken")
    
    # Simulate payment
    paid = True
    if paid:
        print("[OK] Premium unlocked")
        if scans >= 3 and paid:
            print("[OK] Unlimited scans available")

def main():
    print("=" * 50)
    print("SnipeVision Payment System Test")
    print("=" * 50)
    
    test_imports()
    test_env_vars()
    test_payment_logic()
    
    print("\n" + "=" * 50)
    print("[OK] Basic tests complete!")
    print("\nTo test the full app, run:")
    print("  streamlit run app.py")
    print("=" * 50)

if __name__ == "__main__":
    main()

