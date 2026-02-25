#!/usr/bin/env python3
"""Debug Kalshi authentication."""

import os
import time
import base64
from Crypto.PublicKey import RSA
from Crypto.Signature import pkcs1_15
from Crypto.Hash import SHA256
import requests
from dotenv import load_dotenv

load_dotenv()

# Load credentials
api_key_id = os.getenv('KALSHI_API_KEY_ID')
private_key_str = os.getenv('KALSHI_PRIVATE_KEY')

print(f"API Key ID: {api_key_id}")
print(f"Private Key loaded: {len(private_key_str) if private_key_str else 0} bytes\n")

# Load RSA key
private_key = RSA.import_key(private_key_str)
print(f"✅ RSA key loaded successfully\n")

# Test signing
method = "GET"
path = "/trade-api/v2/markets"
body = ""

timestamp = str(int(time.time() * 1000))
message = timestamp + method + path + body

print(f"Signing message:")
print(f"  Timestamp: {timestamp}")
print(f"  Method: {method}")
print(f"  Path: {path}")
print(f"  Message: {message}\n")

# Sign
h = SHA256.new(message.encode('utf-8'))
signature = pkcs1_15.new(private_key).sign(h)
signature_b64 = base64.b64encode(signature).decode('utf-8')

print(f"Signature (base64): {signature_b64[:50]}...\n")

# Make request
url = "https://trading-api.kalshi.com/trade-api/v2/markets"
headers = {
    'KALSHI-ACCESS-KEY': api_key_id,
    'KALSHI-ACCESS-SIGNATURE': signature_b64,
    'KALSHI-ACCESS-TIMESTAMP': timestamp,
    'Content-Type': 'application/json'
}

print(f"Request headers:")
for k, v in headers.items():
    if k == 'KALSHI-ACCESS-SIGNATURE':
        print(f"  {k}: {v[:50]}...")
    else:
        print(f"  {k}: {v}")

print(f"\nMaking request to {url}...")

try:
    response = requests.get(url, headers=headers, params={'limit': 5}, timeout=10, verify=False)
    print(f"\nResponse status: {response.status_code}")
    print(f"Response headers: {dict(response.headers)}\n")

    if response.status_code == 200:
        print("✅ SUCCESS!")
        data = response.json()
        print(f"Markets returned: {len(data.get('markets', []))}")
    else:
        print(f"❌ Failed: {response.status_code}")
        print(f"Response: {response.text[:500]}")

except Exception as e:
    print(f"❌ Error: {e}")
