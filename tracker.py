import os
import base64
import urllib.parse
import urllib.request
import urllib.error
import json
import csv
from datetime import datetime, timezone


print("Pokemon PSA 10 Price Tracker - eBay UK Production")


# ============================================================
# 1. READ PRODUCTION CREDENTIALS FROM GITHUB SECRETS
# ============================================================

client_id = os.environ["EBAY_CLIENT_ID"]
client_secret = os.environ["EBAY_CLIENT_SECRET"]

credentials = f"{client_id}:{client_secret}"

encoded_credentials = base64.b64encode(
    credentials.encode()
).decode()


# ============================================================
# 2. GET EBAY PRODUCTION ACCESS TOKEN
# ============================================================

token_url = "https://api.ebay.com/identity/v1/oauth2/token"

token_data = urllib.parse.urlencode({
    "grant_type": "client_credentials",
    "scope": "https://api.ebay.com/oauth/api_scope"
}).encode()


token_request = urllib.request.Request(
    token_url,
    data=token_data,
    method="POST"
)

token_request.add_header(
    "Authorization",
    f"Basic {encoded_credentials}"
)

token_request.add_header(
    "Content-Type",
    "application/x-www-form-urlencoded"
)


try:

    with urllib.request.urlopen(token_request) as response:
        token_result = json.loads(
            response.read().decode()
        )

    access_token = token_result["access_token"]

    print("SUCCESS: Connected to eBay Production")
    print("Production access token received securely")


except urllib.error.HTTPError as error:

    print("ERROR getting Production access token")
    print("HTTP status:", error.code)
    print(error.read().decode())
    raise


except Exception as error:

    print("ERROR connecting to eBay Production:")
    print(error)
    raise


# ============================================================
# 3. SEARCH REAL EBAY UK LISTINGS
# ============================================================

search_term = "Pokemon PSA 10"

query = urllib.parse.quote(search_term)

search_url = (
    "https://api.ebay.com/buy/browse/v1/item_summary/search"
    f"?q={query}&limit=20"
)


search_request = urllib.request.Request(
    search_url,
    method="GET"
)

search_request.add_header(
    "Authorization",
    f"Bearer {access_token}"
)

search_request.add_header(
    "X-EBAY-C-MARKETPLACE-ID",
    "EBAY_GB"
)


print()
print(f"Searching eBay UK for: {search_term}")
print("----------------------------------------")


# ============================================================
# 4. READ REAL LISTINGS
# ============================================================

try:

    with urllib.request.urlopen(search_request) as response:
        search_result = json.loads(
            response.read().decode()
        )

    items = search_result.get(
        "itemSummaries",
        []
    )

    print(f"Listings found: {len(items)}")
    print()


except urllib.error.HTTPError as error:

    print("ERROR searching eBay Production Browse API")
    print("HTTP status:", error.code)
    print(error.read().decode())
    raise


except Exception as error:

    print("ERROR searching eBay Production:")
    print(error)
    raise


# ============================================================
# 5. PREPARE PRICE HISTORY CSV
# ============================================================

csv_file = "prices.csv"

file_exists = os.path.isfile(csv_file)

today = datetime.now(timezone.utc).strftime("%Y-%m-%d")


with open(
    csv_file,
    "a",
    newline="",
    encoding="utf-8"
) as file:

    writer = csv.writer(file)

    # Create column names only when the CSV is first created
    if not file_exists:

        writer.writerow([
            "date",
            "item_id",
            "title",
            "price",
            "currency",
            "condition",
            "url"
        ])


    # ========================================================
    # 6. SAVE EACH LISTING
    # ========================================================

    for number, item in enumerate(items, start=1):

        item_id = item.get(
            "itemId",
            ""
        )

        title = item.get(
            "title",
            "No title"
        )

        price_data = item.get(
            "price",
            {}
        )

        price = price_data.get(
            "value",
            ""
        )

        currency = price_data.get(
            "currency",
            ""
        )

        condition = item.get(
            "
