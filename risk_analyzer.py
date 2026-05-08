
# ============================================================
# RISK ANALYZER
# ============================================================
#
# This file:
# - Categorizes diseases
# - Computes outbreak statistics
# - Determines overall risk level
#
# The analysis is based on:
# - Total number of cases
# - Number of unique diseases
# - Disease categories
# ============================================================


# ============================================================
# DISEASE CATEGORY GROUPS
# ============================================================
# Sets are used for faster membership lookup.
# ============================================================

WATERBORNE = [
    "cholera",
    "typhoid",
    "paratyphoid",
    "dysentery",
    "diarrhea",
    "e coli",
    "hepatitis a",
    "hepatitis e",
    "giardia",
    "amoebiasis",
    "cryptosporidium",
    "leptospirosis",
    "salmonella",
    "gastroenteritis",
    "food poisoning"
]
VECTORBORNE = [
    "malaria",
    "dengue",
    "chikungunya",
    "zika",
    "yellow fever",
    "japanese encephalitis",
    "west nile virus"
]
GENERAL = [
    "flu",
    "viral fever",
    "fever",
    "cold",
    "cough",
    "skin infection",
    "eye infection",
    "respiratory infection",
    "weakness",
    "body pain"
]

# ============================================================
# RISK LEVEL LOGIC
# ============================================================
# Determines outbreak severity using:
# - Total case count
# - Number of disease types
# ============================================================


def get_risk_level(total_cases, num_diseases):
    if total_cases > 25 and num_diseases >= 3:
        return "CRITICAL"
    elif total_cases > 25:
        return "HIGH"
    elif total_cases > 10:
        return "MEDIUM"
    else:
        return "LOW"
    
# ============================================================
# MAIN RISK ANALYSIS
# ============================================================
# history format:
# {
#     "cholera": 5,
#     "flu": 3
# }
# ============================================================
    
def analyze_risk(history):

    # Store category-wise case counts
    risk_breakdown = {
        "waterborne": 0,
        "vectorborne": 0,
        "general": 0
    }

    # Categorize diseases
    for disease_name, count in history.items():

        normalized_name = disease_name.lower().strip()

        if normalized_name in WATERBORNE:
            risk_breakdown["waterborne"] += count

        elif normalized_name in VECTORBORNE:
            risk_breakdown["vectorborne"] += count

        else:
            risk_breakdown["general"] += count

    # Overall outbreak statistics
    total_cases = sum(history.values())
    num_diseases = sum(1 for count in history.values() if count > 0)

    # Determine final risk level
    risk_level = get_risk_level(total_cases, num_diseases)

    return {
        "risk": risk_breakdown,
        "total_cases": total_cases,
        "num_diseases": num_diseases,
        "risk_level": risk_level
    }