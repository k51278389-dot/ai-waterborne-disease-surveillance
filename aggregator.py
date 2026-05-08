# ============================================================
# OUTBREAK AGGREGATOR
# ============================================================
#
# This file processes multiple sensor locations and:
# - generates outbreak analyses
# - ranks locations by danger level
# - identifies highest-risk regions
#
# Used for:
# - village ranking
# - outbreak prioritization
# - dashboard summaries
# ============================================================

from sensor_adapter import sensor_to_report
from analysis import analyze_report


# ============================================================
# PROCESS ALL SENSOR LOCATIONS
# ============================================================
#
# Converts raw sensor logs into analyzed outbreak reports.
#
# Flow:
# sensor -> report -> analysis
# ============================================================

def process_all_locations(sensor_logs):

    results = []

    for sensor_data in sensor_logs:

        # Convert sensor readings into disease report
        report = sensor_to_report(sensor_data)

        # Generate outbreak analysis
        analysis = analyze_report(report)

        results.append(analysis)

    return results


# ============================================================
# GET MOST RISKY LOCATION
# ============================================================
#
# Ranking priority:
#
# 1. Risk Level
# 2. Impact Score
# 3. Total Cases
#
# Example:
# CRITICAL > HIGH > MEDIUM > LOW
# ============================================================

def get_most_risky(results):

    if not results:
        return None

    # Numeric ranking for risk comparison
    priority = {
        "CRITICAL": 4,
        "HIGH": 3,
        "MEDIUM": 2,
        "LOW": 1
    }

    return max(
        results,
        key=lambda analysis: (
            priority.get(
                analysis.get("risk_level", "LOW"),
                1
            ),

            analysis.get("impact_score", 0),

            analysis.get("total_cases", 0)
        )
    )


# ============================================================
# GET TOP N RISKY LOCATIONS
# ============================================================
#
# Returns top outbreak locations sorted by:
# - risk level
# - impact score
# - total cases
# ============================================================

def get_top_n(results, n=3):

    priority = {
        "CRITICAL": 4,
        "HIGH": 3,
        "MEDIUM": 2,
        "LOW": 1
    }

    # Filter invalid entries
    valid_results = [
        analysis
        for analysis in results
        if analysis and "risk_level" in analysis
    ]

    if not valid_results:
        return []

    # Sort highest risk first
    sorted_results = sorted(
        valid_results,

        key=lambda analysis: (
            priority.get(
                analysis.get("risk_level", "LOW"),
                1
            ),

            analysis.get("impact_score", 0),

            analysis.get("total_cases", 0)
        ),

        reverse=True
    )

    return sorted_results[:n]


