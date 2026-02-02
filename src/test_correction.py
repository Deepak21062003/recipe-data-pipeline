from ingredient_parser import clean_ingredient_name

test_cases = [
    ("chiken", "chicken"),
    ("tumeric", "turmeric"),
    ("onions", "onion"),
    ("tomatoes", "tomato"),
    ("garlics", "garlic"),
    ("gigner", "ginger"),
    ("potatos", "potato"),
    ("salt", "salt"),
    ("totally_unknown_ingredient", "totally_unknown_ingredient"), # Should remain same or close if strictly matching, but here if score < 90 it stays same
    ("chilli", "chili"),
]

print("Running verification tests...")
for input_str, expected in test_cases:
    result = clean_ingredient_name(input_str)
    status = "✅" if result == expected else f"❌ (Got: {result})"
    print(f"{status} Input: '{input_str}' -> Expected: '{expected}'")

print("\nDone.")
