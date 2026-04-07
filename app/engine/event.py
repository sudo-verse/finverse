import re

def clean_text(text: str) -> str:
    text = text.lower()
    text = re.sub(r"\s+", " ", text)
    return text.strip()


CATEGORY_PATTERNS = [

    # 🔴 High priority (critical events first)
    ("insolvency", [
        r"\bcirp\b",
        r"\binsolvenc",
        r"\bibc\b",
        r"\bnclt\b",
        r"\bresolution professional\b",
    ]),

    ("fraud_default", [
        r"\bfraud\b",
        r"\bdefault\b",
        r"\bnp[ab]\b",
        r"\barrest\b",
        r"\bforensic audit\b",
        r"\bwilful defaulter\b",
    ]),

    ("order_win", [
        r"\bbag(g|ged)?.*\b(order|contract|project|work order)s?\b",
        r"\bsecure(d)?.*\b(order|contract|project|work order)s?\b",
        r"\bwon\b.*\b(order|contract|project|work order)s?\b",
        r"\breceiv(ed|e)\b.*\b(order|contract|work order)s?\b",
        r"\b(work order|purchase order|letter of award|loa)s?\b",
    ]),

    ("securities_issuance", [
        r"\ballot",
        r"\bissu(e|ance)\b.*\bsecurit",
        r"\bpreferential\b",
        r"\brights?\b",
        r"\bqip\b",
        r"\bwarrants?\b",
        r"\bconvertible\b",
        r"\bbonus\b",
        r"\bstock split\b",
        r"\bequity shares?\b.*\ballot",
    ]),

    ("management_change", [
        r"\bappoint(ed|ment)?\b.*\b(director|ceo|cfo|kmp|auditor)\b",
        r"\bresign(ed|ation)?\b.*\b(director|ceo|cfo|kmp|auditor)\b",
        r"\bcessation\b",
        r"\bchange in director",
        r"\bauditor\b",
        r"\bkmp\b",
    ]),

    ("dividend", [
        r"\bdividend\b",
        r"\binterim dividend\b",
        r"\bfinal dividend\b",
    ]),

    ("earnings", [
        r"\bfinancial results?\b",
        r"\bquarter(ly)? results?\b",
        r"\bq[1-4]\b",
        r"\bearnings\b",
        r"\bresults?\b",
    ]),

    ("board_outcome", [
        r"\boutcome of board meeting\b",
        r"\bboard meeting outcome\b",
    ]),

    ("shareholder_meeting", [
        r"\bagm\b",
        r"\begm\b",
        r"\bpostal ballot\b",
        r"\bshareholder",
    ]),

    ("agreement_mou", [
        r"\bmou\b",
        r"\bmemorandum of understanding\b",
        r"\bstrategic agreement\b",
        r"\bdefinitive agreement\b",
        r"\bagreement\b",
    ]),

    ("restructuring", [
        r"\brestructur",
        r"\bcdr\b",
        r"\bdebt restructur",
        r"\bscheme of arrangement\b",
    ]),

    ("settlement", [
        r"\bone[\s-]?time settlement\b",
        r"\bots\b",
        r"\bsettlement\b",
        r"\binter[-\s]?creditor",
    ]),
]


def classify_event(text: str) -> str:
    if not isinstance(text, str) or not text.strip():
        return "other"

    text = clean_text(text)

    for category, patterns in CATEGORY_PATTERNS:
        for pattern in patterns:
            if re.search(pattern, text):
                return category

    return "other"
def detect_event(desc, attchmntxt):
    parts = []

    if isinstance(desc, str):
        parts.append(desc)

    if isinstance(attchmntxt, str):
        parts.append(attchmntxt)

    text = " ".join(parts)

    return classify_event(text)