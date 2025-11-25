# SnipeVision Testing Guide

## Quick Start Testing

### 1. Local Testing

```bash
# Install dependencies
pip install -r requirements.txt

# Run the app locally
streamlit run app.py
```

The app will open at `http://localhost:8501`

---

## Testing Scenarios

### Test 1: Free Scan Limit (3 scans)

1. **Open the app** (fresh session)
2. **Check the counter**: Should show "Free Scans Remaining: 3/3"
3. **Click "🔥 RUN SNIPE SCAN"** 3 times
   - First scan: ✅ Should work, counter shows "2/3"
   - Second scan: ✅ Should work, counter shows "1/3"
   - Third scan: ✅ Should work, counter shows "0/3"
4. **Click "🔥 RUN SNIPE SCAN" again** (4th time)
   - ❌ Should show paywall: "You've Used Your 3 Free Scans"
   - Should display payment options

**Expected Result**: Paywall appears after exactly 3 scans.

---

### Test 2: USDC (Solana) Payment Flow

1. **Trigger paywall** (use 3 free scans first)
2. **Click "💰 Pay with USDC"** button
3. **Verify display**:
   - ✅ Shows Solana wallet address
   - ✅ Shows QR code (green/neon style)
   - ✅ Shows "Verify Payment" button
4. **Click "✅ Verify Payment"** button
   - ⚠️ In test mode: Will show "Payment not detected yet"
   - This is expected - real verification needs Helius webhook
5. **For testing**: The button will work but show warning
   - In production, Helius webhook auto-verifies

**Expected Result**: Payment UI appears, QR code generates, verification button works.

---

### Test 3: Lemon Squeezy Checkout

1. **Trigger the paywall** (use 3 free scans first).
2. **Enter your email** (required so we can match the order).
3. **Click "🍋 Launch Lemon Squeezy Checkout"** (opens in a new tab).
4. **Complete the checkout** (test mode uses the Lemon sandbox checkout if your account is in test mode).
5. **Copy the order ID** from the success page or receipt email.
6. **Back in the app**, paste the order ID into the verification field and click **"✅ Verify Lemon order"**.

**Expected Result**: If the order is paid and matches your email, premium mode unlocks and balloons appear.

---

### Test 4: Premium Features After Payment

After unlocking (via Solana verification or Lemon Squeezy order):

1. **Unlimited Scans**:
   - Click "🔥 RUN SNIPE SCAN" multiple times
   - ✅ Should work unlimited (no paywall)
   - ✅ Counter should disappear or show "Premium"

2. **Custom Rules**:
   - Click "⚙️ Custom Rules" feature box
   - ✅ Should show text area (not paywalled)
   - ✅ Can enter custom rules

3. **Tweet Exports**:
   - Run a scan
   - ✅ Each result should show "📋 Copy Tweet" button
   - ✅ Tweet code should be visible

**Expected Result**: All premium features unlocked and working.

---

### Test 5: Session Persistence

1. **Unlock premium** (via either method)
2. **Refresh the page** (F5)
   - ⚠️ **Note**: Streamlit session state resets on refresh
   - This is expected behavior (no database yet)
   - In production, you'd store payment status in database

**Expected Result**: Session resets (this is normal for Streamlit without database).

---

## Advanced Testing

### Test Payment Verification Logic

Edit `app.py` temporarily to test verification:

```python
# In verify_payment() function, change to:
def verify_payment(payment_id, method):
    # For testing, always return True after 2 seconds
    time.sleep(2)
    return True
```

This simulates successful payment verification.

---

### Test QR Code Generation

1. **Click "Pay with USDC"**
2. **Check QR code**:
   - ✅ Should display green QR code
   - ✅ Should be scannable with phone wallet
   - ✅ QR data: `solana:ADDRESS?amount=5&token=USDC`

**Expected Result**: QR code generates and is scannable.

---

## Testing Checklist

- [ ] Free scan counter works (3/3 → 0/3)
- [ ] Paywall appears after 3 scans
- [ ] USDC payment UI displays correctly
- [ ] QR code generates and displays
- [ ] Lemon Squeezy order verification works
- [ ] Premium features unlock after payment
- [ ] Unlimited scans work after payment
- [ ] Custom rules accessible after payment
- [ ] Tweet exports work after payment
- [ ] Charts display correctly
- [ ] Scan results show properly

---

## Common Issues & Fixes

### Issue: QR code not showing
**Fix**: Make sure `qrcode[pil]` is installed:
```bash
pip install qrcode[pil]
```

### Issue: Payment not unlocking
**Fix**: Check that `st.session_state.paid = True` is being set. Add debug:
```python
st.write(f"Paid status: {st.session_state.paid}")
```

### Issue: Session resets on refresh
**Fix**: This is normal. In production, use a database to persist payment status.

### Issue: Webhook not working
**Fix**: Webhooks need to be deployed separately. For testing, use manual verification buttons.

---

## Production Testing

When ready for production:

1. **Set environment variables** in Render:
   - Real Solana wallet address + Helius API key
   - Live Lemon Squeezy checkout URL, API key, and variant ID

2. **(Optional) Deploy webhook service**:
   - Deploy `webhook.py` as separate Render service
   - Add webhook URL to Helius dashboard if you want push-based verification

3. **Test with real payments**:
   - Use small test amounts first
   - Verify webhook receives events
   - Check payment status updates

---

## Quick Test Script

Run this in Python to test payment logic:

```python
# test_payments.py
import streamlit as st

# Simulate session state
st.session_state.scans = 3
st.session_state.paid = False

# Test paywall trigger
if st.session_state.scans >= 3 and not st.session_state.paid:
    print("✅ Paywall should trigger")
else:
    print("❌ Paywall logic broken")

# Test unlock
st.session_state.paid = True
if st.session_state.paid:
    print("✅ Premium unlocked")
```

---

## Need Help?

- Check `app.py` for payment logic
- Check `webhook.py` for webhook endpoints
- Check Render logs for deployment issues
- Test locally first before deploying

