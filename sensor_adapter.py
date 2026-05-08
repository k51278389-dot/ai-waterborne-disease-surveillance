import json

with open("sensor_logs.json") as f:
    sensor_logs = json.load(f)
WATERBORNE_PRIORITY = {
    "primary": ["cholera", "typhoid", "diarrhea", "dysentery", "gastroenteritis"],
    "secondary": ["amoebiasis", "giardia", "e coli", "salmonella"],
    "low": ["hepatitis a", "hepatitis e", "cryptosporidium", "leptospirosis"]
}
VECTOR_PRIORITY = {
    "primary": ["malaria", "dengue"],
    "secondary": ["chikungunya"],
    "low": ["zika", "west nile virus", "yellow fever","japanese encephalitis"]
}
GENERAL_PRIORITY = {
    "primary": ["fever", "viral fever","flu"],
    "low": ["cold","cough","skin infection","eye infection","respiratory infection","weakness","body pain"]
}
def sensor_to_report(sensor):
    location = sensor.get("location")
    turbidity = sensor.get("turbidity", 0)
    ph = sensor.get("ph", 7)

    disease_map = {}

    # -----------------------------
    # HELPER FUNCTION
    # -----------------------------
    def apply_weights( group, weight):
        for d in group:
            disease_map[d] = disease_map.get(d, 0) + weight
    # -----------------------------
    # WATERBORNE (PRIMARY DRIVER)
    # -----------------------------
    if turbidity > 40:
        apply_weights(WATERBORNE_PRIORITY["primary"][:3], 6)
        apply_weights(WATERBORNE_PRIORITY["secondary"][:2], 3)
        apply_weights(WATERBORNE_PRIORITY["low"][:1], 1)

    elif turbidity > 20:
        apply_weights(WATERBORNE_PRIORITY["primary"][:3], 4)
        apply_weights(WATERBORNE_PRIORITY["secondary"][:2], 2)
        apply_weights(WATERBORNE_PRIORITY["low"][:1], 1)

    # -----------------------------
    # pH EFFECT (AMPLIFIER)
    # -----------------------------
    if ph < 6 or ph > 8.5:
        apply_weights(["gastroenteritis", "diarrhea"], 3)

    # -----------------------------
    # VECTORBORNE (INDIRECT)
    # -----------------------------
    if turbidity > 50:
        apply_weights(VECTOR_PRIORITY["primary"], 3)
        apply_weights(VECTOR_PRIORITY["secondary"], 2)
        apply_weights(VECTOR_PRIORITY["low"][:2], 1)

    # -----------------------------
    # GENERAL (WEAK SIGNAL)
    # -----------------------------
    if 20 < turbidity <= 30:
        apply_weights(GENERAL_PRIORITY["primary"][:2], 2)
        apply_weights(GENERAL_PRIORITY["low"][:1], 1)

        
    diseases = [
        {"standard": d, "count": c}
        for d, c in disease_map.items()
    ]

    return {
    "location": location,
    "sensor": {
        "ph": ph,
        "turbidity": turbidity
    },
    "diseases": diseases   
}

for sensor in sensor_logs:
    report = sensor_to_report(sensor)

    if not report["diseases"]:
        continue








