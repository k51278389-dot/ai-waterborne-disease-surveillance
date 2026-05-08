from location_memory_manager import add_case, get_location_history

add_case("Narkul Village", {
    "disease": "cholera",
    "count": 2,
    "cause": "dirty water"
})

add_case("Narkul Village", {
    "disease": "malaria",
    "count": 1,
    "cause": "stagnant water"
})

history = get_location_history("Narkul Village")

print(history)

















