from main import final_cleanup_ingredient_name
from unit_normalizer import normalize_quantity_unit

def test_scaling_removal():
    test_cases = [
        ("onion can be scaled", "onion"),
        ("tomato can be scaled", "tomato"),
        ("salt can be scaled", "salt")
    ]
    for input_name, expected in test_cases:
        result = final_cleanup_ingredient_name(input_name)
        assert result == expected, f"Failed scaling removal: {input_name} -> {result}"
    print("✅ Scaling removal test passed!")

def test_common_ingredient_info():
    test_cases = [
        ("salt", None),
        ("oil", None),
        ("asafoetida", None),
        ("hing", None),
        ("curry leaves", None),
        ("water", 1),
        ("mustard seeds", None),
        ("black pepper", None)
    ]
    
    for name, qty in test_cases:
        _, _, note = normalize_quantity_unit(qty, None, name)
        
        common_keywords = [
            "salt", "oil", "asafoetida", "hing", "curry leaves", 
            "water", "mustard seeds", "black pepper"
        ]
        if any(c in name for c in common_keywords):
            assert note == "Adjusted to taste / standard requirement", f"Failed for {name}: {note}"
            
    print("✅ Common ingredient info test passed!")

if __name__ == "__main__":
    test_scaling_removal()
    test_common_ingredient_info()
