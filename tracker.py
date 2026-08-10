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
# CONFIGURATION
# ============================================================

CARDS = [

    # ========================================================
    # 1. VAN GOGH PIKACHU
    # ========================================================
    {
        "card_id": "pikachu-grey-felt-hat-085-psa10",

        "name": "Pikachu with Grey Felt Hat #085 PSA 10",

        "search_terms": [
            "Pikachu Grey Felt Hat 085 PSA 10",
            "Pikachu Van Gogh 085 PSA 10",
            "Pikachu SVP085 PSA 10",
        ],

        "required_all": [
            "pikachu",
        ],

        "required_any": [
            "grey felt hat",
            "gray felt hat",
            "van gogh",
        ],

        "number_patterns": [
            r"\b0?85\b",
            r"\bsvp[\s\-]*0?85\b",
        ],

        "excluded_terms": [],

        # Manual sold benchmark
        "sold_median": 1918.63,
    },


    # ========================================================
    # 2. PIKACHU 120/SV-P
    # ========================================================
    {
        "card_id": "pikachu-120-sv-p-psa10",

        "name": "Pikachu 120/SV-P Gym Event Campaign PSA 10",

        "search_terms": [
            "Pikachu 120/SV-P PSA 10",
            "Pikachu 120 SV-P PSA 10",
            "Pikachu Gym Event 120/SV-P PSA 10",
        ],

        "required_all": [
            "pikachu",
        ],

        "required_any": [
            "120/sv-p",
            "120 sv-p",
            "gym event",
            "gym campaign",
        ],

        "number_patterns": [
            r"\b120[\s/\-]*sv[\s\-]*p\b",
        ],

        "excluded_terms": [],

        "sold_median": None,
    },


    # ========================================================
    # 3. SWALLOWED UP PIKACHU 105/S-P
    # ========================================================
    {
        "card_id": "swallowed-up-pikachu-105-s-p-psa10",

        "name": "Swallowed Up Pikachu 105/S-P PSA 10",

        "search_terms": [
            "Pikachu 105/S-P PSA 10",
            "Swallowed Up Pikachu 105/S-P PSA 10",
            "Pikachu 105 S-P PSA 10",
        ],

        "required_all": [
            "pikachu",
        ],

        "required_any": [
            "105/s-p",
            "105 s-p",
            "swallowed up",
        ],

        "number_patterns": [
            r"\b105[\s/\-]*s[\s\-]*p\b",
        ],

        "excluded_terms": [],

        "sold_median": None,
    },


    # ========================================================
    # 4. TERAPAGOS EX 170/142
    # ========================================================
    {
        "card_id": "terapagos-ex-170-142-psa10",

        "name": "Terapagos ex 170/142 Stellar Crown PSA 10 - English",

        "search_terms": [
            "Terapagos ex 170/142 PSA 10",
            "Terapagos 170/142 Stellar Crown PSA 10",
            "Terapagos ex SIR 170/142 PSA 10",
        ],

        "required_all": [
            "terapagos",
        ],

        "required_any": [
            "170/142",
            "170 142",
            "stellar crown",
            "special illustration",
            "sir",
        ],

        "number_patterns": [
            r"\b170[\s/\-]*142\b",
        ],

        "excluded_terms": [
            "japanese",
            "jpn",
            "jp psa",
        ],

        "sold_median": None,
    },


    # ========================================================
    # 5. MEOWTH EX 121/088
    # ========================================================
    {
        "card_id": "meowth-ex-121-088-psa10",

        "name": "Meowth ex 121/088 PSA 10",

        "search_terms": [
            "Meowth ex 121/088 PSA 10",
            "Meowth 121/088 PSA 10",
            "Meowth ex 121 088 PSA 10",
        ],

        "required_all": [
            "meowth",
        ],

        "required_any": [
            "121/088",
            "121/88",
            "121 088",
            "special illustration",
            "sir",
        ],

        "number_patterns": [
            r"\b121[\s/\-]*0?88\b",
        ],

        "excluded_terms": [],

        "sold_median": None,
    },


    # ========================================================
    # 6. SLOWPOKE & PSYDUCK GX 35/236
    # ========================================================
    {
        "card_id": "slowpoke-psyduck-gx-35-236-psa10",

        "name": "Slowpoke & Psyduck GX 35/236 PSA 10",

        "search_terms": [
            "Slowpoke Psyduck GX 35/236 PSA 10",
            "Slowpoke & Psyduck GX 35/236 PSA 10",
            "Slowpoke Psyduck Unified Minds 35/236 PSA 10",
        ],

        "required_all": [
            "slowpoke",
            "psyduck",
        ],

        "required_any": [
            "35/236",
            "35 236",
            "unified minds",
            "gx",
        ],

        "number_patterns": [
            r"\b35[\s/\-]*236\b",
        ],

        "excluded_terms": [
            "218/236",
            "218 236",
            "alt art",
            "alternate art",
        ],

        "sold_median": None,
    },


    # ========================================================
    # 7. CHARIZARD EX 199/165
    # ========================================================
    {
        "card_id": "charizard-ex-199-165-psa10",

        "name": "Charizard ex 199/165 Pokemon 151 PSA 10 - English",

        "search_terms": [
            "Charizard ex 199/165 PSA 10",
            "Charizard 199/165 Pokemon 151 PSA 10",
            "Charizard ex SIR 199/165 PSA 10",
        ],

        "required_all": [
            "charizard",
        ],

        "required_any": [
            "199/165",
            "199 165",
            "pokemon 151",
            "special illustration",
            "sir",
        ],

        "number_patterns": [
            r"\b199[\s/\-]*165\b",
        ],

        "excluded_terms": [
            "japanese",
            "jpn",
            "199/108",
            "199/197",
            "199/189",
        ],

        "sold_median": None,
    },


    # ========================================================
    # 8. LATIAS & LATIOS GX 170/181
    # ========================================================
    {
        "card_id": "latias-latios-gx-170-181-psa10",

        "name": "Latias & Latios GX 170/181 Team Up PSA 10",

        "search_terms": [
            "Latias Latios GX 170/181 PSA 10",
            "Latias & Latios GX 170/181 PSA 10",
            "Latias Latios Team Up 170/181 PSA 10",
            "Latias Latios Alt Art PSA 10 170/181",
        ],

        "required_all": [
            "latias",
            "latios",
        ],

        "required_any": [
            "170/181",
            "170 181",
            "team up",
            "alt art",
            "alternate art",
        ],

        "number_patterns": [
            r"\b170[\s/\-]*181\b",
        ],

        "excluded_terms": [
            "169/181",
            "169 181",
            "113/181",
            "113 181",
            "japanese",
            "jpn",
        ],

        "sold_median": None,
    },


    # ========================================================
    # 9. PIKACHU 227/S-P JAPAN POST
    # ========================================================
    {
        "card_id": "pikachu-227-s-p-stamp-box-psa10",

        "name": "Pikachu 227/S-P Japan Post Stamp Box PSA 10",

        "search_terms": [
            "Pikachu 227/S-P PSA 10",
            "Pikachu 227 S-P PSA 10",
            "Pikachu Stamp Box 227/S-P PSA 10",
            "Pikachu Japan Post 227/S-P PSA 10",
        ],

        "required_all": [
            "pikachu",
        ],

        "required_any": [
            "227/s-p",
            "227 s-p",
            "stamp box",
            "japan post",
        ],

        "number_patterns": [
            r"\b227[\s/\-]*s[\s\-]*p\b",
        ],

        "excluded_terms": [
            "cramorant",
            "226/s-p",
            "226 s-p",
            "box only",
        ],

        "sold_median": None,
    },


    # ========================================================
    # 10. MEGA CHARIZARD X EX 125/094
    # ========================================================
    {
        "card_id": "mega-charizard-x-ex-125-094-psa10",

        "name": "Mega Charizard X ex 125/094 PSA 10 - English",

        "search_terms": [
            "Mega Charizard X ex 125/094 PSA 10",
            "Mega Charizard 125/094 PSA 10",
            "Mega Charizard X ex SIR 125/094 PSA 10",
            "Mega Charizard X 125 094 PSA 10",
        ],

        "required_all": [
            "charizard",
        ],

        "required_any": [
            "125/094",
            "125/94",
            "125 094",
            "mega charizard x",
            "special illustration",
            "sir",
        ],

        "number_patterns": [
            r"\b125[\s/\-]*0?94\b",
        ],

        "excluded_terms": [
            "japanese",
            "jpn",
            "110/080",
            "110 080",
            "109/094",
            "109 094",
            "130/094",
            "130 094",
        ],

        "sold_median": None,
    },
]


# ============================================================
# DEAL SETTINGS
# ============================================================

WATCH_PERCENT = 10
GOOD_DEAL_PERCENT = 15
STRONG_DEAL_PERCENT = 20


# ============================================================
# READ GITHUB SECRETS
# ============================================================

# Prefer Production secrets.
# Falls back to the original names if necessary.

client_id = os.environ.get(
    "EBAY_PROD_CLIENT_ID"
) or os.environ.get(
    "EBAY_CLIENT_ID"
)

client_secret = os.environ.get(
    "EBAY_PROD_CLIENT_SECRET"
) or os.environ.get(
    "EBAY_CLIENT_SECRET"
)

if not client_id:
    raise RuntimeError(
        "Missing EBAY_PROD_CLIENT_ID / EBAY_CLIENT_ID"
    )

if not client_secret:
    raise RuntimeError(
        "Missing EBAY_PROD_CLIENT_SECRET / EBAY_CLIENT_SECRET"
    )


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
).replace(
    " ",
    ""
).strip()


# ============================================================
# EBAY AUTHENTICATION
# ============================================================

def get_access_token():

    credentials = (
        f"{client_id}:{client_secret}"
    )

    encoded_credentials = base64.b64encode(
        credentials.encode()
    ).decode()

    token_url = (
        "https://api.ebay.com/"
        "identity/v1/oauth2/token"
    )

    token_data = urllib.parse.urlencode({
        "grant_type":
            "client_credentials",

        "scope":
            "https://api.ebay.com/oauth/api_scope",
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
            token_request,
            timeout=30
        ) as response:

            token_result = json.loads(
                response.read().decode()
            )

        token = token_result.get(
            "access_token"
        )

        if not token:
            raise RuntimeError(
                "eBay did not return an access token."
            )

        print(
            "SUCCESS: Connected to eBay Production"
        )

        return token

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


access_token = get_access_token()


# ============================================================
# TEXT NORMALISATION
# ============================================================

def normalize(text):

    text = str(
        text or ""
    ).lower()

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
# PRICE HELPERS
# ============================================================

def get_item_price(item):

    try:

        return float(
            item["price"]["value"]
        )

    except (
        KeyError,
        ValueError,
        TypeError
    ):

        return None


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
            costs.append(
                cost
            )

    if not costs:
        return None

    return min(
        costs
    )


def get_delivered_price(item):

    item_price = get_item_price(
        item
    )

    shipping = get_shipping_cost(
        item
    )

    if item_price is None:
        return None

    # Some eBay listings may not return a shipping amount.
    # We do not assume that unknown shipping is free.
    if shipping is None:
        return None

    return (
        item_price
        + shipping
    )


# ============================================================
# CARD MATCHING
# ============================================================

def is_target_card(item, card):

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
    # PSA 10 REQUIRED
    # --------------------------------------------------------

    if not re.search(
        r"\bpsa[\s\-]*10\b",
        title
    ):

        return (
            False,
            "not_psa10"
        )

    # --------------------------------------------------------
    # REQUIRED WORDS
    # --------------------------------------------------------

    for term in card.get(
        "required_all",
        []
    ):

        if normalize(
            term
        ) not in title:

            return (
                False,
                "missing_required_term"
            )

    # --------------------------------------------------------
    # CARD NUMBER
    # --------------------------------------------------------

    number_patterns = card.get(
        "number_patterns",
        []
    )

    if number_patterns:

        if not any(
            re.search(
                pattern,
                title
            )
            for pattern in number_patterns
        ):

            return (
                False,
                "wrong_card_number"
            )

    # --------------------------------------------------------
    # IDENTITY TERMS
    # --------------------------------------------------------

    required_any = card.get(
        "required_any",
        []
    )

    if required_any:

        if not any(
            normalize(term) in title
            for term in required_any
        ):

            return (
                False,
                "wrong_card_identity"
            )

    # --------------------------------------------------------
    # OTHER GRADERS
    # --------------------------------------------------------

    other_graders = [
        "ace 10",
        "ace grading",
        "cgc 10",
        "cgc pristine",
        "cgc gem",
        "bgs",
        "beckett",
        "sgc",
        "tag 10",
    ]

    if any(
        grader in title
        for grader in other_graders
    ):

        return (
            False,
            "other_grader"
        )

    # --------------------------------------------------------
    # GENERIC EXCLUSIONS
    # --------------------------------------------------------

    generic_exclusions = [
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
        "bundle",
        "lot of",
        "set of 2",
        "set of 3",
        "2 cards",
        "3 cards",
        "pair of",
        "signed",
        "signature",
        "autograph",
    ]

    if any(
        term in title
        for term in generic_exclusions
    ):

        return (
            False,
            "excluded_product"
        )

    # --------------------------------------------------------
    # CARD-SPECIFIC EXCLUSIONS
    # --------------------------------------------------------

    if any(
        normalize(term) in title
        for term in card.get(
            "excluded_terms",
            []
        )
    ):

        return (
            False,
            "wrong_variant"
        )

    # --------------------------------------------------------
    # GRADED CONDITION
    # --------------------------------------------------------

    if (
        condition
        and "graded" not in condition
    ):

        return (
            False,
            "not_graded_condition"
        )

    # --------------------------------------------------------
    # FIXED PRICE ONLY
    # --------------------------------------------------------

    buying_options = item.get(
        "buyingOptions",
        []
    )

    if (
        buying_options
        and "FIXED_PRICE" not in buying_options
    ):

        return (
            False,
            "not_fixed_price"
        )

    # --------------------------------------------------------
    # GBP PRICE REQUIRED
    # --------------------------------------------------------

    price_data = item.get(
        "price",
        {}
    )

    if price_data.get(
        "currency"
    ) != "GBP":

        return (
            False,
            "not_gbp"
        )

    item_price = get_item_price(
        item
    )

    if (
        item_price is None
        or item_price <= 0
    ):

        return (
            False,
            "invalid_price"
        )

    return (
        True,
        "accepted"
    )


# ============================================================
# SEARCH ONE CARD
# ============================================================

def search_card(card):

    all_items = {}

    print()
    print(
        "=" * 72
    )
    print(
        card["name"]
    )
    print(
        "=" * 72
    )

    # --------------------------------------------------------
    # MULTIPLE SEARCH TERMS
    # --------------------------------------------------------

    for search_term in card[
        "search_terms"
    ]:

        print(
            f"Searching: {search_term}"
        )

        params = {
            "q":
                search_term,

            "limit":
                "50",

            "filter":
                "deliveryCountry:GB",
        }

        query_string = urllib.parse.urlencode(
            params
        )

        search_url = (
            "https://api.ebay.com/"
            "buy/browse/v1/item_summary/search?"
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

        # ----------------------------------------------------
        # BUYER LOCATION FOR SHIPPING
        # ----------------------------------------------------

        if buyer_postcode:

            contextual_location = urllib.parse.quote(
                (
                    "country=GB,"
                    f"zip={buyer_postcode}"
                ),
                safe=""
            )

            request.add_header(
                "X-EBAY-C-ENDUSERCTX",
                (
                    "contextualLocation="
                    f"{contextual_location}"
                )
            )

        # ----------------------------------------------------
        # API REQUEST
        # ----------------------------------------------------

        try:

            with urllib.request.urlopen(
                request,
                timeout=30
            ) as response:

                api_result = json.loads(
                    response.read().decode()
                )

            search_items = api_result.get(
                "itemSummaries",
                []
            )

            print(
                f"Raw results: {len(search_items)}"
            )

            # Deduplicate item IDs
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

    # ========================================================
    # MATCH LISTINGS
    # ========================================================

    matched_items = []

    rejection_reasons = Counter()

    for item in all_items.values():

        matched, reason = is_target_card(
            item,
            card
        )

        if matched:

            matched_items.append(
                item
            )

        else:

            rejection_reasons[
                reason
            ] += 1

    # ========================================================
    # DELIVERED PRICES
    # ========================================================

    delivered_items = []

    unknown_shipping_items = []

    for item in matched_items:

        delivered_price = get_delivered_price(
            item
        )

        if delivered_price is None:

            unknown_shipping_items.append(
                item
            )

        else:

            delivered_items.append({
                "item":
                    item,

                "delivered_price":
                    delivered_price,
            })

    delivered_items.sort(
        key=lambda row:
            row["delivered_price"]
    )

    delivered_prices = [
        row["delivered_price"]
        for row in delivered_items
    ]

    # ========================================================
    # METRICS
    # ========================================================

    if delivered_prices:

        lowest = min(
            delivered_prices
        )

        median = statistics.median(
            delivered_prices
        )

        average = statistics.mean(
            delivered_prices
        )

    else:

        lowest = None
        median = None
        average = None

    # ========================================================
    # DEAL ANALYSIS
    # ========================================================

    deal_candidates = []

    sold_median = card.get(
        "sold_median"
    )

    if sold_median:

        for row in delivered_items:

            delivered_price = row[
                "delivered_price"
            ]

            discount = (
                (
                    sold_median
                    - delivered_price
                )
                / sold_median
            ) * 100

            if discount >= WATCH_PERCENT:

                if discount >= STRONG_DEAL_PERCENT:

                    level = "STRONG DEAL"

                elif discount >= GOOD_DEAL_PERCENT:

                    level = "GOOD DEAL"

                else:

                    level = "WATCH"

                deal_candidates.append({
                    "level":
                        level,

                    "discount":
                        discount,

                    "delivered_price":
                        delivered_price,

                    "item":
                        row["item"],
                })

    return {
        "card":
            card,

        "raw_count":
            len(all_items),

        "matched_count":
            len(matched_items),

        "shipping_count":
            len(delivered_items),

        "unknown_shipping_count":
            len(unknown_shipping_items),

        "lowest":
            lowest,

        "median":
            median,

        "average":
            average,

        "delivered_items":
            delivered_items,

        "deal_candidates":
            deal_candidates,

        "rejection_reasons":
            rejection_reasons,
    }


# ============================================================
# RUN ALL CARDS
# ============================================================

results = []

for card in CARDS:

    try:

        result = search_card(
            card
        )

        results.append(
            result
        )

    except Exception as error:

        print()
        print(
            f"ERROR tracking {card['name']}:"
        )
        print(
            error
        )

        # Keep the daily report running even if one card fails.
        results.append({
            "card":
                card,

            "raw_count":
                0,

            "matched_count":
                0,

            "shipping_count":
                0,

            "unknown_shipping_count":
                0,

            "lowest":
                None,

            "median":
                None,

            "average":
                None,

            "delivered_items":
                [],

            "deal_candidates":
                [],

            "rejection_reasons":
                Counter(),

            "error":
                str(error),
        })


# ============================================================
# CONSOLE SUMMARY
# ============================================================

print()
print(
    "=" * 72
)
print(
    "POKEMON PSA 10 DAILY MARKET REPORT"
)
print(
    "=" * 72
)

for index, result in enumerate(
    results,
    start=1
):

    card = result[
        "card"
    ]

    print()

    print(
        f"{index}. {card['name']}"
    )

    if result.get(
        "error"
    ):

        print(
            f"STATUS: ERROR - {result['error']}"
        )

        continue

    print(
        f"Exact listings: "
        f"{result['matched_count']}"
    )

    print(
        f"Listings with delivered price: "
        f"{result['shipping_count']}"
    )

    if result["median"] is not None:

        print(
            f"Lowest delivered: "
            f"£{result['lowest']:,.2f}"
        )

        print(
            f"Median delivered: "
            f"£{result['median']:,.2f}"
        )

        print(
            f"Average delivered: "
            f"£{result['average']:,.2f}"
        )

    else:

        print(
            "No listings with usable "
            "shipping data."
        )

    sold_median = card.get(
        "sold_median"
    )

    if sold_median:

        print(
            f"Sold benchmark: "
            f"£{sold_median:,.2f}"
        )

        if result["lowest"] is not None:

            difference = (
                (
                    result["lowest"]
                    - sold_median
                )
                / sold_median
            ) * 100

            print(
                "Lowest vs sold benchmark: "
                f"{difference:+.1f}%"
            )

    if result["deal_candidates"]:

        best = min(
            result["deal_candidates"],
            key=lambda item:
                item["delivered_price"]
        )

        print(
            f"STATUS: {best['level']}"
        )

    elif sold_median:

        print(
            "STATUS: NORMAL"
        )

    else:

        print(
            "STATUS: LIVE TRACKING"
        )


# ============================================================
# EMAIL REPORT
# ============================================================

def build_email_body():

    lines = []

    report_date = datetime.now(
        timezone.utc
    ).strftime(
        "%d %b %Y"
    )

    lines.append(
        "Pokemon PSA 10 Daily Market Report"
    )

    lines.append(
        f"Date: {report_date}"
    )

    lines.append(
        "=" * 60
    )

    lines.append("")

    for index, result in enumerate(
        results,
        start=1
    ):

        card = result[
            "card"
        ]

        lines.append(
            f"{index}. {card['name']}"
        )

        lines.append(
            "-" * 60
        )

        # ----------------------------------------------------
        # ERROR
        # ----------------------------------------------------

        if result.get(
            "error"
        ):

            lines.append(
                "TRACKING ERROR"
            )

            lines.append(
                result["error"]
            )

            lines.append("")
            lines.append("")

            continue

        # ----------------------------------------------------
        # LISTING COUNTS
        # ----------------------------------------------------

        lines.append(
            f"Exact listings: "
            f"{result['matched_count']}"
        )

        lines.append(
            f"Listings with delivered price: "
            f"{result['shipping_count']}"
        )

        if result[
            "unknown_shipping_count"
        ]:

            lines.append(
                f"Listings with unknown shipping: "
                f"{result['unknown_shipping_count']}"
            )

        # ----------------------------------------------------
        # LIVE MARKET
        # ----------------------------------------------------

        if (
            result["median"] is not None
            and result["delivered_items"]
        ):

            lines.append(
                f"Lowest delivered: "
                f"£{result['lowest']:,.2f}"
            )

            lines.append(
                f"Median delivered: "
                f"£{result['median']:,.2f}"
            )

            lines.append(
                f"Average delivered: "
                f"£{result['average']:,.2f}"
            )

            cheapest = result[
                "delivered_items"
            ][0]

            cheapest_item = cheapest[
                "item"
            ]

            item_price = get_item_price(
                cheapest_item
            )

            shipping = get_shipping_cost(
                cheapest_item
            )

            lines.append("")
            lines.append(
                "CHEAPEST LISTING"
            )

            if item_price is not None:

                lines.append(
                    f"Item price: "
                    f"£{item_price:,.2f}"
                )

            if shipping is not None:

                lines.append(
                    f"Shipping: "
                    f"£{shipping:,.2f}"
                )

            lines.append(
                f"Delivered: "
                f"£{cheapest['delivered_price']:,.2f}"
            )

            lines.append(
                f"Title: "
                f"{cheapest_item.get('title', '')}"
            )

            lines.append(
                f"URL: "
                f"{cheapest_item.get('itemWebUrl', '')}"
            )

        else:

            lines.append(
                "No usable live listings "
                "with shipping data today."
            )

        # ----------------------------------------------------
        # SOLD BENCHMARK
        # ----------------------------------------------------

        sold_median = card.get(
            "sold_median"
        )

        if sold_median is not None:

            lines.append("")

            lines.append(
                f"30-day sold benchmark: "
                f"£{sold_median:,.2f}"
            )

            if result["lowest"] is not None:

                difference = (
                    (
                        result["lowest"]
                        - sold_median
                    )
                    / sold_median
                ) * 100

                lines.append(
                    "Lowest live price vs "
                    f"sold benchmark: "
                    f"{difference:+.1f}%"
                )

            if result["deal_candidates"]:

                best = min(
                    result["deal_candidates"],
                    key=lambda row:
                        row["delivered_price"]
                )

                lines.append(
                    f"Deal status: "
                    f"{best['level']}"
                )

                lines.append(
                    f"Discount vs sold benchmark: "
                    f"{best['discount']:.1f}%"
                )

            else:

                lines.append(
                    "Deal status: NORMAL"
                )

        else:

            lines.append(
                "Status: LIVE PRICE TRACKING"
            )

        # ----------------------------------------------------
        # TOP 5 CHEAPEST LISTINGS
        # ----------------------------------------------------

        if result["delivered_items"]:

            lines.append("")
            lines.append(
                "TOP 5 CHEAPEST"
            )
            lines.append(
                "-" * 30
            )

            for position, row in enumerate(
                result["delivered_items"][:5],
                start=1
            ):

                item = row[
                    "item"
                ]

                lines.append(
                    f"{position}. "
                    f"£{row['delivered_price']:,.2f}"
                )

                lines.append(
                    item.get(
                        "title",
                        ""
                    )
                )

                lines.append(
                    item.get(
                        "itemWebUrl",
                        ""
                    )
                )

                lines.append("")

        lines.append("")
        lines.append("")

    # ========================================================
    # FOOTER
    # ========================================================

    lines.append(
        "=" * 60
    )

    lines.append(
        "NOTES"
    )

    lines.append(
        "=" * 60
    )

    lines.append(
        "Live prices are current eBay UK asking prices."
    )

    lines.append(
        "Delivered price = item price + available "
        "eBay shipping estimate."
    )

    lines.append(
        "Only listings matching the configured PSA 10 "
        "card filters are included."
    )

    lines.append(
        "The Van Gogh Pikachu sold benchmark is "
        "manually configured and does not "
        "automatically refresh."
    )

    lines.append("")

    lines.append(
        "This report is sent every day even when "
        "there are no deal alerts."
    )

    return "\n".join(
        lines
    )


# ============================================================
# SEND DAILY EMAIL
# ============================================================

def send_email():

    if not email_address:

        print(
            "EMAIL NOT SENT: "
            "EMAIL_ADDRESS secret is missing."
        )

        return

    if not email_app_password:

        print(
            "EMAIL NOT SENT: "
            "EMAIL_APP_PASSWORD secret is missing."
        )

        return

    body = build_email_body()

    # --------------------------------------------------------
    # EMAIL SUBJECT
    # --------------------------------------------------------

    deal_count = sum(
        len(
            result.get(
                "deal_candidates",
                []
            )
        )
        for result in results
    )

    report_date = datetime.now(
        timezone.utc
    ).strftime(
        "%d %b"
    )

    if deal_count > 0:

        subject = (
            f"Pokemon PSA 10 Daily Report "
            f"- {deal_count} Deal Alert"
        )

        if deal_count != 1:
            subject += "s"

        subject += (
            f" - {report_date}"
        )

    else:

        subject = (
            "Pokemon PSA 10 Daily Market Report "
            f"- {report_date}"
        )

    # --------------------------------------------------------
    # CREATE EMAIL
    # --------------------------------------------------------

    message = EmailMessage()

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
        body
    )

    # --------------------------------------------------------
    # SEND USING GMAIL SMTP
    # --------------------------------------------------------

    context = ssl.create_default_context()

    try:

        with smtplib.SMTP_SSL(
            "smtp.gmail.com",
            465,
            context=context
        ) as smtp:

            smtp.login(
                email_address,
                email_app_password
            )

            smtp.send_message(
                message
            )

        print()
        print(
            "=" * 72
        )

        print(
            "SUCCESS: Daily email report sent"
        )

        print(
            f"Email sent to: {email_address}"
        )

        print(
            "=" * 72
        )

    except smtplib.SMTPAuthenticationError:

        print()
        print(
            "ERROR: Gmail authentication failed."
        )

        print(
            "Check EMAIL_ADDRESS and "
            "EMAIL_APP_PASSWORD."
        )

        raise

    except Exception as error:

        print()
        print(
            "ERROR sending email:"
        )

        print(
            error
        )

        raise


# ============================================================
# SEND REPORT EVERY RUN
# ============================================================

send_email()


# ============================================================
# COMPLETE
# ============================================================

print()
print(
    "=" * 72
)

print(
    "Tracker completed successfully."
)

print(
    f"Cards tracked: {len(CARDS)}"
)

print(
    "=" * 72
)
