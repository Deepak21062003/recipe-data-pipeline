from main import final_cleanup_ingredient_name
from unit_normalizer import normalize_quantity_unit

def test_noise_removal():
    test_cases = [
        ("onion can be scaled", "onion"),
        (".", ""),
        ("▢", ""),
        ("-", ""),
        ("fav brand of instant coffee", "instant coffee"),
        ("instant coffee powder or granules", "instant coffee powder")
    ]
    for input_name, expected in test_cases:
        result = final_cleanup_ingredient_name(input_name)
        assert result == expected, f"Failed noise removal: '{input_name}' -> '{result}' (expected '{expected}')"
    print("✅ Noise removal test passed!")

def test_common_ingredient_info():
    test_cases = [
        ("salt", None, "Adjusted to taste / standard requirement"),
        ("oil", None, "Adjusted to taste / standard requirement"),
        ("saffron", None, "Adjusted to taste / standard requirement"),
        ("soy", None, "Adjusted to taste / standard requirement"),
        ("butter", None, "Adjusted to taste / standard requirement"),
        ("ghee", None, "Adjusted to taste / standard requirement"),
        ("bhindi", None, "Quantity as per recipe requirement / instructions"),
        ("okra", None, "Quantity as per recipe requirement / instructions"),
        ("carrot", None, "Quantity as per recipe requirement / instructions")
    ]
    
    for name, qty, expected_note in test_cases:
        _, _, note = normalize_quantity_unit(qty, None, name)
        assert note == expected_note, f"Failed for {name}: Expected '{expected_note}', got '{note}'"
            
    print("✅ Global fallback and pantry info test passed!")

if __name__ == "__main__":
    test_noise_removal()
    test_common_ingredient_info()
