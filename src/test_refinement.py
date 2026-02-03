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
        ("salt", "no conversion applied"), # Before fix this might have been default
        ("oil", "no conversion applied"),
        ("asafoetida", "no conversion applied"),
        ("hing", "no conversion applied"),
        ("potato", "no conversion applied")
    ]
    
    # We want to see if our fix overrides "no conversion applied" for common ones
    for name, _ in test_cases:
        qty, unit, note = normalize_quantity_unit(None, None, name)
        # Note: it returns None if quantity is None in the current implementation of normalize_quantity_unit
        # Let's check with a quantity
        qty, unit, note = normalize_quantity_unit(1, None, name)
        
        if any(c in name for c in ["salt", "oil", "asafoetida", "hing"]):
            assert note == "Adjusted to taste / standard requirement", f"Failed for {name}: {note}"
        else:
            # potato with no unit and no average weight check (if name not in list)
            pass 
            
    print("✅ Common ingredient info test passed!")

if __name__ == "__main__":
    test_scaling_removal()
    test_common_ingredient_info()
