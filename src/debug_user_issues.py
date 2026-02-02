from unit_normalizer import normalize_quantity_unit
from ingredient_parser import parse_ingredient

test_inputs = [
    "1 tsp fenugreek",
    "2 potatoes",
    "1 tsp mustard",
    "curry leaves",
    "4 to 5 dried red chilies",
    "1 pinch asafoetida",
    "1 cup chopped onion",
    "1/2 cup tomato",
    "1 carrot",
    "salt",
]

print(f"{'Input':<30} | {'Name':<20} | {'Qty':<5} | {'Unit':<10} | {'Norm Qty':<10} | {'Norm Unit':<10}")
print("-" * 100)

for text in test_inputs:
    p = parse_ingredient(text)
    name = p["ingredient_name"]
    qty = p["quantity"]
    unit = p["unit"]
    
    n_qty, n_unit, note = normalize_quantity_unit(qty, unit, name)
    
    # Handle None for printing
    d_qty = qty if qty is not None else "None"
    d_unit = unit if unit is not None else "None"
    dn_qty = n_qty if n_qty is not None else "None"
    dn_unit = n_unit if n_unit is not None else "None"
    
    print(f"{text:<30} | {name:<20} | {d_qty:<5} | {d_unit:<10} | {dn_qty:<10} | {dn_unit:<10}")
