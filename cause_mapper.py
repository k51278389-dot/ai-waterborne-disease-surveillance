# ============================================================
# DISEASE → CAUSE CATEGORY MAPPER
# ============================================================
#
# This file derives outbreak cause category using:
# - detected diseases
# - disease transmission groups
#
# Example:
# cholera + typhoid -> waterborne
#
# Used for:
# - automatic cause inference
# - fallback reasoning
# - AI/RAG routing
# ============================================================

from risk_analyzer import (
    WATERBORNE,
    VECTORBORNE,
    GENERAL
)


# ============================================================
# DERIVE CAUSE TYPE FROM DISEASES
# ============================================================
#
# Input:
# [
#     "cholera",
#     "typhoid"
# ]
#
# Output:
# "waterborne"
# ============================================================

def derive_cause_type(diseases):

    # Category counters
    waterborne_count = 0
    vectorborne_count = 0
    general_count = 0

    # ========================================================
    # COUNT DISEASE CATEGORIES
    # ========================================================

    for disease_name in diseases:

        normalized_name = disease_name.lower()

        if normalized_name in WATERBORNE:
            waterborne_count += 1

        elif normalized_name in VECTORBORNE:
            vectorborne_count += 1

        elif normalized_name in GENERAL:
            general_count += 1

    # ========================================================
    # DETERMINE DOMINANT CATEGORY
    # ========================================================

    if (
        waterborne_count > vectorborne_count
        and waterborne_count > general_count
    ):
        return "waterborne"

    elif (
        vectorborne_count > waterborne_count
        and vectorborne_count > general_count
    ):
        return "vectorborne"

    elif general_count > 0:
        return "general"

    # No clear category
    return None