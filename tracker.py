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


print("=" * 70)
print("Pokemon PSA 10 Price Tracker")
print(f"Target: {CARD_NAME}")
print(f"Card ID: {CARD_ID}")
print("=" * 70)


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

    text = str(text).lower()

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

    # Must be Pikachu
    if "pikachu" not in title:
        return False, "not_pikachu"

    # Must contain card number 085 / SVP085 / SVP 085
    number_patterns = [
        r"\b085\b",
        r"\b85\b",
        r"\bsvp[\s\-]*085\b",
        r"\bsvp[\s\-]*85\b",
    ]

    if not any(
        re.search(pattern, title)
        for pattern in number_patterns
    ):
        return False, "wrong_card_number"

    # Must explicitly be PSA 10
    if not re.search(
        r"\bpsa[\s\-]*10\b",
        title
    ):
        return False, "not_psa10"

    # Must identify Grey Felt Hat / Van Gogh
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

    # Exclude other grading companies
    other_graders = [
        "cgc",
        "bgs",
        "beckett",
        "ace 10",
        "ace grading",
        "sgc",
    ]

    if any(
        grader in title
        for grader in other_graders
    ):
        return False, "other_grader"

    # Exclude obvious wrong product types
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
        "case only",
        "protector only",
        "display only",
        "empty case",
    ]

    if any(
        term in title
        for term in excluded_terms
    ):
        return False, "excluded_product"

    # Avoid obvious multi-card lots / bundles
    multi_item_terms = [
        "bundle",
        "lot of",
        "set of 2",
        "set of 3",
        "2 cards",
        "3 cards",
        "pair of",
    ]

    if any(
        term in title
        for term in multi_item_terms
    ):
        return False, "multi_card_listing"

    # eBay condition should normally say graded
    if condition and "graded" not in condition:
        return False, "not_graded_condition"

    # Must have usable GBP price
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
        price = float(price_value)

    except (ValueError, TypeError):
        return False, "invalid_price"

    if price <= 0:
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

        # Deduplicate the two searches using item ID
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
# 6. FILTER EXACT CARD
# ============================================================

matched_items = []

rejection_reasons = Counter()


for item in all_items.values():

    matched, reason = is_target_card(item)

    if matched:
        matched_items.append(item)

    else:
        rejection_reasons[reason] += 1


print(
    f"Exact card matches before price cleaning: {len(matched_items)}"
)


# ============================================================
# 7. GET PRICES
# ============================================================

raw_prices = []

for item in matched_items:

    try:
        price = float(
            item["price"]["value"]
        )

        raw_prices.append(price)

    except (
        KeyError,
        ValueError,
        TypeError
    ):
        pass


# ============================================================
# 8. PERCENTILE HELPER
# ============================================================

def percentile(values, percent):

    values = sorted(values)

    if not values:
        return None

    if len(values) == 1:
        return values[0]

    position = (
        len(values) - 1
    ) * percent

    lower_index = int(position)

    upper_index = min(
        lower_index + 1,
        len(values) - 1
    )

    fraction = (
        position - lower_index
    )

    lower_value = values[
        lower_index
    ]

    upper_value = values[
        upper_index
    ]

    return (
        lower_value
        + (
            upper_value
            - lower_value
        )
        * fraction
    )


# ============================================================
# 9. IQR OUTLIER FILTER
# ============================================================

clean_items = []

outlier_items = []

lower_bound = None
upper_bound = None

q1 = None
q3 = None
iqr = None


if len(raw_prices) >= 4:

    q1 = percentile(
        raw_prices,
        0.25
    )

    q3 = percentile(
        raw_prices,
        0.75
    )

    iqr = q3 - q1

    lower_bound = max(
        0,
        q1 - (1.5 * iqr)
    )

    upper_bound = (
        q3 + (1.5 * iqr)
    )

    for item in matched_items:

        price = float(
            item["price"]["value"]
        )

        if (
            lower_bound
            <= price
            <= upper_bound
        ):
            clean_items.append(
                item
            )

        else:
            outlier_items.append(
                item
            )

else:

    # Not enough data for reliable IQR.
    clean_items = matched_items.copy()


# ============================================================
# 10. SORT CLEAN LISTINGS BY PRICE
# ============================================================

clean_items.sort(
    key=lambda item: float(
        item["price"]["value"]
    )
)


# ============================================================
# 11. DISPLAY CLEAN LISTINGS
# ============================================================

print()
print("=" * 70)
print("CLEAN VAN GOGH PIKACHU PSA 10 LISTINGS")
print("=" * 70)


clean_prices = []


for number, item in enumerate(
    clean_items,
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

    price = float(
        item["price"]["value"]
    )

    condition = item.get(
        "condition",
        "N/A"
    )

    item_url = item.get(
        "itemWebUrl",
        ""
    )

    clean_prices.append(
        price
    )

    print()
    print(
        f"{number}. {title}"
    )

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
# 12. MARKET SNAPSHOT
# ============================================================

print()
print("=" * 70)
print("CURRENT MARKET SNAPSHOT")
print("=" * 70)

print(
    f"Card: {CARD_NAME}"
)

print(
    f"Raw exact matches: {len(matched_items)}"
)

print(
    f"Outliers removed: {len(outlier_items)}"
)

print(
    f"Clean listings: {len(clean_items)}"
)


if clean_prices:

    lowest_price = min(
        clean_prices
    )

    highest_price = max(
        clean_prices
    )

    median_price = statistics.median(
        clean_prices
    )

    average_price = statistics.mean(
        clean_prices
    )

    q1_clean = percentile(
        clean_prices,
        0.25
    )

    q3_clean = percentile(
        clean_prices,
        0.75
    )

    print()

    print(
        f"Lowest asking price: £{lowest_price:,.2f}"
    )

    print(
        f"25th percentile: £{q1_clean:,.2f}"
    )

    print(
        f"Median asking price: £{median_price:,.2f}"
    )

    print(
        f"Average asking price: £{average_price:,.2f}"
    )

    print(
        f"75th percentile: £{q3_clean:,.2f}"
    )

    print(
        f"Highest clean asking price: £{highest_price:,.2f}"
    )

else:

    print()
    print(
        "No valid clean listings found."
    )


# ============================================================
# 13. OUTLIER REPORT
# ============================================================

print()
print("=" * 70)
print("OUTLIER REPORT")
print("=" * 70)


if (
    q1 is not None
    and q3 is not None
):

    print(
        f"Q1: £{q1:,.2f}"
    )

    print(
        f"Q3: £{q3:,.2f}"
    )

    print(
        f"IQR: £{iqr:,.2f}"
    )

    print(
        f"Lower bound: £{lower_bound:,.2f}"
    )

    print(
        f"Upper bound: £{upper_bound:,.2f}"
    )

    print(
        f"Removed listings: {len(outlier_items)}"
    )


    if outlier_items:

        print()
        print(
            "Excluded price outliers:"
        )

        for item in sorted(
            outlier_items,
            key=lambda x: float(
                x["price"]["value"]
            )
        ):

            title = item.get(
                "title",
                "No title"
            )

            price = float(
                item["price"]["value"]
            )

            print(
                f"£{price:,.2f} | {title}"
            )

else:

    print(
        "Not enough listings to calculate IQR."
    )


# ============================================================
# 14. FILTER REPORT
# ============================================================

print()
print("=" * 70)
print("MATCHING FILTER REPORT")
print("=" * 70)


if rejection_reasons:

    for reason, count in sorted(
        rejection_reasons.items()
    ):

        print(
            f"{reason}: {count}"
        )

else:

    print(
        "No listings rejected by identity filters."
    )


print()
print("=" * 70)
print("IMPORTANT")
print("=" * 70)

print(
    "These are live eBay asking prices, not sold prices."
)

print(
    "History saving is disabled."
)

print(
    "No eBay marketplace data is persisted by this script."
)

print()
print(
    "Tracker completed successfully."
)
