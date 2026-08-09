import os
import base64
import urllib.parse
import urllib.request
import urllib.error
import json
import re
import statistics
from collections import Counter


# ============================================================
# TARGET CARD
# ============================================================

CARD_ID = "pikachu-grey-felt-hat-085-van-gogh-psa10"

CARD_NAME = "Pikachu with Grey Felt Hat #085 PSA 10"

SEARCH_TERMS = [
    "Pikachu Grey Felt Hat 085 PSA 10",
    "Pikachu Van Gogh 085 PSA 10",
]

print("=" * 60)
print("Pokemon PSA 10 Price Tracker")
print(f"Target: {CARD_NAME}")
print(f"Card ID: {CARD_ID}")
print("=" * 60)


# ============================================================
# 1. READ EBAY PRODUCTION CREDENTIALS
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
    "scope": "https://api.ebay.com/oauth/api_scope",
}).encode()

token_request = urllib.request.Request(
    token_url,
    data=token_data,
    method="POST",
)

token_request.add_header(
    "Authorization",
    f"Basic {encoded_credentials}",
)

token_request.add_header(
    "Content-Type",
    "application/x-www-form-urlencoded",
)


try:

    with urllib.request.urlopen(token_request) as response:
        token_result = json.loads(
            response.read().decode()
        )

    access_token = token_result["access_token"]

    print()
    print("SUCCESS: Connected to eBay Production")


except urllib.error.HTTPError as error:

    print("ERROR getting eBay access token")
    print("HTTP status:", error.code)
    print(error.read().decode())
    raise


except Exception as error:

    print("ERROR connecting to eBay:")
    print(error)
    raise


# ============================================================
# 3. NORMALISE TEXT
# ============================================================

def normalize(text):

    text = text.lower()

    text = text.replace("–", "-")
    text = text.replace("—", "-")
    text = text.replace("’", "'")

    text = re.sub(
        r"\s+",
        " ",
        text
    )

    return text.strip()


# ============================================================
# 4. STRICT CARD MATCHING
# ============================================================

def is_target_card(item):

    title_original = item.get(
        "title",
        ""
    )

    title = normalize(title_original)

    condition = normalize(
        item.get(
            "condition",
            ""
        )
    )


    # --------------------------------------------------------
    # Must contain Pikachu
    # --------------------------------------------------------

    if "pikachu" not in title:
        return False, "not_pikachu"


    # --------------------------------------------------------
    # Must contain card number 085 / 85
    # --------------------------------------------------------

    card_number_match = re.search(
        r"(?<!\d)0?85(?!\d)",
        title
    )

    if not card_number_match:
        return False, "wrong_card_number"


    # --------------------------------------------------------
    # Must explicitly say PSA 10
    # --------------------------------------------------------

    psa10_match = re.search(
        r"\bpsa[\s\-]*10\b",
        title
    )

    if not psa10_match:
        return False, "not_psa10"


    # --------------------------------------------------------
    # Must identify Van Gogh / Grey Felt Hat
    # --------------------------------------------------------

    identity_terms = [
        "grey felt hat",
        "gray felt hat",
        "van gogh",
    ]

    if not any(
        term in title
        for term in identity_terms
    ):
        return False, "wrong_card_identity"


    # --------------------------------------------------------
    # Exclude other graders
    # --------------------------------------------------------

    other_graders = [
        "cgc",
        "bgs",
        "beckett",
        "ace grading",
        "ace 10",
        "sgc",
    ]

    if any(
        grader in title
        for grader in other_graders
    ):
        return False, "other_grader"


    # --------------------------------------------------------
    # Exclude obvious non-card / junk results
    # --------------------------------------------------------

    excluded_terms = [
        "mystery",
        "proxy",
        "replica",
        "reprint",
        "custom",
        "digital",
        "metal card",
        "postcard",
        "poster",
        "art print",
        "sticker",
        "booster",
        "mystery pack",
        "mystery slab",
        "lot of",
        "bundle",
        "case only",
        "protector only",
        "display only",
    ]

    if any(
        term in title
        for term in excluded_terms
    ):
        return False, "excluded_product"


    # --------------------------------------------------------
    # Prefer actual graded-card condition
    # --------------------------------------------------------

    if condition and "graded" not in condition:
        return False, "not_graded_condition"


    # --------------------------------------------------------
    # Must have a usable GBP price
    # --------------------------------------------------------

    price_data = item.get(
        "price",
        {}
    )

    price_value = price_data.get(
        "value"
    )

    currency = price_data.get(
        "currency",
        ""
    )

    if price_value is None:
        return False, "no_price"


    if currency != "GBP":
        return False, "not_gbp"


    try:
        float(price_value)

    except (ValueError, TypeError):
        return False, "invalid_price"


    return True, "accepted"


# ============================================================
# 5. SEARCH EBAY UK
# ============================================================

all_items = {}

for search_term in SEARCH_TERMS:

    print()
    print(f"Searching: {search_term}")

    params = urllib.parse.urlencode({
        "q": search_term,
        "limit": "50",
    })

    search_url = (
        "https://api.ebay.com/buy/browse/v1/"
        f"item_summary/search?{params}"
    )

    search_request = urllib.request.Request(
        search_url,
        method="GET",
    )

    search_request.add_header(
        "Authorization",
        f"Bearer {access_token}",
    )

    search_request.add_header(
        "X-EBAY-C-MARKETPLACE-ID",
        "EBAY_GB",
    )


    try:

        with urllib.request.urlopen(
            search_request
        ) as response:

            search_result = json.loads(
                response.read().decode()
            )

        search_items = search_result.get(
            "itemSummaries",
            []
        )

        print(
            f"Raw results: {len(search_items)}"
        )


        # Deduplicate results from our two searches
        for item in search_items:

            item_id = item.get(
                "itemId"
            )

            if item_id:
                all_items[item_id] = item


    except urllib.error.HTTPError as error:

        print("ERROR searching eBay")
        print("HTTP status:", error.code)
        print(error.read().decode())
        raise


    except Exception as error:

        print("ERROR searching eBay:")
        print(error)
        raise


print()
print(
    f"Unique raw listings found: {len(all_items)}"
)


# ============================================================
# 6. FILTER ONLY THE EXACT CARD
# ============================================================

matched_items = []

rejection_reasons = Counter()


for item in all_items.values():

    matched, reason = is_target_card(item)

    if matched:
        matched_items.append(item)

    else:
        rejection_reasons[reason] += 1


# ============================================================
# 7. SORT MATCHES BY PRICE
# ============================================================

matched_items.sort(
    key=lambda item: float(
        item.get(
            "price",
            {}
        ).get(
            "value",
            999999
        )
    )
)


# ============================================================
# 8. DISPLAY VALID LISTINGS
# ============================================================

print()
print("=" * 60)
print("MATCHED VAN GOGH PIKACHU PSA 10 LISTINGS")
print("=" * 60)

prices = []


for number, item in enumerate(
    matched_items,
    start=1
):

    title = item.get(
        "title",
        "No title"
    )

    item_id = item.get(
        "itemId",
        ""
    )

    price_data = item.get(
        "price",
        {}
    )

    price = float(
        price_data.get(
            "value"
        )
    )

    currency = price_data.get(
        "currency",
        ""
    )

    condition = item.get(
        "condition",
        "N/A"
    )

    item_url = item.get(
        "itemWebUrl",
        ""
    )

    prices.append(price)

    print()
    print(f"{number}. {title}")

    print(
        f"   Price: £{price:,.2f}"
    )

    print(
        f"   Condition: {condition}"
    )

    print(
        f"   Item ID: {item_id}"
    )

    print(
        f"   URL: {item_url}"
    )


# ============================================================
# 9. CALCULATE CURRENT MARKET SNAPSHOT
# ============================================================

print()
print("=" * 60)
print("CURRENT MARKET SNAPSHOT")
print("=" * 60)

print(
    f"Card: {CARD_NAME}"
)

print(
    f"Valid listings: {len(prices)}"
)


if prices:

    lowest_price = min(prices)

    highest_price = max(prices)

    median_price = statistics.median(
        prices
    )

    average_price = statistics.mean(
        prices
    )

    print(
        f"Lowest asking price: £{lowest_price:,.2f}"
    )

    print(
        f"Median asking price: £{median_price:,.2f}"
    )

    print(
        f"Average asking price: £{average_price:,.2f}"
    )

    print(
        f"Highest asking price: £{highest_price:,.2f}"
    )

else:

    print(
        "No listings passed the strict matching rules."
    )


# ============================================================
# 10. SHOW FILTERING REPORT
# ============================================================

print()
print("=" * 60)
print("FILTER REPORT")
print("=" * 60)

for reason, count in rejection_reasons.items():

    print(
        f"{reason}: {count}"
    )


print()
print(
    "History saving is currently disabled."
)

print(
    "Tracker completed successfully."
)
