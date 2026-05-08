
# ============================================================
# DISEASE COMPARISON ENGINE
# ============================================================
#
# This file compares:
# - Sensor predicted diseases
# - User reported diseases
#
# Comparison categories:
#
# matched:
#     Disease appears in BOTH sensor and user data
#
# sensor_only:
#     Disease predicted by environment but not reported
#
# user_only:
#     Disease reported by user but not supported by environment
# ============================================================

from disease_severity_spreadability import DISEASE_SEVERITY, SPREADABILITY
# ============================================================
# MAIN COMPARISON FUNCTION
# ============================================================


def compare_diseases(sensor_diseases, user_diseases):

    # Convert disease dictionaries into lowercase name sets
    sensor_set = {
        disease["standard"].lower()
        for disease in sensor_diseases
    }

    user_set = {
        disease["standard"].lower()
        for disease in user_diseases
    }

    # Find overlaps and differences
    matched = sensor_set & user_set
    sensor_only = sensor_set - user_set
    user_only = user_set - sensor_set

    return {
        "matched": list(matched),
        "sensor_only": list(sensor_only),
        "user_only": list(user_only)
    }
    
    

# ============================================================
# GENERATE HUMAN-READABLE INSIGHTS
# ============================================================
# This converts raw comparison data into explanatory messages.
# ============================================================


def generate_comparison_insights(comparison):

    matched = comparison["matched"]
    sensor_only = comparison["sensor_only"]
    user_only = comparison["user_only"]

    messages = []
    high_risk_predictions = []

    # ========================================================
    # CONFIRMED MATCHES
    # ========================================================

    for disease_name in matched:
        messages.append(
            f"{disease_name} cases match environmental conditions → high confidence."
        )

    # ========================================================
    # SENSOR-ONLY PREDICTIONS
    # ========================================================
    # Only high severity/spread diseases are highlighted.
    # This prevents noisy output.
    # ========================================================

    for disease_name in sensor_only:

        severity = DISEASE_SEVERITY.get(disease_name, 2)
        spread = SPREADABILITY.get(disease_name, 2)

        if severity >= 4 or spread >= 4:
            high_risk_predictions.append(disease_name)

    # Limit predictions to top few warnings
    for disease_name in high_risk_predictions[:3]:
        messages.append(
            f"Potential risk of {disease_name} detected (not yet reported)."
        )

    # ========================================================
    # USER-ONLY REPORTS
    # ========================================================

    for disease_name in user_only:
        messages.append(
            f"{disease_name} reported but not explained by environmental conditions."
        )

    return messages

# ============================================================
# LIGHTWEIGHT COMPARISON INTERPRETER
# ============================================================
# Simpler version of the comparison explanation.
#
# This version:
# - does not use severity scoring
# - surfaces more sensor predictions
# - is useful for quick summaries/debugging
# ============================================================

def interpret_comparison(comparison):

    matched = comparison["matched"]
    sensor_only = comparison["sensor_only"]
    user_only = comparison["user_only"]

    messages = []

    # ========================================================
    # MATCHED DISEASES
    # ========================================================
    # Diseases confirmed by both:
    # - environmental conditions
    # - user reports
    # ========================================================

    for disease_name in matched:
        messages.append(
            f"{disease_name} cases align with environmental risk."
        )

    # ========================================================
    # SENSOR-ONLY PREDICTIONS
    # ========================================================
    # Limit warning count to avoid excessive noisy output.
    # ========================================================

    for disease_name in sensor_only[:5]:
        messages.append(
            f"Potential risk of {disease_name} detected (not yet reported)."
        )

    # ========================================================
    # USER-ONLY REPORTS
    # ========================================================

    for disease_name in user_only:
        messages.append(
            f"{disease_name} reported but not explained by environmental conditions."
        )

    return messages
