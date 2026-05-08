# ============================================================
# ANALYSIS ENGINE
# ============================================================
#
# This file is responsible for:
# - Computing disease impact
# - Determining dominant disease
# - Computing outbreak score
# - Generating outbreak insights
# - Producing final structured analysis
#
# This acts as the central intelligence layer between:
# - sensor predictions
# - disease scoring
# - risk analysis
# - AI/RAG pipeline
# ============================================================

import math

from risk_analyzer import analyze_risk

from disease_severity_spreadability import (
    DISEASE_SEVERITY,
    SPREADABILITY,
    get_spreadability
)

# ============================================================
# CONVERT REPORT INTO HISTORY FORMAT
# ============================================================
#
# Converts:
#
# [
#     {"standard": "cholera", "count": 5}
# ]
#
# into:
#
# {
#     "cholera": 5
# }
#
# This format is easier for risk analysis functions.
# ============================================================

def report_to_history(report):

    history = {}

    for disease_entry in report["diseases"]:
        history[disease_entry["standard"]] = disease_entry["count"]

    return history


# ============================================================
# COMPUTE DISEASE IMPACT
# ============================================================
#
# Formula:
#
# severity × spreadability × case_count
#
# Used for:
# - Dominant disease detection
# - Disease prioritization
# - Ranking diseases by importance
#
# Higher score = more dangerous outbreak contribution
# ============================================================

def compute_disease_impact(disease_entry):

    disease_name = disease_entry["standard"].lower()
    case_count = disease_entry["count"]

    severity = DISEASE_SEVERITY.get(disease_name, 2)
    spread = SPREADABILITY.get(disease_name, 2)

    return severity * spread * case_count


# ============================================================
# DETERMINE DOMINANT DISEASE
# ============================================================
#
# Returns the disease with highest weighted impact.
#
# This is NOT simply the highest count.
# Severity and spreadability also influence priority.
# ============================================================

def get_dominant_disease(diseases):

    if not diseases:
        return None

    return max(diseases, key=compute_disease_impact)


# ============================================================
# COMPUTE TOTAL OUTBREAK SCORE
# ============================================================
#
# Uses logarithmic scaling:
#
# severity × spreadability × log(case_count + 1)
#
# Log scaling prevents extremely large case counts
# from dominating the score too aggressively.
# ============================================================

def compute_disease_score(diseases):

    if not diseases:
        return 0

    total_score = 0

    for disease_entry in diseases:

        disease_name = disease_entry["standard"].lower()
        case_count = disease_entry["count"]

        severity = DISEASE_SEVERITY.get(disease_name, 2)
        spread = SPREADABILITY.get(disease_name, 2)

        # Log scaling reduces extreme growth
        score = severity * spread * math.log(case_count + 1)

        total_score += score

    return total_score


# ============================================================
# MAIN REPORT ANALYSIS
# ============================================================
#
# Combines:
# - risk analysis
# - disease scoring
# - dominant disease detection
# - insight generation
#
# Produces one final structured analysis object.
# ============================================================

def analyze_report(report):

    diseases = report["diseases"]

    # ========================================================
    # HANDLE EMPTY REPORTS
    # ========================================================
    # Prevents crashes when no diseases are detected.
    # ========================================================

    if not diseases:
        return {
            "location": report["location"],
            "dominant_disease": None,
            "diseases": [],
            "total_cases": 0,
            "num_diseases": 0,
            "risk_level": "LOW",
            "impact_score": 0,
            "sensor": report.get("sensor", {}),
            "insight": "No significant health risk detected."
        }

    # ========================================================
    # CONVERT REPORT FORMAT
    # ========================================================

    history = report_to_history(report)

    # ========================================================
    # RISK ANALYSIS
    # ========================================================

    risk_data = analyze_risk(history)

    # ========================================================
    # DOMINANT DISEASE DETECTION
    # ========================================================

    dominant_disease = get_dominant_disease(diseases)

    # ========================================================
    # TOTAL IMPACT SCORE
    # ========================================================

    impact_score = compute_disease_score(diseases)

    # ========================================================
    # FINAL STRUCTURED ANALYSIS OBJECT
    # ========================================================

    analysis = {
        "location": report["location"],
        "dominant_disease": dominant_disease,
        "diseases": diseases,
        "total_cases": risk_data["total_cases"],
        "num_diseases": risk_data["num_diseases"],
        "risk_level": risk_data["risk_level"],
        "impact_score": impact_score,
        "sensor": report.get("sensor", {})
    }

    # Generate readable outbreak insight
    analysis["insight"] = generate_insight(analysis)

    return analysis


# ============================================================
# GENERATE HUMAN-READABLE INSIGHT
# ============================================================
#
# Produces a concise outbreak summary using:
# - dominant disease
# - spreadability
# - sensor conditions
# - secondary disease
#
# Example:
#
# "CRITICAL risk driven by cholera (high spread)
# with secondary concern of typhoid due to
# high turbidity and abnormal pH."
# ============================================================

def generate_insight(analysis):

    sensor_data = analysis.get("sensor", {})
    diseases = analysis.get("diseases", [])

    if not diseases:
        return "No significant health risk detected."

    # ========================================================
    # SORT DISEASES BY IMPACT
    # ========================================================

    sorted_diseases = sorted(
        diseases,
        key=compute_disease_impact,
        reverse=True
    )

    dominant_disease = sorted_diseases[0]["standard"]

    secondary_disease = (
        sorted_diseases[1]["standard"]
        if len(sorted_diseases) > 1
        else None
    )

    # ========================================================
    # DETERMINE SPREAD LEVEL
    # ========================================================

    spread_score = get_spreadability(dominant_disease)

    if spread_score >= 4:
        spread_text = "high spread"

    elif spread_score == 3:
        spread_text = "moderate spread"

    else:
        spread_text = "low spread"

    # ========================================================
    # SENSOR-BASED CAUSE ANALYSIS
    # ========================================================

    turbidity = sensor_data.get("turbidity", 0)
    ph = sensor_data.get("ph", 7)

    cause_parts = []

    # High turbidity usually indicates contamination
    if turbidity > 40:
        cause_parts.append("high turbidity (water contamination)")

    elif turbidity > 20:
        cause_parts.append("moderate turbidity")

    # Abnormal pH may indicate unsafe water conditions
    if ph < 6 or ph > 8.5:
        cause_parts.append("abnormal pH")

    # Combine causes into readable text
    cause = (
        " and ".join(cause_parts)
        if cause_parts
        else "limited environmental evidence"
    )

    # ========================================================
    # FINAL INSIGHT GENERATION
    # ========================================================

    if secondary_disease:
        return (
            f"{analysis['risk_level']} risk driven by "
            f"{dominant_disease} ({spread_text}) with "
            f"secondary concern of {secondary_disease} "
            f"due to {cause}."
        )

    return (
        f"{analysis['risk_level']} risk driven by "
        f"{dominant_disease} ({spread_text}) "
        f"due to {cause}."
    )
