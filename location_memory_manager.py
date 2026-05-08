import json
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FILE_NAME = os.path.join(BASE_DIR, "memory.json")

def load_memory():
    if os.path.exists(FILE_NAME):
        try:
            with open(FILE_NAME, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            print(f"[WARNING] Could not load memory: {e}")
            return {}
    return {}


def save_memory():
    with open(FILE_NAME, "w", encoding="utf-8") as f:
        json.dump(location_memory, f, indent=4)


# =========================================
# Location Memory Storage
# =========================================

location_memory = load_memory()


# =========================================
# Create Location if Missing
# =========================================
def create_location_if_missing(location):
    if location not in location_memory:
        location_memory[location] = {}


# =========================================
# Add New Case
# =========================================

def add_case(location, case_data):
    create_location_if_missing(location)

    disease = case_data["disease"]
    count = case_data["count"]

    if disease in location_memory[location]:
        location_memory[location][disease] += count
    else:
        location_memory[location][disease] = count

    save_memory()
# =========================================
# Get Location History
# =========================================
def get_location_history(location):
    create_location_if_missing(location)
    return location_memory[location]


# existing code...

def print_all_locations():
    print("\n========== ALL VILLAGE DATA ==========")

    sorted_locations = sorted(
        location_memory.items(),
        key=lambda x: sum(x[1].values()),
        reverse=True
    )

    for location, diseases in sorted_locations:
        print(f"\n{location.upper()}")

        sorted_diseases = sorted(
            diseases.items(),
            key=lambda x: x[1],
            reverse=True
        )

        for disease, count in sorted_diseases:
            print(f"  - {disease.upper():<10} : {count}")

    print("\n======================================")