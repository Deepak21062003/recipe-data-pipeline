from rapidfuzz import process, fuzz
from standard_ingredients import STANDARD_INGREDIENTS

test_cases = [
    ("green chilli", "green chili"),
    ("fresh green chilli", "green chili"),
]

print("Checking scores...")
for input_str, target in test_cases:
    match = process.extractOne(input_str, STANDARD_INGREDIENTS, scorer=fuzz.WRatio)
    print(f"Input: '{input_str}' -> Best Match: {match}")
