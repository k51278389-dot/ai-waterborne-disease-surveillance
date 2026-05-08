# ============================================================
# RAG DISEASE FILTER
# ============================================================
#
# This file selects the most important diseases
# before sending them into the RAG pipeline.
#
# Goals:
# - reduce noisy diseases
# - prioritize dangerous outbreaks
# - improve AI response quality
#
# Selection priority:
# - user reported diseases
# - environmentally confirmed diseases
# - high severity predictions
# ============================================================

from disease_severity_spreadability import (
    DISEASE_SEVERITY,
    SPREADABILITY
)


# ============================================================
# SELECT IMPORTANT DISEASES
# ============================================================
#
# Input:
# comparison = {
#     "matched": [...],
#     "sensor_only": [...],
#     "user_only": [...]
# }
#
# Output:
# [
#     "cholera",
#     "typhoid"
# ]
# ============================================================

def select_important_diseases(comparison):

    important_diseases = set()

    # ========================================================
    # ALWAYS INCLUDE USER-REPORTED DISEASES
    # ========================================================
    # These are considered highest priority because
    # they represent confirmed human-reported cases.
    # ========================================================

    important_diseases.update(comparison["matched"])

    important_diseases.update(comparison["user_only"])

    # ========================================================
    # SELECT HIGH-RISK SENSOR PREDICTIONS
    # ========================================================
    # Only severe/high-spread predictions are included.
    # This reduces unnecessary RAG noise.
    # ========================================================

    for disease_name in comparison["sensor_only"]:

        severity = DISEASE_SEVERITY.get(disease_name, 2)

        spread = SPREADABILITY.get(disease_name, 2)

        if severity >= 4 or spread >= 4:
            important_diseases.add(disease_name)

    # ========================================================
    # RANKING FUNCTION
    # ========================================================
    # Higher severity + spread diseases appear first.
    # ========================================================

    def disease_priority_score(disease_name):

        return (
            DISEASE_SEVERITY.get(disease_name, 2)
            *
            SPREADABILITY.get(disease_name, 2)
        )

    # Return top diseases only
    return sorted(
        important_diseases,
        key=disease_priority_score,
        reverse=True
    )[:5]