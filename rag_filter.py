from disease_severity_spreadability import DISEASE_SEVERITY, SPREADABILITY

def select_important_diseases(comparison):
    important = set()

    # ✅ ALWAYS include user-reported diseases
    important.update(comparison["matched"])
    important.update(comparison["user_only"])

    # ✅ selectively include sensor predictions
    for d in comparison["sensor_only"]:
        severity = DISEASE_SEVERITY.get(d, 2)
        spread = SPREADABILITY.get(d, 2)

        if severity >= 4 or spread >= 4:
            important.add(d)

    # ranking
    def score(d):
        return (
            DISEASE_SEVERITY.get(d, 2) *
            SPREADABILITY.get(d, 2)
        )

    return sorted(important, key=score, reverse=True)[:5]