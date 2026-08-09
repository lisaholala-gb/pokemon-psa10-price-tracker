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


# ============================================================
# 30-DAY ACTUAL SOLD BENCHMARK
# ============================================================
#
# Manually derived from eBay Product Research:
# UK marketplace
# 10 Jul 2026 - 9 Aug 2026
# Explicit PSA 10 Van Gogh Pikachu #085 sales only
# Delivered price = sold price + postage
#
# This benchmark does NOT automatically update yet.
# ============================================================

SOLD_DELIVERED_MEDIAN_GBP = 1918.63


# Deal thresholds versus ACTUAL SOLD median

WATCH_PERCENT = 10
GOOD_DEAL_PERCENT = 15
STRONG_DEAL_PERCENT = 20


print("=" * 72)
print("POKEMON PSA 10 TRUE DEAL FINDER")
print(f"Target: {CARD_NAME}")
print(f"Card ID: {CARD_ID}")
print("=" * 72)


# ============================================================
# 1. READ GITHUB SECRETS
# ============================================================

client_id = os.environ["EBAY_CLIENT_ID"]
client_secret = os.environ["EBAY_CLIENT_SECRET"]

buyer_postcode = os.environ.get(
    "BUYER_POSTCODE",
    ""
).strip()


if not buyer_postcode:

    print()
    print("WARNING: BUYER_POSTCODE is missing.")
    print("Shipping estimates may be incomplete.")
    print()


# ============================================================
# 2. GET EBAY PRODUCTION ACCESS TOKEN
# ============================================================

credentials = f"{client_id}:{client_secret}"

encoded_credentials = base64.b64encode(
    credentials.encode()
).decode()


token_url = (
    "https://api.ebay.com/"
    "identity/v1/oauth2/token"
)


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
    f"Basic {encoded_credentials}"
)


token_request.add_header(
    "Content-Type",
    "application/x-www-form-urlencoded"
)


try:

    with urllib.request.urlopen(
        token_request
    ) as response:

        token_result = json.loads(
            response.read().decode()
        )

    access_token = token_result[
        "access_token"
    ]

    print()
    print("SUCCESS: Connected to eBay Production")


except urllib.error.HTTPError as error:

    print("ERROR getting eBay access token")
    print("HTTP status:", error.code)
    print(error.read().decode())

    raise


except Exception as error:

    print("ERROR connecting to eBay Production:")
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
# 4. STRICT TARGET CARD MATCHING
# ============================================================

def is_target_card(item):

    title = normalize(
        item.get(
            "title",
            ""
        )
    )

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
    # Must contain card number 085 / SVP085
    # --------------------------------------------------------

    card_number_patterns = [
        r"\b085\b",
        r"\b85\b",
        r"\bsvp[\s\-]*085\b",
        r"\bsvp[\s\-]*85\b",
    ]


    if not any(
        re.search(
            pattern,
            title
        )
        for pattern in card_number_patterns
    ):

        return False, "wrong_card_number"


    # --------------------------------------------------------
    # Must explicitly say PSA 10
    # --------------------------------------------------------

    if not re.search(
        r"\bpsa[\s\-]*10\b",
        title
    ):

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
    # Exclude competing grading companies
    # --------------------------------------------------------

    other_graders = [
        "ace 10",
        "ace grading",
        "cgc",
        "bgs",
        "beckett",
        "sgc",
    ]


    if any(
        grader in title
        for grader in other_graders
    ):

        return False, "other_grader"


    # --------------------------------------------------------
    # Exclude autographs / unusual premium versions
    # --------------------------------------------------------

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


    # --------------------------------------------------------
    # Exclude obvious wrong products
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


    # --------------------------------------------------------
    # Exclude multi-card listings
    # --------------------------------------------------------

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


    # --------------------------------------------------------
    # Must normally be eBay graded condition
    # --------------------------------------------------------

    if (
        condition
        and "graded" not in condition
    ):

        return False, "not_graded_condition"


    # --------------------------------------------------------
    # Only immediately purchasable listings
    # --------------------------------------------------------

    buying_options = item.get(
        "buyingOptions",
        []
    )


    if (
        buying_options
        and "FIXED_PRICE" not in buying_options
    ):

        return False, "not_fixed_price"


    # --------------------------------------------------------
    # Must have GBP price
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

        price = float(
            price_value
        )

    except (
        ValueError,
        TypeError
    ):

        return False, "invalid_price"


    if price <= 0:

        return False, "invalid_price"


    return True, "accepted"


# ============================================================
# 5. GET ITEM PRICE
# ============================================================

def get_item_price(item):

    return float(
        item[
            "price"
        ][
            "value"
        ]
    )


# ============================================================
# 6. GET SHIPPING COST
# ============================================================

def get_shipping_cost(item):

    shipping_options = item.get(
        "shippingOptions",
        []
    )


    valid_shipping_costs = []


    for option in shipping_options:

        shipping_cost = option.get(
            "shippingCost",
            {}
        )


        value = shipping_cost.get(
            "value"
        )


        currency = shipping_cost.get(
            "currency",
            ""
        )


        if value is None:

            continue


        if currency != "GBP":

            continue


        try:

            cost = float(
                value
            )

        except (
            ValueError,
            TypeError
        ):

            continue


        if cost >= 0:

            valid_shipping_costs.append(
                cost
            )


    if not valid_shipping_costs:

        return None


    # Use cheapest available shipping option

    return min(
        valid_shipping_costs
    )


# ============================================================
# 7. DELIVERED PRICE
# ============================================================

def get_delivered_price(item):

    item_price = get_item_price(
        item
    )


    shipping_cost = get_shipping_cost(
        item
    )


    if shipping_cost is None:

        return None


    return (
        item_price
        + shipping_cost
    )


# ============================================================
# 8. BUILD EBAY END USER CONTEXT HEADER
# ============================================================

def build_end_user_context():

    if not buyer_postcode:

        return None


    location = (
        "country=GB,"
        f"zip={buyer_postcode}"
    )


    encoded_location = (
        urllib.parse.quote(
            location,
            safe=""
        )
    )


    return (
        "contextualLocation="
        f"{encoded_location}"
    )


end_user_context = (
    build_end_user_context()
)


# ============================================================
# 9. SEARCH EBAY UK
# ============================================================

all_items = {}


for search_term in SEARCH_TERMS:

    print()
    print(
        f"Searching: {search_term}"
    )


    params = {
        "q": search_term,
        "limit": "50",
        "filter": "deliveryCountry:GB",
    }


    search_url = (
        "https://api.ebay.com/"
        "buy/browse/v1/"
        "item_summary/search?"
        + urllib.parse.urlencode(
            params
        )
    )


    search_request = urllib.request.Request(
        search_url,
        method="GET",
    )


    search_request.add_header(
        "Authorization",
        f"Bearer {access_token}"
    )


    search_request.add_header(
        "X-EBAY-C-MARKETPLACE-ID",
        "EBAY_GB"
    )


    if end_user_context:

        search_request.add_header(
            "X-EBAY-C-ENDUSERCTX",
            end_user_context
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


        # Deduplicate between search phrases

        for item in search_items:

            item_id = item.get(
                "itemId"
            )


            if item_id:

                all_items[
                    item_id
                ] = item


    except urllib.error.HTTPError as error:

        print()
        print("ERROR searching eBay Browse API")
        print("HTTP status:", error.code)
        print(error.read().decode())

        raise


    except Exception as error:

        print()
        print("ERROR searching eBay:")
        print(error)

        raise


print()
print(
    f"Unique raw listings: {len(all_items)}"
)


# ============================================================
# 10. EXACT CARD FILTER
# ============================================================

matched_items = []

rejection_reasons = Counter()


for item in all_items.values():

    matched, reason = (
        is_target_card(
            item
        )
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
    f"Exact PSA 10 matches: {len(matched_items)}"
)


# ============================================================
# 11. SHIPPING COVERAGE
# ============================================================

known_shipping_items = []

unknown_shipping_items = []


for item in matched_items:

    shipping_cost = (
        get_shipping_cost(
            item
        )
    )


    if shipping_cost is None:

        unknown_shipping_items.append(
            item
        )


    else:

        known_shipping_items.append(
            item
        )


print(
    "Listings with shipping estimate: "
    f"{len(known_shipping_items)}"
)


print(
    "Listings with shipping unavailable: "
    f"{len(unknown_shipping_items)}"
)


# ============================================================
# 12. CURRENT LIVE MARKET SNAPSHOT
# ============================================================

delivered_prices = []


for item in known_shipping_items:

    delivered_price = (
        get_delivered_price(
            item
        )
    )


    if delivered_price is not None:

        delivered_prices.append(
            delivered_price
        )


print()
print("=" * 72)
print("LIVE MARKET SNAPSHOT")
print("=" * 72)


if delivered_prices:

    live_median = statistics.median(
        delivered_prices
    )


    live_average = statistics.mean(
        delivered_prices
    )


    live_low = min(
        delivered_prices
    )


    live_high = max(
        delivered_prices
    )


    print(
        f"Listings analysed: "
        f"{len(delivered_prices)}"
    )


    print(
        "Lowest delivered asking price: "
        f"£{live_low:,.2f}"
    )


    print(
        "Live delivered median: "
        f"£{live_median:,.2f}"
    )


    print(
        "Live delivered average: "
        f"£{live_average:,.2f}"
    )


    print(
        "Highest delivered asking price: "
        f"£{live_high:,.2f}"
    )


else:

    live_median = None

    print(
        "No usable delivered-price listings found."
    )


# ============================================================
# 13. ACTUAL SOLD MARKET BENCHMARK
# ============================================================

print()
print("=" * 72)
print("30-DAY ACTUAL SOLD MARKET")
print("=" * 72)


print(
    "Clean PSA 10 delivered median:"
)

print(
    f"£{SOLD_DELIVERED_MEDIAN_GBP:,.2f}"
)


watch_threshold = (
    SOLD_DELIVERED_MEDIAN_GBP
    * (
        1
        - WATCH_PERCENT / 100
    )
)


good_threshold = (
    SOLD_DELIVERED_MEDIAN_GBP
    * (
        1
        - GOOD_DEAL_PERCENT / 100
    )
)


strong_threshold = (
    SOLD_DELIVERED_MEDIAN_GBP
    * (
        1
        - STRONG_DEAL_PERCENT / 100
    )
)


print()

print(
    f"WATCH (-10%): "
    f"£{watch_threshold:,.2f}"
)


print(
    f"GOOD DEAL (-15%): "
    f"£{good_threshold:,.2f}"
)


print(
    f"STRONG DEAL (-20%): "
    f"£{strong_threshold:,.2f}"
)


# ============================================================
# 14. TRUE DEAL WATCH
# ============================================================

print()
print("=" * 72)
print("TRUE DEAL WATCH")
print("=" * 72)


deal_candidates = []


for item in known_shipping_items:

    delivered_price = (
        get_delivered_price(
            item
        )
    )


    if delivered_price is None:

        continue


    discount_percent = (
        (
            SOLD_DELIVERED_MEDIAN_GBP
            - delivered_price
        )
        / SOLD_DELIVERED_MEDIAN_GBP
    ) * 100


    if discount_percent >= WATCH_PERCENT:

        deal_candidates.append(
            (
                delivered_price,
                discount_percent,
                item
            )
        )


deal_candidates.sort(
    key=lambda result: result[0]
)


if not deal_candidates:

    print()
    print(
        "No current listings are at least "
        "10% below the 30-day actual sold median."
    )


for (
    delivered_price,
    discount_percent,
    item
) in deal_candidates:

    item_price = (
        get_item_price(
            item
        )
    )


    shipping_cost = (
        get_shipping_cost(
            item
        )
    )


    if (
        discount_percent
        >= STRONG_DEAL_PERCENT
    ):

        deal_level = (
            "STRONG DEAL"
        )


    elif (
        discount_percent
        >= GOOD_DEAL_PERCENT
    ):

        deal_level = (
            "GOOD DEAL"
        )


    else:

        deal_level = (
            "WATCH"
        )


    title = item.get(
        "title",
        "No title"
    )


    item_id = item.get(
        "itemId",
        ""
    )


    item_url = item.get(
        "itemWebUrl",
        ""
    )


    print()
    print("-" * 72)

    print(
        deal_level
    )


    print(
        f"Item price: "
        f"£{item_price:,.2f}"
    )


    print(
        f"Shipping: "
        f"£{shipping_cost:,.2f}"
    )


    print(
        f"DELIVERED PRICE: "
        f"£{delivered_price:,.2f}"
    )


    print(
        f"30-day sold median: "
        f"£{SOLD_DELIVERED_MEDIAN_GBP:,.2f}"
    )


    print(
        "Discount vs actual sold market: "
        f"{discount_percent:.1f}%"
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


# ============================================================
# 15. CHEAPEST CURRENT LISTINGS
# ============================================================

print()
print("=" * 72)
print("CHEAPEST CURRENT LISTINGS")
print("=" * 72)


sorted_current_items = sorted(
    known_shipping_items,
    key=lambda item: (
        get_delivered_price(item)
        if get_delivered_price(item)
        is not None
        else float("inf")
    )
)


for number, item in enumerate(
    sorted_current_items[:5],
    start=1
):

    item_price = (
        get_item_price(
            item
        )
    )


    shipping_cost = (
        get_shipping_cost(
            item
        )
    )


    delivered_price = (
        get_delivered_price(
            item
        )
    )


    difference_percent = (
        (
            delivered_price
            - SOLD_DELIVERED_MEDIAN_GBP
        )
        / SOLD_DELIVERED_MEDIAN_GBP
    ) * 100


    print()
    print(
        f"{number}. "
        f"{item.get('title', 'No title')}"
    )


    print(
        f"   Item: £{item_price:,.2f}"
    )


    print(
        f"   Shipping: £{shipping_cost:,.2f}"
    )


    print(
        f"   Delivered: £{delivered_price:,.2f}"
    )


    print(
        "   Vs sold median: "
        f"{difference_percent:+.1f}%"
    )


    print(
        f"   URL: "
        f"{item.get('itemWebUrl', '')}"
    )


# ============================================================
# 16. SHIPPING UNKNOWN
# ============================================================

if unknown_shipping_items:

    print()
    print("=" * 72)
    print("NOT SCORED - SHIPPING UNKNOWN")
    print("=" * 72)


    for item in sorted(
        unknown_shipping_items,
        key=get_item_price
    ):

        print()

        print(
            f"Item price: "
            f"£{get_item_price(item):,.2f}"
        )


        print(
            f"Title: "
            f"{item.get('title', 'No title')}"
        )


        print(
            "Reason: eBay did not return a usable "
            "GBP shipping estimate."
        )


        print(
            f"URL: "
            f"{item.get('itemWebUrl', '')}"
        )


# ============================================================
# 17. FILTER REPORT
# ============================================================

print()
print("=" * 72)
print("FILTER REPORT")
print("=" * 72)


if rejection_reasons:

    for reason, count in sorted(
        rejection_reasons.items()
    ):

        print(
            f"{reason}: {count}"
        )


else:

    print(
        "No listings rejected."
    )


# ============================================================
# 18. IMPORTANT NOTES
# ============================================================

print()
print("=" * 72)
print("IMPORTANT")
print("=" * 72)


print(
    "1. Live prices are current eBay asking prices."
)


print(
    "2. Delivered price = item price + available "
    "eBay shipping estimate."
)


print(
    "3. Deal ratings compare against the manually "
    "calculated 30-day actual sold delivered median."
)


print(
    "4. The £1,918.63 sold benchmark does not "
    "automatically refresh yet."
)


print(
    "5. No eBay marketplace price history is saved."
)


print()
print(
    "Tracker completed successfully."
)
