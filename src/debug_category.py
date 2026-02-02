from unit_normalizer import normalize_quantity_unit, infer_category

ingredients = [
    ("coriander", 0.25, "cup"),
    ("cumin", 1.0, "tsp"),
    ("turmeric", 1.25, "g"),
    ("clove", 0.4, "g"),
    ("cardamom", 0.6, "g"),
    ("water", 1, "cup")
]

print(f"{'Name':<15} | {'Category':<10} | {'Input':<15} | {'Output':<15}")
print("-" * 60)

for name, qty, unit in ingredients:
    cat = infer_category(name)
    n_qty, n_unit, note = normalize_quantity_unit(qty, unit, name)
    print(f"{name:<15} | {cat:<10} | {qty} {unit:<8} | {n_qty} {n_unit}")
