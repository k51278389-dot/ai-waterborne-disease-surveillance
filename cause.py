# ============================================================
# CAUSE DETECTION ENGINE
# ============================================================
#
# This file detects possible outbreak causes using:
# - user descriptions
# - environmental keywords
#
# Example input:
# "dirty water near drainage"
#
# Example output:
# "waterborne"
#
# Used for:
# - RAG filtering
# - medical protocol prioritization
# - outbreak reasoning
# ============================================================


# ============================================================
# CAUSE KEYWORD DATABASE
# ============================================================
#
# Each category contains environmental/contextual keywords
# associated with a disease transmission pattern.
# ============================================================

CAUSE_KEYWORDS = {

    # ========================================================
    # WATERBORNE CONDITIONS
    # ========================================================

    "waterborne": [

        "dirty water",
        "contaminated",
        "smell",
        "foul",
        "sewage",
        "drain",
        "plastic",
        "garbage",
        "waste",
        "polluted",
        "unsafe water",
        "drinking water",
        "pipeline leak",
        "water supply",
        "open defecation",
        "toilet overflow",
        "muddy water",
        "unclean water"
    ],

    # ========================================================
    # VECTORBORNE CONDITIONS
    # ========================================================

    "vectorborne": [

        "mosquito",
        "breeding",
        "stagnant",
        "water logging",
        "standing water",
        "pond",
        "ditch",
        "drain water",
        "rain water",
        "wet area",
        "swamp",
        "insects",
        "flies",
        "bugs",
        "open water"
    ],

    # ========================================================
    # GENERAL CONDITIONS
    # ========================================================

    "general": [

        "dirty",
        "hygiene",
        "unclean",
        "crowded",
        "overcrowded",
        "poor sanitation",
        "infection",
        "fever spreading",
        "seasonal",
        "weather",
        "cold",
        "flu spread",
        "touch",
        "contact",
        "air",
        "cough"
    ]
}


# ============================================================
# DETECT CAUSE TYPE
# ============================================================
#
# Uses keyword matching to identify the most likely
# environmental cause category.
#
# Output:
# - waterborne
# - vectorborne
# - general
# - unknown
# ============================================================

def detect_cause_type(text):

    # Normalize input text
    text = text.lower()

    # Score tracker for each category
    scores = {
        "waterborne": 0,
        "vectorborne": 0,
        "general": 0
    }

    # ========================================================
    # KEYWORD MATCHING
    # ========================================================
    # Count how many keywords from each category
    # appear inside the user text.
    # ========================================================

    for cause_type, keywords in CAUSE_KEYWORDS.items():

        for keyword in keywords:

            if keyword in text:
                scores[cause_type] += 1

    # ========================================================
    # FIND BEST MATCH
    # ========================================================

    best_match = max(scores, key=scores.get)

    # No keywords detected
    if scores[best_match] == 0:
        return "unknown"

    return best_match