"""
Webhook endpoints for payment verification
Run this alongside app.py on Render.com
"""
from flask import Flask, request, jsonify
import os
import requests
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

# In-memory storage (use database in production)
payments_db = {}

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

@app.route('/payment/status/<payment_id>', methods=['GET'])
def payment_status(payment_id):
    """Check payment status"""
    payment = payments_db.get(payment_id)
    if payment:
        return jsonify(payment), 200
    return jsonify({'status': 'not_found'}), 404

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)

