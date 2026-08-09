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
# SOLD MARKET BENCHMARK
# ============================================================
#
# Source:
# eBay Product Research
# UK
# 10 Jul 2026 - 9 Aug 2026
#
# Clean PSA 10 sold listings
# Item price + postage
#
# This is a MANUAL benchmark.
# It does NOT automatically update.
# ============================================================

SOLD_DELIVERED_MEDIAN_GBP = 1918.63

WATCH_PERCENT = 10
GOOD_DEAL_PERCENT = 15
STRONG_DEAL_PERCENT = 20


print("=" * 72)
print("POKEMON DEAL FINDER")
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
    print("WARNING:")
    print("BUYER_POSTCODE is missing.")
    print("Calculated shipping may be unavailable or inaccurate.")
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

    print(
        "SUCCESS: Connected to eBay Production"
    )


except urllib.error.HTTPError as error:

    print(
        "ERROR getting eBay access token"
    )

    print(
        "HTTP status:",
        error.code
    )

    print(
        error.read().decode()
    )

    raise


except Exception as error:

    print(
        "ERROR connecting to eBay:"
    )

    print(error)

    raise


# ============================================================
# 3. NORMALISE TEXT
# ============================================================

def normalize(text):

    text = str(text).lower()

    text = text.replace(
        "–",
        "-"
    )

    text = text.replace(
        "—",
        "-"
    )

    text = text.replace(
        "’",
        "'"
    )

    text = re.sub(
        r"\s+",
        " ",
        text
    )

    return text.strip()


# ============================================================
# 4. MATCH ONLY THE EXACT CARD
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


    # Pikachu required
    if "pikachu" not in title:

        return (
            False,
            "not_pikachu"
        )


    # Card number 085 / SVP085 required
    number_patterns = [
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
        for pattern
        in number_patterns
    ):

        return (
            False,
            "wrong_card_number"
        )


    # PSA 10 required
    if not re.search(
        r"\bpsa[\s\-]*10\b",
        title
    ):

        return (
            False,
            "not_psa10"
        )


    # Card identity required
    identity_terms = [
        "grey felt hat",
        "gray felt hat",
        "van gogh",
    ]


    if not any(
        term in title
        for term
        in identity_terms
    ):

        return (
            False,
            "wrong_card_identity"
        )


    # Exclude competing graders
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
        for grader
        in other_graders
    ):

        return (
            False,
            "other_grader"
        )


    # Exclude unusual premium versions
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
        for term
        in special_versions
    ):

        return (
            False,
            "special_version"
        )


    # Exclude wrong products
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
        for term
        in excluded_terms
    ):

        return (
            False,
            "excluded_product"
        )


    # Exclude bundles / lots
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
        for term
        in multi_item_terms
    ):

        return (
            False,
            "multi_card_listing"
        )


    # Must be graded
    if (
        condition
        and "graded"
        not in condition
    ):

        return (
            False,
            "not_graded_condition"
        )


    # We want immediately buyable listings
    buying_options = item.get(
        "buyingOptions",
        []
    )


    if (
        buying_options
        and "FIXED_PRICE"
        not in buying_options
    ):

        return (
            False,
            "not_fixed_price"
        )


    # GBP item price required
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

        return (
            False,
            "no_price"
        )


    if currency != "GBP":

        return (
            False,
            "not_gbp"
        )


    try:

        price = float(
            price_value
        )

    except (
        ValueError,
        TypeError
    ):

        return (
            False,
            "invalid_price"
        )


    if price <= 0:

        return (
            False,
            "invalid_price"
        )


    return (
        True,
        "accepted"
    )


# ============================================================
# 5. ITEM PRICE
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
# 6. SHIPPING COST
# ============================================================

def get_shipping_cost(item):

    shipping_options = item.get(
        "shippingOptions",
        []
    )


    possible_costs = []


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


        if (
            value is None
            or currency != "GBP"
        ):

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

            possible_costs.append(
                cost
            )


    if not possible_costs:

        return None


    return min(
        possible_costs
    )


# ============================================================
# 7. DELIVERED PRICE
# ============================================================

def get_delivered_price(item):

    item_price = get_item_price(
        item
    )


    shipping = get_shipping_cost(
        item
    )


    if shipping is None:

        return None


    return (
        item_price
        + shipping
    )


# ============================================================
# 8. SEARCH EBAY UK
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


    query_string = (
        urllib.parse.urlencode(
            params
        )
    )


    search_url = (
        "https://api.ebay.com/"
        "buy/browse/v1/"
        "item_summary/search?"
        f"{query_string}"
    )


    search_request = (
        urllib.request.Request(
            search_url,
            method="GET"
        )
    )


    search_request.add_header(
        "Authorization",
        f"Bearer {access_token}"
    )


    search_request.add_header(
        "X-EBAY-C-MARKETPLACE-ID",
        "EBAY_GB"
    )


    # Improve shipping accuracy
    if buyer_postcode:

        contextual_location = (
            urllib.parse.quote(
                (
                    "country=GB,"
                    f"zip={buyer_postcode}"
                ),
                safe=""
            )
        )


        search_request.add_header(
            "X-EBAY-C-ENDUSERCTX",
            (
                "contextualLocation="
                f"{contextual_location}"
            )
        )


    try:

        with urllib.request.urlopen(
            search_request
        ) as response:

            result = json.loads(
                response.read().decode()
            )


        search_items = result.get(
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

                all_items[
                    item_id
                ] = item


    except urllib.error.HTTPError as error:

        print(
            "ERROR searching eBay"
        )

        print(
            "HTTP status:",
            error.code
        )

        print(
            error.read().decode()
        )

        raise


    except Exception as error:

        print(
            "ERROR searching eBay:"
        )

        print(error)

        raise


print()

print(
    f"Unique raw listings: {len(all_items)}"
)


# ============================================================
# 9. EXACT CARD FILTER
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
# 10. SHIPPING COVERAGE
# ============================================================

known_shipping_items = []

unknown_shipping_items = []


for item in matched_items:

    shipping = get_shipping_cost(
        item
    )


    if shipping is None:

        unknown_shipping_items.append(
            item
        )

    else:

        known_shipping_items.append(
            item
        )


print(
    f"Listings with shipping cost: "
    f"{len(known_shipping_items)}"
)

print(
    f"Listings with unknown shipping: "
    f"{len(unknown_shipping_items)}"
)


# ============================================================
# 11. LIVE MARKET SNAPSHOT
# ============================================================

delivered_prices = [
    get_delivered_price(
        item
    )
    for item
    in known_shipping_items
]


print()
print("=" * 72)
print("LIVE MARKET SNAPSHOT")
print("=" * 72)


if delivered_prices:

    live_median = statistics.median(
        delivered_prices
    )


    print(
        f"Listings analysed: "
        f"{len(delivered_prices)}"
    )


    print(
        "Live delivered median: "
        f"£{live_median:,.2f}"
    )


    print(
        "Lowest live delivered price: "
        f"£{min(delivered_prices):,.2f}"
    )


else:

    live_median = None

    print(
        "No listings have usable shipping data."
    )


# ============================================================
# 12. SOLD MARKET BENCHMARK
# ============================================================

print()
print("=" * 72)
print("30-DAY SOLD MARKET BENCHMARK")
print("=" * 72)


print(
    "Clean PSA 10 sold delivered median:"
)

print(
    f"£{SOLD_DELIVERED_MEDIAN_GBP:,.2f}"
)


watch_price = (
    SOLD_DELIVERED_MEDIAN_GBP
    * (
        1
        - WATCH_PERCENT / 100
    )
)


good_price = (
    SOLD_DELIVERED_MEDIAN_GBP
    * (
        1
        - GOOD_DEAL_PERCENT / 100
    )
)


strong_price = (
    SOLD_DELIVERED_MEDIAN_GBP
    * (
        1
        - STRONG_DEAL_PERCENT / 100
    )
)


print()

print(
    f"10% below sold median: "
    f"£{watch_price:,.2f}"
)

print(
    f"15% below sold median: "
    f"£{good_price:,.2f}"
)

print(
    f"20% below sold median: "
    f"£{strong_price:,.2f}"
)


# ============================================================
# 13. TRUE DEAL WATCH
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


    discount = (
        (
            SOLD_DELIVERED_MEDIAN_GBP
            - delivered_price
        )
        / SOLD_DELIVERED_MEDIAN_GBP
    ) * 100


    if discount >= WATCH_PERCENT:

        deal_candidates.append(
            (
                delivered_price,
                discount,
                item
            )
        )


deal_candidates.sort(
    key=lambda x: x[0]
)


if not deal_candidates:

    print(
        "No current listing is at least "
        "10% below the 30-day sold median."
    )


for (
    delivered_price,
    discount,
    item
) in deal_candidates:

    item_price = (
        get_item_price(
            item
        )
    )


    shipping = (
        get_shipping_cost(
            item
        )
    )


    if (
        discount
        >= STRONG_DEAL_PERCENT
    ):

        deal_level = (
            "STRONG DEAL"
        )


    elif (
        discount
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


    item_url = item.get(
        "itemWebUrl",
        ""
    )


    item_id = item.get(
        "itemId",
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
        f"£{shipping:,.2f}"
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
        f"{discount:.1f}%"
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
# 14. SHIPPING UNKNOWN
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
            "Reason: shipping cost unavailable"
        )

        print(
            f"URL: "
            f"{item.get('itemWebUrl', '')}"
        )


# ============================================================
# 15. FILTER REPORT
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
        "No identity-filter rejections."
    )


# ============================================================
# FINISH
# ============================================================

print()
print("=" * 72)
print("IMPORTANT")
print("=" * 72)

print(
    "Live prices include available shipping estimates."
)

print(
    "Deal ratings are compared with the manually "
    "calculated 30-day sold delivered median."
)

print(
    "The sold benchmark is not automatically refreshed yet."
)

print(
    "No eBay marketplace history is saved."
)

print()
print(
    "Tracker completed successfully."
)
