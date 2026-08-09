import os
import base64
import urllib.parse
import urllib.request
import urllib.error
import json


print("Pokemon PSA 10 Price Tracker")


# ============================================================
# 1. READ EBAY CREDENTIALS FROM GITHUB SECRETS
# ============================================================

client_id = os.environ["EBAY_CLIENT_ID"]
client_secret = os.environ["EBAY_CLIENT_SECRET"]

credentials = f"{client_id}:{client_secret}"

encoded_credentials = base64.b64encode(
    credentials.encode()
).decode()


# ============================================================
# 2. GET EBAY SANDBOX ACCESS TOKEN
# ============================================================

token_url = "https://api.sandbox.ebay.com/identity/v1/oauth2/token"

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

    print("SUCCESS: Connected to eBay Sandbox")
    print("Access token received securely")


except urllib.error.HTTPError as error:

    print("ERROR getting eBay access token")
    print("HTTP status:", error.code)

    error_body = error.read().decode()

    print(error_body)

    raise


except Exception as error:

    print("ERROR connecting to eBay:")
    print(error)

    raise


# ============================================================
# 3. SEARCH EBAY BROWSE API
# ============================================================

search_term = "Pokemon PSA 10"

query = urllib.parse.quote(search_term)

search_url = (
    "https://api.sandbox.ebay.com/buy/browse/v1/item_summary/search"
    f"?q={query}&limit=10"
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
print(f"Searching eBay for: {search_term}")
print("----------------------------------")


# ============================================================
# 4. READ SEARCH RESULTS
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


    # --------------------------------------------------------
    # No Sandbox results
    # --------------------------------------------------------

    if not items:

        print("No listings found in eBay Sandbox.")
        print("This can be normal because Sandbox inventory is limited.")


    # --------------------------------------------------------
    # Display listings
    # --------------------------------------------------------

    for number, item in enumerate(items, start=1):

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
            "N/A"
        )

        currency = price_data.get(
            "currency",
            ""
        )


        item_url = item.get(
            "itemWebUrl",
            "No URL"
        )


        print(f"{number}. {title}")

        print(
            f"   Price: {price} {currency}"
        )

        print(
            f"   URL: {item_url}"
        )

        print()


# ============================================================
# 5. SHOW API ERRORS
# ============================================================

except urllib.error.HTTPError as error:

    print("ERROR searching eBay Browse API")
    print("HTTP status:", error.code)

    error_body = error.read().decode()

    print(error_body)

    raise


except Exception as error:

    print("ERROR searching eBay:")
    print(error)

    raise
