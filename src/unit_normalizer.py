from typing import Optional, Tuple

# ------------------------------------
# Base conversions
# ------------------------------------
VOLUME_TO_ML = {
    "tsp": 5,
    "tbsp": 15,
    "cup": 240,
    "ml": 1,
    "l": 1000
}

WEIGHT_TO_G = {
    "g": 1,
    "kg": 1000,
    "lb": 453.6,
    "pinch": 0.5  # approx 0.5g
}

# Average weights for single items (grams)
AVERAGE_WEIGHTS = {
    "potato": 150,
    "onion": 100,
    "tomato": 100,
    "carrot": 100,
    "capsicum": 100,
    "egg": 50,
    "apple": 150,
    "banana": 120,
    "chili": 5,
    "green chili": 5,
    "red chili": 2,
    "clove": 0.1,
    "cardamom": 0.2,
    "almond": 1.2,
    "cashew": 1.5,
    "lemon": 50
}

# ------------------------------------
# Category inference (keyword-based)
# ------------------------------------
LIQUID_KEYWORDS = {
    "water", "milk", "oil", "juice", "curd", "yogurt",
    "broth", "stock", "cream", "vinegar", "syrup", "ghee",
    "soy", "sauce"
}

SOLID_KEYWORDS = {
    "salt", "sugar", "flour", "rice", "lentil", "dal", "moong", "urad", "chana", "toor",
    "spice", "powder", "seed", "leaf", "leaves", "clove", "cardamom", "cinnamon", "stick",
    "ginger", "garlic", "onion", "tomato", "potato", "carrot", "bean", "pea",
    "chili", "pepper", "turmeric", "paneer", "cheese", "chicken", "meat", "fish",
    "vegetable", "nut", "cashew", "almond", "bread", "corn", "mushroom", "soya", "besan",
    "wheat", "asafoetida", "fenugreek", "mustard"
}

# ------------------------------------
# Category inference
# ------------------------------------
def infer_category(name: str) -> str:
    name = name.lower()

    if any(k in name for k in LIQUID_KEYWORDS):
        return "liquid"

    # Default to solid for everything else (spices, veg, etc.)
    return "solid"


# ------------------------------------
# Core normalizer
# ------------------------------------
def normalize_quantity_unit(
    quantity: Optional[float],
    unit: Optional[str],
    ingredient_name: Optional[str] = ""
) -> Tuple[Optional[int], Optional[str], Optional[str]]:
    """
    Normalize quantities to:
    - grams (g) for solids
    - milliliters (ml) for liquids

    Returns:
      normalized_quantity,
      normalized_unit,
      conversion_note
    """

    if not ingredient_name:
        return None, None, None

    clean_name_lower = ingredient_name.lower()
    note = "no conversion applied"
    unit = unit.lower() if unit else None
    category = infer_category(ingredient_name)

    # 🔥 Special Handle: Common Pantry Items (often have no quantity)
    common_pantry = {
        "salt", "oil", "asafoetida", "hing", "curry leaves", "water", 
        "mustard seeds", "cumin seeds", "jeera", "pepper", "black pepper",
        "saffron", "soy", "butter", "ghee", "sugar", "turmeric"
    }
    is_common = any(c in clean_name_lower for c in common_pantry)

    # Skip conversion blocks if quantity is None
    if quantity is not None:
        # 1. Try Normalize Solids
        if category == "solid":
            if unit in WEIGHT_TO_G:
                g = round(quantity * WEIGHT_TO_G[unit], 2)
                return g, "g", f"{quantity} {unit} → {g} g"
            
            # Approximate volume to weight for solids (1 ml approx 1 g for rough estimate)
            if unit in VOLUME_TO_ML:
                 g = round(quantity * VOLUME_TO_ML[unit], 2)
                 return g, "g", f"{quantity} {unit} → {g} g (approx)"

        # 2. Try Normalize Liquids
        if category == "liquid":
            if unit in VOLUME_TO_ML:
                ml = round(quantity * VOLUME_TO_ML[unit], 2)
                return ml, "ml", f"{quantity} {unit} → {ml} ml"
            
            # Approximate weight to volume (1 g approx 1 ml)
            if unit in WEIGHT_TO_G:
                ml = round(quantity * WEIGHT_TO_G[unit], 2)
                return ml, "ml", f"{quantity} {unit} → {ml} ml (approx)"
                
        # 3. Unit-less counts (e.g. 2 potatoes)
        if unit is None and category == "solid":
            # Check average weights
            if clean_name_lower in AVERAGE_WEIGHTS:
                avg = AVERAGE_WEIGHTS[clean_name_lower]
                g = round(quantity * avg, 2)
                return g, "g", f"{quantity} x {clean_name_lower} (~{avg}g) → {g} g"

    # 4. Fallback: Ensure no null quantity/unit for solids/liquids (except exemptions)
    # 🔥 Special Handling: User requested no nulls for solids (g) and liquids (ml)
    exemptions = {"saffron", "hing", "asafoetida"}
    is_exempt = any(ex in clean_name_lower for ex in exemptions)

    if not is_exempt:
        if quantity is None:
            quantity = 1.0
        if unit is None:
            unit = "g" if category == "solid" else "ml"
        
        if note == "no conversion applied":
            note = f"Default quantity assigned: {quantity} {unit}"

    # 🔥 Special Handling for Common Ingredients (Ensure info is never empty)
    if note == "no conversion applied" or not note:
        if is_common:
             note = "Adjusted to taste / standard requirement"
        else:
             note = "Quantity as per recipe requirement / instructions"

    return quantity, unit, note
