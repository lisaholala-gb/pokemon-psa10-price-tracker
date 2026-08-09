import os
import base64
import urllib.parse
import urllib.request
import json

print("Pokemon PSA 10 Price Tracker")

# ---------------------------------
# 1. Read eBay credentials
# ---------------------------------

client_id = os.environ["EBAY_CLIENT_ID"]
client_secret = os.environ["EBAY_CLIENT_SECRET"]

credentials = f"{client_id}:{client_secret}"

encoded_credentials = base64.b64encode(
    credentials.encode()
).decode()


# ---------------------------------
# 2. Get eBay Sandbox access token
# ---------------------------------

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

    access_token = result["access_token"]

    print("SUCCESS: Connected to eBay Sandbox")
    print("Access token received securely")

except Exception as error:
    print("ERROR connecting to eBay:")
    print(error)
    raise


# ---------------------------------
# 3. Search eBay Browse API
# ---------------------------------

search_term = "Pokemon PSA 10"

query = urllib.parse.quote(search_term)

search_url = (
    "https://api.sandbox.ebay.com/buy/browse/v1/item_summary/search"
    f"?q={query}&limit=10"
)

search_request = urllib.request.Request(search_url)

search_request.add_header(
    "Authorization",
    f"Bearer {access_token}"
)

search_request.add_header(
    "X-EBAY-C-MARKETPLACE-ID",
    "EBAY_GB"
)

print()
print(f"Searching eBay for: {search_term}")
print("----------------------------------")

try:

    with urllib.request.urlopen(search_request) as response:
        search_result = json.loads(response.read().decode())

    items = search_result.get("itemSummaries", [])

    print(f"Listings found: {len(items)}")
    print()

    if not items:
        print("No listings found in eBay Sandbox.")
        print("This can be normal because Sandbox inventory is limited.")

    for number, item in enumerate(items, start=1):

        title = item.get("title", "No title")

        price_data = item.get("price", {})
        price = price_data.get("value", "N/A")
        currency = price_data.get("currency", "")

        item_url = item.get("itemWebUrl", "No URL")

        print(f"{number}. {title}")
        print(f"   Price: {price} {currency}")
        print(f"   URL: {item_url}")
        print()

except Exception as error:

    print("ERROR searching eBay:")
    print(error)
    raise
