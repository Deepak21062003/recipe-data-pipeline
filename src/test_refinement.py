import re
from main import final_cleanup_ingredient_name
from unit_normalizer import normalize_quantity_unit

def test_scaling_removal():
    test_cases = [
        ("onion can be scaled", "onion"),
        ("tomato can be scaled", "tomato"),
        ("salt can be scaled", "salt"),
        ("chili.", "chili")
    ]
    for input_name, expected in test_cases:
        result = final_cleanup_ingredient_name(input_name)
        assert result == expected, f"Failed scaling removal: {input_name} -> {result}"
    print("✅ Scaling removal test passed!")

def test_common_ingredient_info():
    test_cases = [
        # name, input_qty, expected_qty, expected_unit, expected_note
        ("salt", None, 1.0, "g", "Default quantity assigned: 1.0 g"),
        ("oil", None, 1.0, "ml", "Default quantity assigned: 1.0 ml"),
        ("saffron", None, None, None, "Adjusted to taste / standard requirement"),
        ("hing", None, None, None, "Adjusted to taste / standard requirement"),
        ("asafoetida", None, None, None, "Adjusted to taste / standard requirement"),
        ("curry leaves", None, None, None, "Adjusted to taste / standard requirement"),
        ("ginger", None, 1.0, "g", "Default quantity assigned: 1.0 g"),
        ("water", None, 1.0, "ml", "Default quantity assigned: 1.0 ml"),
        ("fenugreek", None, 1.0, "g", "Default quantity assigned: 1.0 g"),
        ("soy", None, 1.0, "ml", "Default quantity assigned: 1.0 ml")
    ]
    
    for name, qty, exp_qty, exp_unit, exp_note in test_cases:
        res_qty, res_unit, res_note = normalize_quantity_unit(qty, None, name)
        assert res_qty == exp_qty, f"Failed QTY for {name}: Expected {exp_qty}, got {res_qty}"
        assert res_unit == exp_unit, f"Failed UNIT for {name}: Expected {exp_unit}, got {res_unit}"
        assert exp_note in res_note, f"Failed NOTE for {name}: Expected '{exp_note}' to be in '{res_note}'"
            
    print("✅ Null quantity/unit elimination test passed!")

if __name__ == "__main__":
    test_scaling_removal()
    test_common_ingredient_info()
