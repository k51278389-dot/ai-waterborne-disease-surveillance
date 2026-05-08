# ============================================================
# LOCATION MEMORY MANAGER
# ============================================================
#
# This file handles persistent outbreak memory storage.
#
# Responsibilities:
# - loading saved outbreak memory
# - saving outbreak memory
# - adding new disease cases
# - retrieving village history
# - printing village outbreak summaries
#
# Data is stored inside:
# memory.json
# ============================================================

import json
import os


# ============================================================
# FILE CONFIGURATION
# ============================================================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

FILE_NAME = os.path.join(BASE_DIR, "memory.json")


# ============================================================
# LOAD MEMORY
# ============================================================
#
# Loads saved outbreak data from disk.
#
# Safe loading:
# - handles missing file
# - handles corrupted JSON
# ============================================================

def load_memory():

    if os.path.exists(FILE_NAME):

        try:
            with open(FILE_NAME, "r", encoding="utf-8") as file:
                return json.load(file)

        except (json.JSONDecodeError, IOError) as error:

            print(f"[WARNING] Could not load memory: {error}")

            return {}

    return {}


# ============================================================
# SAVE MEMORY
# ============================================================
#
# Saves current outbreak memory into memory.json
# ============================================================

def save_memory():

    with open(FILE_NAME, "w", encoding="utf-8") as file:

        json.dump(
            location_memory,
            file,
            indent=4
        )


# ============================================================
# GLOBAL LOCATION MEMORY
# ============================================================
#
# Structure:
#
# {
#     "Umden": {
#         "cholera": 5
#     }
# }
# ============================================================

location_memory = load_memory()


# ============================================================
# CREATE LOCATION IF MISSING
# ============================================================
#
# Ensures every location exists before updating.
# ============================================================

def create_location_if_missing(location):

    if location not in location_memory:
        location_memory[location] = {}


# ============================================================
# ADD NEW CASE
# ============================================================
#
# Adds disease counts into location history.
#
# Example:
#
# add_case(
#     "Umden",
#     {
#         "disease": "cholera",
#         "count": 5
#     }
# )
# ============================================================

def add_case(location, case_data):

    create_location_if_missing(location)

    disease_name = case_data["disease"]

    case_count = case_data["count"]

    # Update existing disease count
    if disease_name in location_memory[location]:

        location_memory[location][disease_name] += case_count

    # Create new disease entry
    else:
        location_memory[location][disease_name] = case_count

    # Persist updated memory
    save_memory()


# ============================================================
# GET LOCATION HISTORY
# ============================================================
#
# Returns all disease data for a village/location.
# ============================================================

def get_location_history(location):

    create_location_if_missing(location)

    return location_memory[location]


# ============================================================
# PRINT ALL STORED LOCATIONS
# ============================================================
#
# Displays:
# - villages
# - diseases
# - case counts
#
# Villages are sorted by total outbreak severity.
# ============================================================

def print_all_locations():

    print("\n========== ALL VILLAGE DATA ==========")

    # Sort villages by total cases
    sorted_locations = sorted(

        location_memory.items(),

        key=lambda location_entry: sum(
            location_entry[1].values()
        ),

        reverse=True
    )

    for location_name, diseases in sorted_locations:

        print(f"\n{location_name.upper()}")

        # Sort diseases by case count
        sorted_diseases = sorted(

            diseases.items(),

            key=lambda disease_entry: disease_entry[1],

            reverse=True
        )

        for disease_name, case_count in sorted_diseases:

            print(
                f"  - {disease_name.upper():<10} : {case_count}"
            )

    print("\n======================================")