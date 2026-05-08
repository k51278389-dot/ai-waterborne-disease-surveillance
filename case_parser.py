# ============================================================
# CASE PARSER
# ============================================================
#
# Main orchestration layer of the system.
#
# Responsibilities:
# - parse user outbreak reports
# - detect diseases
# - detect locations
# - manage outbreak memory
# - run risk analysis
# - compare sensor predictions
# - trigger RAG pipeline
#
# This is effectively the central controller of the project.
# ============================================================


# ============================================================
# IMPORTS
# ============================================================

import re
import json

from difflib import get_close_matches

# RAG
from rag_pipeline import (
    build_query_from_analysis,
    run_rag_pipeline
)

# Memory
from location_memory_manager import (
    add_case,
    get_location_history,
    print_all_locations,
    save_memory,
    location_memory
)

# Risk Analysis
from risk_analyzer import (
    WATERBORNE,
    VECTORBORNE,
    GENERAL,
    analyze_risk
)

# Cause Detection
from cause import detect_cause_type

# Response Engine
from response_engine import generate_response

# Comparison Engine
from compare import (
    compare_diseases,
    generate_comparison_insights
)

# Sensor Adapter
from sensor_adapter import sensor_to_report

# RAG Filtering
from rag_filter import select_important_diseases

# Cause Mapping
from cause_mapper import derive_cause_type


# ============================================================
# KNOWN DISEASE DATABASE
# ============================================================

KNOWN_DISEASES = (
    WATERBORNE
    + VECTORBORNE
    + GENERAL
)

# ============================================================
# LOCATION DATABASE
# ============================================================

KNOWN_LOCATIONS = [
    "East Kalabaria",
    "Kakichhuah",
    "Nalani Gaon",
    "Barigaon",
    "Kothora",
    "Behiating",
    "Dudhnoi",
    "Borbam Tea Estate",
    "Boginodi",
    "Thanga Village",
    "Gamariguri",
    "Lowkhowa",
    "Paschim Koliabar",
    "Binakandi",
    "Kathiatoli",
    "Titabor",
    "Selenghat",
    "Telahi",
    "Ghaimora Gossai",
    "Narayanpur",
    "Barama",
    "Naherbari",
    "Tumulpur",
    "Sissiborgoan",
    "Jonai",
    "Mandia",
    "Bajali",
    "Mankachar",
    "Bahmolla",
    "Sialmari",
    "Teklabala",
    "Kahibari",
    "Khunyai",
    "Kakching",
    "Nighthou Lekei",
    "Doimukh",
    "Yazali",
    "Dokum",
    "Hunli",
    "Tzudikong",
    "Tuli",
    "Naginimara",
    "Jirania",
    "Salema",
    "Kamalpur",
    "Nartiang",
    "Umden",
    "Madanpur Rampur",
    "Laitryngew",
    "Yuksom"
]


# ============================================================
# LOCATION ALIASES
# ============================================================

LOCATION_ALIASES = {

    "nighthou": "Nighthou Lekei",
    "lekei": "Nighthou Lekei",

    "sissiborgaon": "Sissiborgoan",

    "borbam": "Borbam Tea Estate",

    "madanpur": "Madanpur Rampur",
    "rampur": "Madanpur Rampur",

    "paschim koliabar": "Paschim Koliabar",
    "koliabar": "Paschim Koliabar",

    "ghaemora": "Ghaimora Gossai",
    "gossai": "Ghaimora Gossai",

    "nartiang": "Nartiang",
    "laitryngew": "Laitryngew"
}


# ============================================================
# DISEASE ALIASES
# ============================================================
#
# Maps casual/non-medical phrases into
# standardized disease names.
# ============================================================

ALIASES = {

    # ========================================================
    # DIARRHEA
    # ========================================================

    "loose motion": "diarrhea",
    "loose motions": "diarrhea",

    # ========================================================
    # GASTROENTERITIS
    # ========================================================

    "stomach pain": "gastroenteritis",
    "stomach problem": "gastroenteritis",
    "vomiting": "gastroenteritis",
    "vomit": "gastroenteritis",

    "dirty water": "gastroenteritis",
    "bad water": "gastroenteritis",
    "smelly water": "gastroenteritis",
    "contaminated water": "gastroenteritis",
    "drinking dirty water": "gastroenteritis",
    "toilet water mixing": "gastroenteritis",

    # ========================================================
    # FOOD RELATED
    # ========================================================

    "food poisoning": "food poisoning",

    # ========================================================
    # VECTORBORNE
    # ========================================================

    "mosquito fever": "malaria",
    "mosquito bite fever": "malaria",
    "dengue fever": "dengue",
    "high fever mosquito": "dengue",

    "stagnant water": "malaria",
    "water logging": "malaria",
    "mosquito breeding": "malaria",

    # ========================================================
    # GENERAL
    # ========================================================

    "normal fever": "fever",
    "seasonal fever": "viral fever",
    "cold and cough": "flu",
    "body weakness": "weakness",
    "skin rash": "skin infection",
    "eye redness": "eye infection",
}


# ============================================================
# SENSOR DATA LOADING
# ============================================================

with open("sensor_logs.json") as file:

    SENSOR_DATA = json.load(file)
    
# ============================================================
# GET SENSOR DATA BY LOCATION
# ============================================================

def get_sensor_by_location(location):

    if not location:
        return None

    for sensor_entry in SENSOR_DATA:

        if sensor_entry["location"].lower() == location.lower():

            return sensor_entry

    return None


# ============================================================
# NORMALIZE USER INPUT
# ============================================================

def normalize_user_input(text: str) -> str:

    text = text.lower()

    # Separate joined words/numbers
    text = re.sub(r"(\d)([a-zA-Z])", r"\1 \2", text)

    text = re.sub(r"([a-zA-Z])(\d)", r"\1 \2", text)

    # Standardize connectorsh
    connectors = [
        " and ",
        " & ",
        ",",
        ";",
        " with "
    ]

    for connector in connectors:
        text = text.replace(connector, " | ")

    # Remove extra spaces
    text = re.sub(r"\s+", " ", text).strip()

    return text


# ============================================================
# NORMALIZE CAUSE INPUT
# ============================================================

def normalize_cause_input(text):

    text = text.lower().strip()

    # Remove punctuation
    text = re.sub(r"[^\w\s]", "", text)

    # Normalize spacing
    text = re.sub(r"\s+", " ", text)

    return text


# ============================================================
# MAIN CASE REPORT PARSER
# ============================================================
#
# Extracts:
# - diseases
# - case counts
# - location
#
# Handles:
# - aliases
# - fuzzy matching
# - noisy user inputs
# ============================================================

def parse_case_report(text):

    text = " ".join(text.split())

    text_lower = text.lower()

    # ========================================================
    # NORMALIZE INPUT
    # ========================================================

    normalized = normalize_user_input(text)

    segments = normalized.split("|")

    # ========================================================
    # DISEASE EXTRACTION
    # ========================================================

    diseases = []

    LOCATION_SET = {
        token
        for location in KNOWN_LOCATIONS
        for token in location.lower().split()
    }

    for segment in segments:

        segment = segment.strip()

        segment_lower = segment.lower()

        words = re.findall(
            r"\b[a-zA-Z]+\b",
            segment_lower
        )

        # ====================================================
        # NOISE FILTER
        # ====================================================

        NOISE_WORDS = {

            "patient",
            "patients",
            "case",
            "cases",
            "report",
            "reported",

            "in",
            "at",
            "of",
            "with",
            "from",
            "to",
            "and",
            "or",

            "have",
            "has",
            "had",
            "got",
            "getting",
            "suffering",
            "having",

            "around",
            "about",
            "approx",
            "approximately",

            "village",
            "area",
            "region",
            "place",

            "today",
            "yesterday",
            "recently",

            "people",
            "person",
            "individuals"
        }

        words = [

            word
            for word in words

            if (
                word.lower() not in NOISE_WORDS
                and not word.isdigit()
            )
        ]

        disease_name = None

        # ====================================================
        # CASE COUNT
        # ====================================================

        numbers = re.findall(r"\d+", segment_lower)

        case_count = int(numbers[0]) if numbers else 1

        # ====================================================
        # CLEAN ORIGINAL PHRASE
        # ====================================================

        original_phrase = " ".join(

            word
            for word in words

            if word not in LOCATION_SET
        )

        # ====================================================
        # ALIAS MATCH
        # ====================================================

        for word in words:

            word = word.lower()

            if word in LOCATION_SET:
                continue

            if word in ALIASES:
                disease_name = ALIASES[word]
                break

        # ====================================================
        # PHRASE ALIAS MATCH
        # ====================================================

        if not disease_name:

            for phrase, mapped_disease in ALIASES.items():

                if f" {phrase} " in f" {segment_lower} ":

                    disease_name = mapped_disease
                    break
                # ====================================================
        # DIRECT DISEASE MATCH
        # ====================================================

        if not disease_name:

            for word in words:

                word = word.lower()

                if word in LOCATION_SET:
                    continue

                if word in KNOWN_DISEASES:
                    disease_name = word
                    break

        # ====================================================
        # FUZZY MATCHING
        # ====================================================
        # Handles typos like:
        # cholra -> cholera
        # flue -> flu
        # ====================================================

        if not disease_name:

            for word in words:

                if word in LOCATION_SET:
                    continue

                match = get_close_matches(
                    word,
                    KNOWN_DISEASES,
                    n=1,
                    cutoff=0.72
                )

                if match:
                    disease_name = match[0]
                    break

        # ====================================================
        # SAVE DISEASE
        # ====================================================

        if disease_name:

            diseases.append({

                "original": original_phrase,

                "standard": disease_name,

                "count": case_count
            })

    # ========================================================
    # LOCATION EXTRACTION
    # ========================================================

    words = text_lower.split()

    location_found = None

    # ========================================================
    # LOCATION ALIAS MATCH
    # ========================================================

    for phrase, mapped_location in LOCATION_ALIASES.items():

        if phrase in text_lower:

            location_found = mapped_location
            break

    # ========================================================
    # FUZZY LOCATION MATCH
    # ========================================================

    if not location_found:

        location_candidate = text_lower

        if " in " in text_lower:
            location_candidate = text_lower.split(" in ")[-1]

        clean_location_text = re.sub(
            r"[^a-z\s]",
            "",
            location_candidate
        ).strip()

        clean_location_text = " ".join(
            clean_location_text.split()
        )

        # ====================================================
        # FULL LOCATION FUZZY MATCH
        # ====================================================

        match = get_close_matches(

            clean_location_text,

            [location.lower() for location in KNOWN_LOCATIONS],

            n=1,
            cutoff=0.6
        )

        if match:

            for location in KNOWN_LOCATIONS:

                if location.lower() == match[0]:

                    location_found = location
                    break

    # ========================================================
    # WORD-LEVEL LOCATION MATCH
    # ========================================================

    if not location_found:

        for word in clean_location_text.split():

            match = get_close_matches(

                word,

                [location.lower() for location in KNOWN_LOCATIONS],

                n=1,
                cutoff=0.75
            )

            if match:

                for location in KNOWN_LOCATIONS:

                    if location.lower() == match[0]:

                        location_found = location
                        break

                if location_found:
                    break

    # ========================================================
    # PARTIAL MULTI-WORD LOCATION MATCH
    # ========================================================

    if not location_found:

        for location in KNOWN_LOCATIONS:

            location_words = location.lower().split()

            matched_words = sum(

                1
                for location_word in location_words

                if location_word in words
            )

            if matched_words >= len(location_words) * 0.6:

                location_found = location
                break

    # ========================================================
    # EMPTY DISEASE HANDLING
    # ========================================================

    if not diseases:

        return {
            "diseases": [],
            "location": location_found
        }

    # ========================================================
    # FINAL STRUCTURED OUTPUT
    # ========================================================

    return {
        "diseases": diseases,
        "location": location_found
    }


# ============================================================
# VALID UNKNOWN INPUTS
# ============================================================

VALID_UNKNOWN = {

    "idk",
    "dk",
    "unk",
    "na",
    "n/a",

    "unknown",
    "not known",
    "no idea",
    "dont know",
    "don't know",

    "i dont know",
    "i don't know",

    "i have no idea",

    "no clue",
    "not sure",
    "unsure",

    "cant say",
    "can't say",

    "no information",
    "no info",

    "i dont  know",
    "dont  know",
}


# ============================================================
# VALIDATE USER CAUSE INPUT
# ============================================================

def is_valid_cause(text):

    text = normalize_cause_input(text)

    # ========================================================
    # ALLOW UNKNOWN-TYPE INPUTS
    # ========================================================

    if text in VALID_UNKNOWN:
        return True

    # ========================================================
    # REJECT VERY SHORT INPUTS
    # ========================================================

    if len(text) < 3:
        return False

    # ========================================================
    # REJECT NON-MEANINGFUL INPUTS
    # ========================================================

    words = text.split()

    if all(len(word) <= 1 for word in words):
        return False

    return True


# ============================================================
# MAIN APPLICATION LOOP
# ============================================================

if __name__ == "__main__":

    # ========================================================
    # OPTIONAL MEMORY RESET
    # ========================================================

    RESET_MEMORY = True

    if RESET_MEMORY:

        location_memory.clear()

        save_memory()

    # ========================================================
    # MAIN USER LOOP
    # ========================================================

    while True:

        user_input = input(
            "\nEnter case report (type 'exit' to quit): "
        )

        # ====================================================
        # EXIT CONDITION
        # ====================================================

        if user_input == "exit":
            break

        # ====================================================
        # PARSE USER REPORT
        # ====================================================

        report = parse_case_report(user_input)

        # ====================================================
        # INVALID INPUT HANDLING
        # ====================================================

        if not report["diseases"]:

            print(
                "❌ No recognizable disease found. "
                "Please rephrase."
            )

            print(
                "Try inputs like: "
                "10 malaria, 5 dengue, loose motion cases"
            )

            continue

        # ====================================================
        # DISPLAY PARSED REPORT
        # ====================================================

        print("\n========== PARSED REPORT ==========")

        for disease_entry in report["diseases"]:

            print(
                f"{disease_entry['standard'].upper():<15} "
                f": {disease_entry['count']}"
            )

        print(
            f"LOCATION  : "
            f"{report['location'].upper() if report['location'] else 'NOT FOUND'}"
        )

        print("===================================")

                # ====================================================
        # LOCATION-BASED ANALYSIS
        # ====================================================

        if report["diseases"]:

            # =================================================
            # LOCATION AVAILABLE
            # =================================================

            if report["location"]:

                # =============================================
                # SAVE CASES INTO MEMORY
                # =============================================

                for disease_entry in report["diseases"]:

                    add_case(

                        report["location"],

                        {
                            "disease": disease_entry["standard"],
                            "count": disease_entry["count"]
                        }
                    )

                # =============================================
                # RETRIEVE LOCATION HISTORY
                # =============================================

                history = get_location_history(
                    report["location"]
                )

                # =============================================
                # RISK ANALYSIS
                # =============================================

                analysis = analyze_risk(history)

                print("\n========== RISK ANALYSIS ==========")

                print(
                    f"TOTAL CASES   : "
                    f"{analysis['total_cases']}"
                )

                print(
                    f"DISEASE TYPES : "
                    f"{analysis['num_diseases']}"
                )

                print(
                    f"WATERBORNE    : "
                    f"{analysis['risk']['waterborne']}"
                )

                print(
                    f"VECTORBORNE   : "
                    f"{analysis['risk']['vectorborne']}"
                )

                print(
                    f"GENERAL       : "
                    f"{analysis['risk']['general']}"
                )

                print(
                    f"RISK LEVEL    : "
                    f"{analysis['risk_level']}"
                )

                print("===================================")

                # =============================================
                # OPTIONAL MEMORY DISPLAY
                # =============================================

                while True:

                    choice = input(
                        "Show full village data? (y/n): "
                    ).strip().lower()

                    if choice in ["y", "n"]:
                        break

                    print(
                        "❗ Please enter 'y' or 'n' only."
                    )

                if choice == "y":

                    print_all_locations()

                # =============================================
                # GENERATE BASIC RESPONSE
                # =============================================

                response = generate_response(
                    report,
                    analysis
                )

                print(response)

            # =================================================
            # NO LOCATION FOUND
            # =================================================

            else:

                print(
                    "⚠ No location detected → "
                    "analysis based only on disease.\n"
                )

                total_cases = sum(

                    disease_entry["count"]

                    for disease_entry in report["diseases"]
                )

                # =============================================
                # FALLBACK ANALYSIS
                # =============================================

                analysis = {

                    "total_cases": total_cases,

                    "num_diseases": len(
                        report["diseases"]
                    ),

                    "risk": {

                        "waterborne": 0,
                        "vectorborne": 0,
                        "general": total_cases
                    },

                    "risk_level": "UNKNOWN"
                }

                response = generate_response(
                    report,
                    analysis
                )

                print(response)

            # =================================================
            # SENSOR-BASED ANALYSIS
            # =================================================

            sensor_data = get_sensor_by_location(
                report["location"]
            )

            # =================================================
            # FALLBACK SENSOR
            # =================================================
            # Used if no real sensor exists for location.
            # =================================================

            if not sensor_data:

                sensor_data = {

                    "location": report["location"],

                    "ph": 7,

                    "turbidity": 10
                }

            # =================================================
            # SENSOR DISEASE PREDICTION
            # =================================================

            sensor_report = sensor_to_report(
                sensor_data
            )

            sensor_diseases = sensor_report["diseases"]

            # =================================================
            # USER DISEASES
            # =================================================

            user_diseases = report["diseases"]

            # =================================================
            # DISEASE COMPARISON
            # =================================================

            comparison = compare_diseases(
                sensor_diseases,
                user_diseases
            )

            # =================================================
            # GENERATE COMPARISON INSIGHTS
            # =================================================

            messages = generate_comparison_insights(
                comparison
            )

            print("\n=== INTERPRETATION ===")

            for message in messages:
                print("-", message)

            # =================================================
            # AI ADVISORY SYSTEM
            # =================================================

            print("\n" + "=" * 35)

            print(" 🤖 AI MEDICAL ADVISORY SYSTEM")

            print("=" * 35)

            # =================================================
            # USER CAUSE INPUT LOOP
            # =================================================

            while True:

                cause_text = input(
                    "❓ Describe suspected cause "
                    "(or type 'unknown'): "
                ).strip().lower()

                if is_valid_cause(cause_text):
                    break

                print(
                    "⚠ Please enter a meaningful cause "
                    "or type 'idk' / 'unknown'."
                )

            print(
                "\n========== FULL MEDICAL PLAN =========="
            )

            # =================================================
            # SELECT IMPORTANT DISEASES
            # =================================================

            important_diseases = select_important_diseases(
                comparison
            )

            # =================================================
            # CAUSE DETECTION
            # =================================================

            user_cause = detect_cause_type(
                cause_text
            )

            system_cause = derive_cause_type(
                important_diseases
            )

            # =================================================
            # FINAL CAUSE FUSION
            # =================================================
            # System-derived causes are prioritized.
            # =================================================

            cause_type = system_cause or user_cause

            print(f"[*] User Cause: {user_cause}")

            print(f"[*] System Cause: {system_cause}")

            print(f"[*] Final Cause Used: {cause_type}")

            # =================================================
            # CONFLICT DETECTION
            # =================================================

            if system_cause and user_cause and system_cause != user_cause:

                print(
                    f"⚠ Conflict: user said "
                    f"{user_cause}, "
                    f"system suggests {system_cause}"
                )

            print(
                "[*] Searching WHO & CDC medical "
                "protocols... please wait..."
            )

            # =================================================
            # SPLIT USER/PREDICTED DISEASES
            # =================================================

            user_disease_set = set(

                comparison["matched"]
                + comparison["user_only"]
            )

            all_selected = set(
                important_diseases
            )

            predicted_diseases = list(
                all_selected - user_disease_set
            )

            user_disease_list = list(
                user_disease_set
            )

            # =================================================
            # BUILD RAG QUERY
            # =================================================

            query = build_query_from_analysis(

                user_disease_list,

                predicted_diseases,

                analysis
            )

            # =================================================
            # RUN RAG PIPELINE
            # =================================================

            answer, sources = run_rag_pipeline(

                query,

                cause_type=cause_type
            )

            # =================================================
            # FINAL AI RESPONSE
            # =================================================

            print(answer)

            print("=======================================\n")