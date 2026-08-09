import os
import base64
import urllib.parse
import urllib.request
import urllib.error
import json
import re
import statistics
import smtplib
import ssl

from collections import Counter
from email.message import EmailMessage
from datetime import datetime, timezone


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
# MANUAL 30-DAY SOLD BENCHMARK
# ============================================================
#
# eBay Product Research
# UK
# Clean PSA 10 sold delivered-price benchmark
#
# IMPORTANT:
# This value does NOT update automatically yet.
# ============================================================

SOLD_DELIVERED_MEDIAN_GBP = 1918.63


WATCH_PERCENT = 10
GOOD_DEAL_PERCENT = 15
STRONG_DEAL_PERCENT = 20


# ============================================================
# READ GITHUB SECRETS
# ============================================================

client_id = os.environ["EBAY_CLIENT_ID"]

client_secret = os.environ["EBAY_CLIENT_SECRET"]

buyer_postcode = os.environ.get(
    "BUYER_POSTCODE",
    ""
).strip()


email_address = os.environ.get(
    "EMAIL_ADDRESS",
    ""
).strip()


email_app_password = os.environ.get(
    "EMAIL_APP_PASSWORD",
    ""
).replace(" ", "").strip()


force_email_test = (
    os.environ.get(
        "FORCE_EMAIL_TEST",
        ""
    ).lower()
    == "true"
)


print("=" * 72)
print("POKEMON DEAL FINDER")
print(f"Target: {CARD_NAME}")
print("=" * 72)


# ============================================================
# GET EBAY ACCESS TOKEN
# ============================================================

credentials = (
    f"{client_id}:{client_secret}"
)

encoded_credentials = (
    base64.b64encode(
        credentials.encode()
    ).decode()
)


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


# ============================================================
# NORMALISE TEXT
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
# CARD MATCHING
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


    if "pikachu" not in title:

        return False, "not_pikachu"


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

        return False, "wrong_card_number"


    if not re.search(
        r"\bpsa[\s\-]*10\b",
        title
    ):

        return False, "not_psa10"


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

        return False, "wrong_card_identity"


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

        return False, "other_grader"


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

        return False, "special_version"


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

        return False, "excluded_product"


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

        return False, "multi_card_listing"


    if (
        condition
        and "graded"
        not in condition
    ):

        return False, "not_graded_condition"


    buying_options = item.get(
        "buyingOptions",
        []
    )


    if (
        buying_options
        and "FIXED_PRICE"
        not in buying_options
    ):

        return False, "not_fixed_price"


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
# PRICE HELPERS
# ============================================================

def get_item_price(item):

    return float(
        item["price"]["value"]
    )


def get_shipping_cost(item):

    shipping_options = item.get(
        "shippingOptions",
        []
    )


    costs = []


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

            costs.append(
                cost
            )


    if not costs:

        return None


    return min(
        costs
    )


def get_delivered_price(item):

    shipping = get_shipping_cost(
        item
    )


    if shipping is None:

        return None


    return (
        get_item_price(item)
        + shipping
    )


# ============================================================
# SEARCH EBAY UK
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


    request = urllib.request.Request(
        search_url,
        method="GET"
    )


    request.add_header(
        "Authorization",
        f"Bearer {access_token}"
    )


    request.add_header(
        "X-EBAY-C-MARKETPLACE-ID",
        "EBAY_GB"
    )


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


        request.add_header(
            "X-EBAY-C-ENDUSERCTX",
            (
                "contextualLocation="
                f"{contextual_location}"
            )
        )


    try:

        with urllib.request.urlopen(
            request
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


print()

print(
    f"Unique raw listings: {len(all_items)}"
)


# ============================================================
# FILTER EXACT CARD
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
# SHIPPING COVERAGE
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


# ============================================================
# LIVE MARKET SNAPSHOT
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
        f"Live delivered median: "
        f"£{live_median:,.2f}"
    )


    print(
        f"Lowest delivered price: "
        f"£{min(delivered_prices):,.2f}"
    )


else:

    live_median = None

    print(
        "No usable shipping data."
    )


# ============================================================
# DEAL THRESHOLDS
# ============================================================

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
print("=" * 72)
print("30-DAY SOLD MARKET BENCHMARK")
print("=" * 72)

print(
    f"Sold delivered median: "
    f"£{SOLD_DELIVERED_MEDIAN_GBP:,.2f}"
)

print(
    f"WATCH threshold (-10%): "
    f"£{watch_price:,.2f}"
)

print(
    f"GOOD DEAL threshold (-15%): "
    f"£{good_price:,.2f}"
)

print(
    f"STRONG DEAL threshold (-20%): "
    f"£{strong_price:,.2f}"
)


# ============================================================
# TRUE DEAL WATCH
# ============================================================

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


print()
print("=" * 72)
print("TRUE DEAL WATCH")
print("=" * 72)


if not deal_candidates:

    print(
        "No qualifying deals found."
    )


for (
    delivered_price,
    discount,
    item
) in deal_candidates:


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


    print()

    print(
        deal_level
    )

    print(
        f"Item price: "
        f"£{get_item_price(item):,.2f}"
    )

    print(
        f"Shipping: "
        f"£{get_shipping_cost(item):,.2f}"
    )

    print(
        f"Delivered: "
        f"£{delivered_price:,.2f}"
    )

    print(
        f"Discount vs sold median: "
        f"{discount:.1f}%"
    )

    print(
        f"Title: "
        f"{item.get('title', '')}"
    )

    print(
        f"URL: "
        f"{item.get('itemWebUrl', '')}"
    )


# ============================================================
# EMAIL BODY
# ============================================================

def build_email_body():

    lines = []


    lines.append(
        "Pokemon Deal Tracker"
    )

    lines.append(
        ""
    )

    lines.append(
        CARD_NAME
    )

    lines.append(
        ""
    )


    lines.append(
        "30-day sold delivered median: "
        f"£{SOLD_DELIVERED_MEDIAN_GBP:,.2f}"
    )


    if live_median is not None:

        lines.append(
            "Current live delivered median: "
            f"£{live_median:,.2f}"
        )


    lines.append(
        ""
    )


    if deal_candidates:

        lines.append(
            f"Deals found: "
            f"{len(deal_candidates)}"
        )

        lines.append(
            ""
        )


        for (
            delivered_price,
            discount,
            item
        ) in deal_candidates:


            if (
                discount
                >= STRONG_DEAL_PERCENT
            ):

                level = (
                    "STRONG DEAL"
                )


            elif (
                discount
                >= GOOD_DEAL_PERCENT
            ):

                level = (
                    "GOOD DEAL"
                )


            else:

                level = (
                    "WATCH"
                )


            lines.append(
                "=" * 50
            )


            lines.append(
                level
            )


            lines.append(
                f"Item: "
                f"£{get_item_price(item):,.2f}"
            )


            lines.append(
                f"Shipping: "
                f"£{get_shipping_cost(item):,.2f}"
            )


            lines.append(
                f"Delivered: "
                f"£{delivered_price:,.2f}"
            )


            lines.append(
                "Discount vs sold market: "
                f"{discount:.1f}%"
            )


            lines.append(
                ""
            )


            lines.append(
                item.get(
                    "title",
                    ""
                )
            )


            lines.append(
                ""
            )


            lines.append(
                item.get(
                    "itemWebUrl",
                    ""
                )
            )


            lines.append(
                ""
            )


    else:

        lines.append(
            "No qualifying deals were found."
        )


    lines.append(
        ""
    )


    lines.append(
        "Run time UTC: "
        + datetime.now(
            timezone.utc
        ).strftime(
            "%Y-%m-%d %H:%M:%S"
        )
    )


    return "\n".join(
        lines
    )


# ============================================================
# SEND EMAIL
# ============================================================

should_send_email = (
    bool(deal_candidates)
    or force_email_test
)


if should_send_email:

    print()
    print("=" * 72)
    print("EMAIL ALERT")
    print("=" * 72)


    if (
        not email_address
        or not email_app_password
    ):

        raise RuntimeError(
            "EMAIL_ADDRESS or EMAIL_APP_PASSWORD is missing"
        )


    message = EmailMessage()


    if deal_candidates:

        best_discount = max(
            deal[1]
            for deal
            in deal_candidates
        )


        subject = (
            "Pokemon Deal Alert - "
            f"{best_discount:.1f}% below sold market"
        )


    else:

        subject = (
            "Pokemon Deal Tracker - TEST EMAIL"
        )


    message[
        "Subject"
    ] = subject


    message[
        "From"
    ] = email_address


    message[
        "To"
    ] = email_address


    message.set_content(
        build_email_body()
    )


    context = (
        ssl.create_default_context()
    )


    try:

        with smtplib.SMTP_SSL(
            "smtp.gmail.com",
            465,
            context=context
        ) as server:

            server.login(
                email_address,
                email_app_password
            )


            server.send_message(
                message
            )


        print(
            "SUCCESS: Email alert sent."
        )


    except Exception as error:

        print(
            "ERROR sending email:"
        )

        print(error)

        raise


else:

    print()
    print(
        "No deal found. No email sent."
    )


# ============================================================
# FILTER REPORT
# ============================================================

print()
print("=" * 72)
print("FILTER REPORT")
print("=" * 72)


for reason, count in sorted(
    rejection_reasons.items()
):

    print(
        f"{reason}: {count}"
    )


print()
print("=" * 72)
print("IMPORTANT")
print("=" * 72)

print(
    "1. Deal score uses delivered price."
)

print(
    "2. Deal score compares against the "
    "manual 30-day sold benchmark."
)

print(
    "3. The sold benchmark does not "
    "automatically refresh yet."
)

print(
    "4. No eBay price history is saved."
)

print(
    "5. Email is sent only when a deal "
    "is found, unless test mode is enabled."
)

print()
print(
    "Tracker completed successfully."
)
