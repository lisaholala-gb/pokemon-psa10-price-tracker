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
    {
        "card_id": "pikachu-grey-felt-hat-085-psa10",
        "name": "Pikachu with Grey Felt Hat #085 PSA 10",
        "search_terms": [
            "Pikachu Grey Felt Hat 085 PSA 10",
            "Pikachu Van Gogh 085 PSA 10",
        ],
        "required_any": [
            "grey felt hat",
            "gray felt hat",
            "van gogh",
        ],
        "number_patterns": [
            r"\b085\b",
            r"\b85\b",
            r"\bsvp[\s\-]*085\b",
            r"\bsvp[\s\-]*85\b",
        ],
        "required_all": [
            "pikachu",
        ],
        "excluded_terms": [],
        "sold_median": 1918.63,
    },

    {
        "card_id": "pikachu-120-sv-p-psa10",
        "name": "Pikachu 120/SV-P Gym Event Campaign PSA 10",
        "search_terms": [
            "Pikachu 120/SV-P PSA 10",
            "Pikachu 120 SV-P PSA 10",
            "Pikachu Gym Event Campaign 120/SV-P PSA 10",
        ],
        "required_any": [
            "gym event",
            "sv-p",
            "svp",
        ],
        "number_patterns": [
            r"\b120[\s/\-]*sv[\s\-]*p\b",
            r"\b120sv[\s\-]*p\b",
        ],
        "required_all": [
            "pikachu",
        ],
        "excluded_terms": [],
        "sold_median": None,
    },

    {
        "card_id": "swallowed-up-pikachu-105-s-p-psa10",
        "name": "Swallowed Up Pikachu 105/S-P PSA 10",
        "search_terms": [
            "Pikachu 105/S-P PSA 10",
            "Swallowed Up Pikachu 105/S-P PSA 10",
            "Pikachu 105 S-P Koko PSA 10",
        ],
        "required_any": [
            "swallowed up",
            "105/s-p",
            "105 s-p",
            "koko",
            "m23",
        ],
        "number_patterns": [
            r"\b105[\s/\-]*s[\s\-]*p\b",
        ],
        "required_all": [
            "pikachu",
        ],
        "excluded_terms": [],
        "sold_median": None,
    },

    {
        "card_id": "terapagos-ex-170-142-psa10",
        "name": "Terapagos ex 170/142 Stellar Crown PSA 10",
        "search_terms": [
            "Terapagos ex 170/142 PSA 10",
            "Terapagos 170/142 Stellar Crown PSA 10",
            "Terapagos ex SIR 170/142 PSA 10",
        ],
        "required_any": [
            "stellar crown",
            "sir",
            "special illustration",
            "170/142",
        ],
        "number_patterns": [
            r"\b170[\s/\-]*142\b",
        ],
        "required_all": [
            "terapagos",
        ],
        "excluded_terms": [
            "japanese",
            "jp",
        ],
        "sold_median": None,
    },

    {
        "card_id": "meowth-ex-121-088-psa10",
        "name": "Meowth ex 121/088 Perfect Order PSA 10",
        "search_terms": [
            "Meowth ex 121/088 PSA 10",
            "Meowth 121/088 Perfect Order PSA 10",
            "Meowth ex SIR 121/088 PSA 10",
        ],
        "required_any": [
            "perfect order",
            "sir",
            "special illustration",
            "121/088",
        ],
        "number_patterns": [
            r"\b121[\s/\-]*088\b",
            r"\b121[\s/\-]*88\b",
        ],
        "required_all": [
            "meowth",
        ],
        "excluded_terms": [
            "japanese",
            "jp",
        ],
        "sold_median": None,
    },

    {
        "card_id": "slowpoke-psyduck-gx-35-236-psa10",
        "name": "Slowpoke & Psyduck GX 35/236 PSA 10",
        "search_terms": [
            "Slowpoke Psyduck GX 35/236 PSA 10",
            "Slowpoke & Psyduck GX 35/236 PSA 10",
            "Slowpoke Psyduck Unified Minds 35/236 PSA 10",
        ],
        "required_any": [
            "unified minds",
            "35/236",
            "gx",
        ],
        "number_patterns": [
            r"\b35[\s/\-]*236\b",
        ],
        "required_all": [
            "slowpoke",
            "psyduck",
        ],
        "excluded_terms": [
            "218/236",
            "218 236",
            "alternate art",
            "alt art",
            "japanese",
        ],
        "sold_median": None,
    },
]


WATCH_PERCENT = 10
GOOD_DEAL_PERCENT = 15
STRONG_DEAL_PERCENT = 20


# ============================================================
# GITHUB SECRETS
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


# ============================================================
# EBAY AUTHENTICATION
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

    access_token = token_result["access_token"]

    print("SUCCESS: Connected to eBay Production")

except urllib.error.HTTPError as error:

    print("ERROR getting eBay access token")
    print("HTTP status:", error.code)
    print(error.read().decode())
    raise


# ============================================================
# HELPERS
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

        if (
            value is None
            or currency != "GBP"
        ):
            continue

        try:
            cost = float(value)

        except (
            ValueError,
            TypeError
        ):
            continue

        if cost >= 0:
            costs.append(cost)

    if not costs:
        return None

    return min(costs)


def get_delivered_price(item):

    item_price = get_item_price(
        item
    )

    shipping = get_shipping_cost(
        item
    )

    if (
        item_price is None
        or shipping is None
    ):
        return None

    return (
        item_price
        + shipping
    )


# ============================================================
# CARD MATCHING
# ============================================================

def is_target_card(
    item,
    card
):

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


    # Must explicitly be PSA 10
    if not re.search(
        r"\bpsa[\s\-]*10\b",
        title
    ):
        return False, "not_psa10"


    # Required words
    for term in card[
        "required_all"
    ]:

        if normalize(term) not in title:
            return False, "missing_required_term"


    # Correct card number
    if not any(
        re.search(
            pattern,
            title
        )
        for pattern
        in card[
            "number_patterns"
        ]
    ):
        return False, "wrong_card_number"


    # At least one identity hint
    required_any = card.get(
        "required_any",
        []
    )

    if required_any:

        if not any(
            normalize(term) in title
            for term
            in required_any
        ):
            return False, "wrong_card_identity"


    # Other graders
    other_graders = [
        "ace 10",
        "ace grading",
        "cgc 10",
        "cgc pristine",
        "bgs",
        "beckett",
        "sgc",
        "tag 10",
    ]

    if any(
        grader in title
        for grader
        in other_graders
    ):
        return False, "other_grader"


    # Generic bad products
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
        for term
        in generic_exclusions
    ):
        return False, "excluded_product"


    # Card-specific exclusions
    if any(
        normalize(term) in title
        for term
        in card.get(
            "excluded_terms",
            []
        )
    ):
        return False, "wrong_variant"


    # Graded condition
    if (
        condition
        and "graded" not in condition
    ):
        return False, "not_graded_condition"


    # Fixed-price only
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


    # GBP price
    price_data = item.get(
        "price",
        {}
    )

    if (
        price_data.get("currency")
        != "GBP"
    ):
        return False, "not_gbp"


    item_price = get_item_price(
        item
    )

    if (
        item_price is None
        or item_price <= 0
    ):
        return False, "invalid_price"


    return True, "accepted"


# ============================================================
# SEARCH ONE CARD
# ============================================================

def search_card(card):

    all_items = {}

    print()
    print("=" * 72)
    print(card["name"])
    print("=" * 72)


    for search_term in card[
        "search_terms"
    ]:

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

        request = (
            urllib.request.Request(
                search_url,
                method="GET"
            )
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
                f"Raw results: "
                f"{len(search_items)}"
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


    # --------------------------------------------------------
    # MATCH
    # --------------------------------------------------------

    matched_items = []

    rejection_reasons = Counter()


    for item in all_items.values():

        matched, reason = (
            is_target_card(
                item,
                card
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


    # --------------------------------------------------------
    # SHIPPING
    # --------------------------------------------------------

    delivered_items = []

    unknown_shipping_items = []


    for item in matched_items:

        delivered_price = (
            get_delivered_price(
                item
            )
        )

        if delivered_price is None:

            unknown_shipping_items.append(
                item
            )

        else:

            delivered_items.append(
                {
                    "item": item,
                    "delivered_price": delivered_price,
                }
            )


    delivered_items.sort(
        key=lambda x:
        x["delivered_price"]
    )


    delivered_prices = [
        row["delivered_price"]
        for row
        in delivered_items
    ]


    # --------------------------------------------------------
    # MARKET METRICS
    # --------------------------------------------------------

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


    # --------------------------------------------------------
    # DEAL STATUS
    # --------------------------------------------------------

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


            if (
                discount
                >= WATCH_PERCENT
            ):

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


                deal_candidates.append({
                    "level": level,
                    "discount": discount,
                    "delivered_price": delivered_price,
                    "item": row["item"],
                })


    return {
        "card": card,
        "raw_count": len(
            all_items
        ),
        "matched_count": len(
            matched_items
        ),
        "shipping_count": len(
            delivered_items
        ),
        "unknown_shipping_count": len(
            unknown_shipping_items
        ),
        "lowest": lowest,
        "median": median,
        "average": average,
        "delivered_items": delivered_items,
        "deal_candidates": deal_candidates,
        "rejection_reasons": rejection_reasons,
    }


# ============================================================
# RUN ALL CARDS
# ============================================================

results = []

for card in CARDS:

    result = search_card(
        card
    )

    results.append(
        result
    )


# ============================================================
# CONSOLE REPORT
# ============================================================

print()
print("=" * 72)
print("DAILY MULTI-CARD MARKET REPORT")
print("=" * 72)


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

    print(
        f"Exact listings: "
        f"{result['matched_count']}"
    )


    if result[
        "median"
    ] is not None:

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


        if (
            result["lowest"]
            is not None
        ):

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


    if result[
        "deal_candidates"
    ]:

        best = min(
            result[
                "deal_candidates"
            ],
            key=lambda x:
            x["delivered_price"]
        )

        print(
            f"Status: "
            f"{best['level']}"
        )

    else:

        if sold_median:

            print(
                "Status: NORMAL"
            )

        else:

            print(
                "Status: LIVE TRACKING ONLY"
            )


# ============================================================
# BUILD DAILY EMAIL
# ============================================================

def build_email_body():

    lines = []

    lines.append(
        "Pokemon PSA 10 Daily Market Report"
    )

    lines.append(
        "=" * 55
    )

    lines.append(
        ""
    )


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
            "-" * 55
        )

        lines.append(
            f"Exact listings: "
            f"{result['matched_count']}"
        )


        if (
            result["median"]
            is not None
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


            cheapest = (
                result[
                    "delivered_items"
                ][0]
            )

            cheapest_item = (
                cheapest["item"]
            )

            lines.append(
                ""
            )

            lines.append(
                "Cheapest current listing:"
            )

            lines.append(
                f"£{cheapest['delivered_price']:,.2f}"
            )

            lines.append(
                cheapest_item.get(
                    "title",
                    ""
                )
            )

            lines.append(
                cheapest_item.get(
                    "itemWebUrl",
                    ""
                )
            )

        else:

            lines.append(
                "No usable live listings."
            )


        sold_median = card.get(
            "sold_median"
        )


        if sold_median:

            lines.append(
                ""
            )

            lines.append(
                f"30-day sold benchmark: "
                f"£{sold_median:,.2f}"
            )


            if (
                result["lowest"]
                is not None
            ):

                difference = (
                    (
                        result["lowest"]
                        - sold_median
                    )
                    / sold_median
                ) * 100

                lines.append(
                    "Lowest vs sold benchmark: "
                    f"{difference:+.1f}%"
                )


            if (
                result[
                    "deal_candidates"
                ]
            ):

                lines.append(
                    ""
                )

                lines.append(
                    "DEALS"
                )


                for deal in result[
                    "deal_candidates"
                ]:

                    item = deal[
                        "item"
                    ]

                    lines.append(
                        f"{deal['level']} | "
                        f"£{deal['delivered_price']:,.2f} | "
                        f"{deal['discount']:.1f}% "
                        "below sold benchmark"
                    )

                    lines.append(
                        item.get(
                            "itemWebUrl",
                            ""
                        )
                    )


        else:

            lines.append(
                "Tracking mode: "
                "live asking prices only"
            )


        lines.append(
            ""
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

    lines.append(
        ""
    )

    lines.append(
        "Note: only Van Gogh Pikachu "
        "currently uses a sold-price benchmark."
    )


    return "\n".join(
        lines
    )


# ============================================================
# SEND DAILY EMAIL
# ============================================================

print()
print("=" * 72)
print("EMAIL")
print("=" * 72)


if (
    not email_address
    or not email_app_password
):

    raise RuntimeError(
        "EMAIL_ADDRESS or "
        "EMAIL_APP_PASSWORD is missing"
    )


message = EmailMessage()

message[
    "Subject"
] = (
    "Pokemon PSA 10 Daily Market Report"
)

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
        "SUCCESS: Daily email sent."
    )

except Exception as error:

    print(
        "ERROR sending email:"
    )

    print(error)

    raise


print()
print(
    "Tracker completed successfully."
)
