# ============================================================
# RESPONSE ENGINE
# ============================================================
#
# This file generates human-readable outbreak summaries.
#
# Responsibilities:
# - summarize outbreak data
# - explain possible causes
# - suggest actions
# - generate alert messages
#
# Used before the AI/RAG stage.
# ============================================================


# ============================================================
# GENERATE OUTBREAK RESPONSE
# ============================================================
#
# Inputs:
# - parsed report
# - analyzed risk data
#
# Output:
# formatted outbreak summary string
# ============================================================

def generate_response(report, analysis):

    location = report["location"]

    diseases = report["diseases"]

    # ========================================================
    # TOTAL REPORTED CASES
    # ========================================================

    total_reported = sum(
        disease_entry["count"]
        for disease_entry in diseases
    )

    # ========================================================
    # RESPONSE STRING
    # ========================================================

    response = ""

    # ========================================================
    # BASIC OUTBREAK INFORMATION
    # ========================================================

    response += (
        f"\n⚠ {analysis['risk_level']} RISK DETECTED\n"
    )

    response += (
        f"Location: {location if location else 'Unknown'}\n"
    )

    response += (
        f"Reported: {total_reported} cases\n"
    )

    # ========================================================
    # DISEASE BREAKDOWN
    # ========================================================

    response += "Breakdown:\n"

    for disease_entry in diseases:

        response += (
            f"  - {disease_entry['standard']} "
            f": {disease_entry['count']}\n"
        )

    response += (
        f"Total Cases in Area: "
        f"{analysis['total_cases']}\n"
    )

    # ========================================================
    # PRIMARY CONCERN
    # ========================================================
    # Highest case-count disease.
    # ========================================================

    if diseases:

        dominant_disease = max(
            diseases,
            key=lambda disease_entry: disease_entry["count"]
        )

        response += (
            f"Primary Concern: "
            f"{dominant_disease['standard']} "
            f"({dominant_disease['count']})\n"
        )

    # ========================================================
    # POSSIBLE CAUSES
    # ========================================================

    response += "\nPossible Causes:\n"

    if analysis["risk"]["waterborne"] > 0:

        response += (
            "- Likely contaminated water "
            "or poor sanitation\n"
        )

    if analysis["risk"]["vectorborne"] > 0:

        response += (
            "- Mosquito breeding due to stagnant water\n"
        )

    if analysis["risk"]["general"] > 0:

        response += (
            "- Seasonal or hygiene-related infections\n"
        )

    # ========================================================
    # RECOMMENDED ACTIONS
    # ========================================================

    response += "\nRecommended Actions:\n"

    if analysis["risk"]["waterborne"] > 0:

        response += "- Boil drinking water\n"

        response += "- Avoid unsafe water sources\n"

    if analysis["risk"]["vectorborne"] > 0:

        response += "- Remove stagnant water\n"

        response += "- Use mosquito nets\n"

    if analysis["risk"]["general"] > 0:

        response += "- Maintain hygiene\n"

        response += "- Avoid crowded areas\n"

    # ========================================================
    # ALERT SECTION
    # ========================================================

    if analysis["risk_level"] == "CRITICAL":

        response += (
            "\n🚨 Immediate intervention required. "
            "Contact health authorities.\n"
        )

    elif analysis["risk_level"] == "HIGH":

        response += (
            "\n⚠ Situation worsening. "
            "Take action within 24 hours.\n"
        )

    return response