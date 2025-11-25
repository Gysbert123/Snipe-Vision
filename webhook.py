"""
Webhook endpoints for payment verification
Run this alongside app.py on Render.com
"""
from flask import Flask, request, jsonify
import os
import requests
from dotenv import load_dotenv
from datetime import datetime, timedelta

load_dotenv()

app = Flask(__name__)

# In-memory storage (use database in production)
payments_db = {}

# Supabase for persistent storage
try:
    from supabase import create_client
    SUPABASE_URL = os.getenv("SUPABASE_URL")
    SUPABASE_SERVICE_ROLE = os.getenv("SUPABASE_SERVICE_ROLE")
    supabase = None
    if SUPABASE_URL and SUPABASE_SERVICE_ROLE:
        supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE)
except ImportError:
    supabase = None

@app.route('/webhook/solana', methods=['POST'])
def solana_webhook():
    """Helius webhook for Solana payments"""
    try:
        data = request.json
        
        # Verify webhook signature (add in production)
        # Verify transaction on Solana
        signature = data.get('signature')
        amount = data.get('amount', 0)
        
        if amount >= 5.0:  # $5 USDC
            payment_id = data.get('payment_id', f"sol_{signature[:8]}")
            payments_db[payment_id] = {
                'status': 'verified',
                'method': 'solana',
                'amount': amount,
                'timestamp': data.get('timestamp')
            }
            return jsonify({'status': 'success', 'payment_id': payment_id}), 200
        
        return jsonify({'status': 'insufficient_amount'}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/webhook/paypal', methods=['POST'])
def paypal_webhook():
    """PayPal webhook for subscription payments"""
    try:
        data = request.json
        event_type = data.get('event_type', '')
        
        # Handle PayPal webhook events
        if event_type == 'BILLING.SUBSCRIPTION.CREATED':
            subscription_id = data.get('resource', {}).get('id', '')
            payments_db[subscription_id] = {
                'status': 'active',
                'method': 'paypal',
                'timestamp': data.get('create_time')
            }
            return jsonify({'status': 'success'}), 200
        
        return jsonify({'status': 'ignored'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/webhook/lemon', methods=['POST'])
def lemon_webhook():
    """Lemon Squeezy webhook for order payments"""
    try:
        # Lemon Squeezy sends webhook signature in header for verification
        # For now, we'll accept all webhooks (add signature verification in production)
        data = request.json
        
        # Lemon Squeezy webhook format
        event_name = data.get('meta', {}).get('event_name', '')
        order_data = data.get('data', {})
        attributes = order_data.get('attributes', {})
        
        # Handle order_created or order_paid events
        if event_name in ['order_created', 'order_paid', 'subscription_created', 'subscription_payment_success']:
            order_id = order_data.get('id', '')
            order_number = str(attributes.get('order_number', ''))
            status = (attributes.get('status') or '').lower()
            user_email = (attributes.get('user_email') or attributes.get('customer_email') or '').lower()
            total = attributes.get('total', 0)
            variant_id = str(attributes.get('variant_id', ''))
            
            # Only process paid/completed orders
            if status in ['paid', 'completed']:
                payment_ref = f"lemon-{order_number or order_id}"
                amount = float(total) / 100.0 if total else 0
                
                # Store in memory
                payments_db[payment_ref] = {
                    'status': 'verified',
                    'method': 'lemon',
                    'order_id': order_id,
                    'order_number': order_number,
                    'email': user_email,
                    'amount': amount,
                    'variant_id': variant_id,
                    'timestamp': attributes.get('created_at', '')
                }
                
                # Also store in Supabase for persistence
                if supabase and user_email:
                    try:
                        payload = {
                            "email": user_email,
                            "wallet": "",
                            "reference": payment_ref,
                            "amount": amount,
                            "status": "active",
                            "paid_at": datetime.utcnow().isoformat(),
                            "expires_at": (datetime.utcnow() + timedelta(days=30)).isoformat(),
                        }
                        supabase.table("subscriptions").upsert(payload, on_conflict="reference").execute()
                    except Exception as e:
                        print(f"Supabase save error: {e}")
                
                # Also store by email for lookup
                if user_email:
                    payments_db[f"lemon-email-{user_email}"] = payment_ref
                
                return jsonify({'status': 'success', 'order_number': order_number, 'email': user_email}), 200
        
        return jsonify({'status': 'ignored', 'event': event_name}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/payment/status/<payment_id>', methods=['GET'])
def payment_status(payment_id):
    """Check payment status"""
    payment = payments_db.get(payment_id)
    if payment:
        return jsonify(payment), 200
    return jsonify({'status': 'not_found'}), 404

@app.route('/payment/check-email/<email>', methods=['GET'])
def check_email_payment(email):
    """Check if email has a verified payment via webhook"""
    email_lower = email.lower()
    
    # Check in-memory first
    payment_ref = payments_db.get(f"lemon-email-{email_lower}")
    if payment_ref:
        payment = payments_db.get(payment_ref)
        if payment:
            return jsonify({'verified': True, 'payment': payment}), 200
    
    # Check Supabase
    if supabase:
        try:
            result = supabase.table("subscriptions").select("*").eq("email", email_lower).like("reference", "lemon-%").order("paid_at", desc=True).limit(1).execute()
            if result.data and len(result.data) > 0:
                payment = result.data[0]
                expires_at = payment.get("expires_at")
                if expires_at:
                    try:
                        exp_date = datetime.fromisoformat(expires_at.replace('Z', '+00:00'))
                        if exp_date > datetime.utcnow():
                            return jsonify({'verified': True, 'payment': payment}), 200
                    except:
                        pass
                return jsonify({'verified': True, 'payment': payment, 'expired': True}), 200
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    return jsonify({'verified': False}), 200

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)

