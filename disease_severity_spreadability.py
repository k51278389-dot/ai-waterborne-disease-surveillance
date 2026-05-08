# ============================================================
# DISEASE SEVERITY & SPREADABILITY DATABASE
# ============================================================
#
# This file stores:
# - Disease severity scores
# - Disease spreadability scores
# - Utility helper functions for normalized lookup
#
# These scores are later used for:
# - Risk analysis
# - Disease prioritization
# - Dominant disease detection
# - AI response ranking
#
# Higher score = more dangerous / more contagious
# ============================================================


# ============================================================
# DISEASE SEVERITY SCORES
# ============================================================
# Measures how medically dangerous a disease is.
#
# Example:
# Cholera is extremely severe because it can rapidly
# cause dehydration and large outbreaks.
# ============================================================

DISEASE_SEVERITY = {
    # VERY HIGH
    "cholera": 7,
    "typhoid": 6,
    "paratyphoid": 5,
    "dysentery": 5,
    "hepatitis a": 5,
    "hepatitis e": 5,

    # HIGH
    "malaria": 5,
    "dengue": 5,
    "leptospirosis": 5,
    "salmonella": 4,
    "e coli": 4,

    # MODERATE
    "gastroenteritis": 4,
    "diarrhea": 4,
    "amoebiasis": 4,
    "giardia": 4,
    "cryptosporidium": 4,
    "chikungunya": 4,
    "japanese encephalitis": 4,
    "yellow fever": 4,

    # LOWER MODERATE
    "zika": 3,
    "west nile virus": 3,
    "food poisoning": 3,

    # LOW
    "flu": 2,
    "viral fever": 2,
    "fever": 2,

    # VERY LOW
    "cold": 1,
    "cough": 1,
    "skin infection": 1,
    "eye infection": 1,
    "respiratory infection": 1,
    "weakness": 1,
    "body pain": 1
}


# ============================================================
# DISEASE SPREADABILITY SCORES
# ============================================================
# Measures how easily the disease spreads.
#
# Example:
# Cholera spreads rapidly through contaminated water.
# ============================================================

SPREADABILITY = {
    # VERY HIGH
    "cholera": 5,
    "diarrhea": 5,
    "gastroenteritis": 5,
    "dysentery": 5,

    # HIGH
    "typhoid": 4,
    "paratyphoid": 4,
    "e coli": 4,
    "salmonella": 4,
    "amoebiasis": 4,
    "giardia": 4,
    "cryptosporidium": 4,
    "food poisoning": 4,

    # MODERATE
    "hepatitis a": 3,
    "hepatitis e": 3,
    "leptospirosis": 3,

    # VECTORBORNE
    "dengue": 4,
    "malaria": 4,
    "chikungunya": 3,
    "zika": 3,
    "west nile virus": 3,
    "japanese encephalitis": 3,
    "yellow fever": 3,

    # GENERAL INFECTIOUS
    "flu": 3,
    "viral fever": 3,
    "fever": 2,

    # LOW SPREAD
    "cold": 2,
    "cough": 2,
    "respiratory infection": 2,
    "skin infection": 1,
    "eye infection": 1,
    "weakness": 1,
    "body pain": 1
}



# ============================================================
# HELPER FUNCTIONS
# ============================================================


def normalize_disease_name(name):
    """
    Normalize disease names for consistent dictionary lookup.

    Example:
    " Cholera " -> "cholera"
    "TYPHOID" -> "typhoid"
    """

    return name.strip().lower()



def get_disease_severity_score(dominant_disease):
    """
    Return severity score of dominant disease.

    Default score = 2
    This prevents crashes when disease is unknown.
    """

    if not dominant_disease:
        return 0

    disease_name = normalize_disease_name(dominant_disease["standard"])

    return DISEASE_SEVERITY.get(disease_name, 2)



def get_spreadability(disease_name):
    """
    Return spreadability score of a disease.

    Default score = 2 for unknown diseases.
    """

    if not disease_name:
        return 2

    

    normalized_name = normalize_disease_name(disease_name)

    return SPREADABILITY.get(normalized_name, 2)



