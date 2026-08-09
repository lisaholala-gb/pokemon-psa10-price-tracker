import os
import base64
import urllib.parse
import urllib.request
import json

print("Pokemon PSA 10 Price Tracker")

client_id = os.environ["EBAY_CLIENT_ID"]
client_secret = os.environ["EBAY_CLIENT_SECRET"]

credentials = f"{client_id}:{client_secret}"
encoded_credentials = base64.b64encode(
    credentials.encode()
).decode()

token_url = "https://api.sandbox.ebay.com/identity/v1/oauth2/token"

data = urllib.parse.urlencode({
    "grant_type": "client_credentials",
    "scope": "https://api.ebay.com/oauth/api_scope"
}).encode()

request = urllib.request.Request(
    token_url,
    data=data,
    method="POST"
)

request.add_header(
    "Authorization",
    f"Basic {encoded_credentials}"
)
request.add_header(
    "Content-Type",
    "application/x-www-form-urlencoded"
)

try:
    with urllib.request.urlopen(request) as response:
        result = json.loads(response.read().decode())

    if "access_token" in result:
        print("SUCCESS: Connected to eBay Sandbox")
        print("Access token received securely")
    else:
        print("ERROR: No access token returned")

except Exception as error:
    print("ERROR connecting to eBay:")
    print(error)
