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

DEAL_WATCH_PERCENT = 10
GOOD_DEAL_PERCENT = 15
STRONG_DEAL_PERCENT = 20


print("=" * 70)
print("POKEMON PSA 10 DEAL WATCH")
print(f"Target: {CARD_NAME}")
print(f"Card ID: {CARD_ID}")
print("=" * 70)


# ============================================================
# 1. EBAY CREDENTIALS
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
# 3. TEXT NORMALISATION
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
# 4. EXACT CARD MATCHING
# ============================================================

def is_target_card(item):

    title = normalize(
        item.get("title", "")
    )

    condition = normalize(
        item.get("condition", "")
    )

    # Pikachu required
    if "pikachu" not in title:
        return False, "not_pikachu"

    # Card number required
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

    # PSA 10 required
    if not re.search(
        r"\bpsa[\s\-]*10\b",
        title
    ):
        return False, "not_psa10"

    # Van Gogh / Grey Felt Hat identity required
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

    # Exclude other graders
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

    # Exclude special / altered versions
    special_versions = [
        "signed",
        "signature",
        "autograph",
        "veronica taylor",
        "error card",
        "misprint",
    ]

    if any(
        term in title
        for term in special_versions
    ):
        return False, "special_version"

    # Exclude junk / accessories
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

    # Exclude multi-card listings
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

    # Condition should be graded if supplied
    if condition and "graded" not in condition:
        return False, "not_graded_condition"

    # Fixed-price listings only
    buying_options = item.get(
        "buyingOptions",
        []
    )

    if buying_options and "FIXED_PRICE" not in buying_options:
        return False, "not_fixed_price"

    # GBP price required
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

        price = float(
            price_value
        )

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
    f"Unique raw listings: {len(all_items)}"
)


# ============================================================
# 6. EXACT CARD FILTER
# ============================================================

matched_items = []
rejection_reasons = Counter()

for item in all_items.values():

    matched, reason = is_target_card(
        item
    )

    if matched:

        matched_items.append(
            item
        )

    else:

        rejection_reasons[
            reason
        ] += 1


print(
    f"Exact card matches: {len(matched_items)}"
)


# ============================================================
# 7. PRICE HELPER
# ============================================================

def get_price(item):

    return float(
        item["price"]["value"]
    )


raw_prices = [
    get_price(item)
    for item in matched_items
]


# ============================================================
# 8. PERCENTILE
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

    lower_index = int(
        position
    )

    upper_index = min(
        lower_index + 1,
        len(values) - 1
    )

    fraction = (
        position
        - lower_index
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
# 9. BUILD CLEAN MARKET BASELINE
# ============================================================

baseline_items = []
low_outlier_items = []
high_outlier_items = []

q1 = None
q3 = None
iqr = None
lower_bound = None
upper_bound = None


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

        price = get_price(
            item
        )

        if price < lower_bound:

            low_outlier_items.append(
                item
            )

        elif price > upper_bound:

            high_outlier_items.append(
                item
            )

        else:

            baseline_items.append(
                item
            )

else:

    baseline_items = (
        matched_items.copy()
    )


# Safety fallback
if not baseline_items:

    baseline_items = (
        matched_items.copy()
    )


baseline_prices = [
    get_price(item)
    for item in baseline_items
]


# ============================================================
# 10. MARKET SNAPSHOT
# ============================================================

print()
print("=" * 70)
print("CURRENT MARKET SNAPSHOT")
print("=" * 70)

print(
    f"Card: {CARD_NAME}"
)

print(
    f"Exact matches: {len(matched_items)}"
)

print(
    f"Normal market listings: {len(baseline_items)}"
)

print(
    f"Low-price outliers: {len(low_outlier_items)}"
)

print(
    f"High-price outliers removed: {len(high_outlier_items)}"
)


if baseline_prices:

    market_low = min(
        baseline_prices
    )

    market_median = statistics.median(
        baseline_prices
    )

    market_average = statistics.mean(
        baseline_prices
    )

    market_q1 = percentile(
        baseline_prices,
        0.25
    )

    market_q3 = percentile(
        baseline_prices,
        0.75
    )

    market_high = max(
        baseline_prices
    )

    print()

    print(
        f"Lowest normal asking price: £{market_low:,.2f}"
    )

    print(
        f"Q1 / 25th percentile: £{market_q1:,.2f}"
    )

    print(
        f"MARKET MEDIAN: £{market_median:,.2f}"
    )

    print(
        f"Average: £{market_average:,.2f}"
    )

    print(
        f"Q3 / 75th percentile: £{market_q3:,.2f}"
    )

    print(
        f"Highest normal asking price: £{market_high:,.2f}"
    )

else:

    market_median = None

    print(
        "No usable listings."
    )


# ============================================================
# 11. DEAL WATCH
# ============================================================

print()
print("=" * 70)
print("DEAL WATCH")
print("=" * 70)


if market_median:

    watch_price = (
        market_median
        * (
            1
            - DEAL_WATCH_PERCENT / 100
        )
    )

    good_price = (
        market_median
        * (
            1
            - GOOD_DEAL_PERCENT / 100
        )
    )

    strong_price = (
        market_median
        * (
            1
            - STRONG_DEAL_PERCENT / 100
        )
    )

    print(
        f"Market median: £{market_median:,.2f}"
    )

    print(
        f"10% below median: £{watch_price:,.2f}"
    )

    print(
        f"15% below median: £{good_price:,.2f}"
    )

    print(
        f"20% below median: £{strong_price:,.2f}"
    )

    print()


    # Include all exact matches here,
    # including unusually low prices.
    deal_candidates = []

    for item in matched_items:

        price = get_price(
            item
        )

        discount = (
            (
                market_median
                - price
            )
            / market_median
        ) * 100

        if discount >= DEAL_WATCH_PERCENT:

            deal_candidates.append(
                (
                    price,
                    discount,
                    item
                )
            )


    deal_candidates.sort(
        key=lambda x: x[0]
    )


    if not deal_candidates:

        print(
            "No listings currently 10%+ below market median."
        )


    for price, discount, item in deal_candidates:

        if discount >= STRONG_DEAL_PERCENT:

            deal_level = "STRONG DEAL"

        elif discount >= GOOD_DEAL_PERCENT:

            deal_level = "GOOD DEAL"

        else:

            deal_level = "WATCH"


        title = item.get(
            "title",
            "No title"
        )

        item_url = item.get(
            "itemWebUrl",
            ""
        )

        item_id = item.get(
            "itemId",
            ""
        )


        print(
            "-" * 70
        )

        print(
            deal_level
        )

        print(
            f"Price: £{price:,.2f}"
        )

        print(
            f"Discount vs median: {discount:.1f}%"
        )

        print(
            f"Title: {title}"
        )

        print(
            f"Item ID: {item_id}"
        )

        print(
            f"URL: {item_url}"
        )


        # Important:
        # an extreme low price can be a deal,
        # but can also indicate a bad listing.
        if (
            lower_bound is not None
            and price < lower_bound
        ):

            print(
                "WARNING: Price is below the statistical lower bound."
            )

            print(
                "Verify listing details carefully before buying."
            )


# ============================================================
# 12. HIGH OUTLIER REPORT
# ============================================================

print()
print("=" * 70)
print("HIGH PRICE OUTLIERS")
print("=" * 70)


if high_outlier_items:

    for item in sorted(
        high_outlier_items,
        key=get_price
    ):

        print(
            f"£{get_price(item):,.2f} | "
            f"{item.get('title', 'No title')}"
        )

else:

    print(
        "No high-price outliers."
    )


# ============================================================
# 13. MATCH FILTER REPORT
# ============================================================

print()
print("=" * 70)
print("FILTER REPORT")
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
        "No identity-filter rejections."
    )


# ============================================================
# FINISH
# ============================================================

print()
print("=" * 70)
print("IMPORTANT")
print("=" * 70)

print(
    "Prices shown are live eBay asking prices, not sold prices."
)

print(
    "No price-history data is saved by this script."
)

print()
print(
    "Tracker completed successfully."
)
