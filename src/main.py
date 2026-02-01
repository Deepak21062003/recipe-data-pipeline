import json
import os
import re

from ingredient_parser import parse_ingredient
from instruction_cleaner import clean_instructions
from time_normalizer import normalize_times
from db import get_connection
from db_insert import (
    insert_recipe,
    insert_recipe_ingredients,
    insert_meal,
    insert_meal_recipe,
    insert_meal_ingredients
)

# ------------------------------------
# CONFIG
# ------------------------------------
GENERIC_BAD_TOKENS = {
    "powder", "masala", "leaves", "leaf",
    "nut", "nuts"
}

INSTRUCTION_VERBS = {
    "add", "pour", "serve", "make", "now", "then",
    "mix", "stir", "cook", "boil", "fry",
    "heat", "place", "put", "adjust", "garnish",
    "sprinkle", "knead", "cover"
}

SPELLING_FIXES = {
    "tomatoe": "tomato",
    "chilie": "chili",
    "chillie": "chili",
    "chillies": "chillies",
    "potatoe": "potato",
    "coriander leave": "coriander leaves",
    "mint leave": "mint leaves",
    "curry leave": "curry leaves",
    "leaves curry leave": "curry leaves",
    "garlic clove": "garlic cloves",
    "green chilie": "green chili",
    "red chilie": "red chili",
}
PROCESS_VERBS = {
    "blend", "blending",
    "increase", "decrease",
    "remember", "adjust",
    "check", "taste",
    "serve", "garnish"
}


# ------------------------------------
# LOAD DATASET
# ------------------------------------
def load_dataset():
    base_dir = os.path.dirname(__file__)
    data_path = os.path.join(base_dir, "..", "data", "recipes.json")
    with open(data_path, "r") as f:
        data = json.load(f)

    if not isinstance(data, list):
        raise ValueError("Expected dataset to be a list of recipes")

    return data


# ------------------------------------
# MEAL TYPE INFERENCE
# ------------------------------------
def infer_meal_type(recipe_name: str) -> str:
    name = recipe_name.lower()

    breakfast_keywords = [
        "dosa", "idli", "uttapam", "pesarattu",
        "pongal", "poha", "upma", "sevai",
        "idiyappam", "appam", "puttu", "vada",
        "paratha", "poori", "bhatura", "sandwich"
    ]

    lunch_keywords = [
        "rice", "biryani", "pulao", "khichdi", "curd rice"
    ]

    if any(k in name for k in breakfast_keywords):
        return "breakfast"

    if any(k in name for k in lunch_keywords):
        return "lunch"

    return "dinner"


# ------------------------------------
# HARD INSTRUCTION LINE DETECTOR
# ------------------------------------
def is_instruction_line(text: str) -> bool:
    """
    Returns True if the text is a cooking / instruction sentence
    and should NEVER be treated as an ingredient.
    """
    if not text:
        return True

    text = text.strip().lower()

    # Starts with "to ..."
    if text.startswith("to "):
        return True

    # Starts with cooking verbs (including gerunds)
    if re.match(
        r'^(add|adding|pour|serve|make|making|now|then|mix|mixing|'
        r'stir|stirring|cook|cooking|boil|boiling|fry|frying|'
        r'heat|heating|place|placing|put|putting|adjust|adjusting|'
        r'garnish|garnishing|sprinkle|sprinkling|knead|kneading|'
        r'cover|covering)\b',
        text
    ):
        return True

    # Contains full instruction sentence markers
    if re.search(
        r'\b(add|adding|pour|serve|make|cook|boil|fry|stir|knead|'
        r'cover|heat|mix)\b',
        text
    ) and len(text.split()) > 3:
        return True

    return False


# ------------------------------------
# FINAL INGREDIENT VALIDATOR (POST PARSE)
# ------------------------------------
def final_is_valid_ingredient(name: str) -> bool:
    """
    Final validation AFTER parse_ingredient().
    If this returns False, the row MUST NOT be inserted.
    """
    if not name:
        return False

    name = name.strip().lower()
    for word in PROCESS_VERBS:
        if word in name:
            return False

    # Starts with instruction verbs or helper words
    if re.match(
        r'^(add|adding|pour|serve|make|making|now|then|to|mix|mixing|'
        r'stir|stirring|cook|cooking|boil|boiling|fry|frying|'
        r'heat|heating|place|placing|put|putting|adjust|adjusting|'
        r'garnish|garnishing|sprinkle|sprinkling|knead|kneading|'
        r'cover|covering)\b',
        name
    ):
        return False

    # Contains verbs → sentence fragment
    if re.search(
        r'\b(add|adding|pour|serve|make|cook|boil|fry|stir|knead|'
        r'cover|heat|mix)\b',
        name
    ):
        return False

    # Too long → not an ingredient noun
    if len(name.split()) > 4:
        return False

    return True

# ------------------------------------
# SPLIT INGREDIENT + NOTES
# ------------------------------------
def split_ingredient_and_notes(text: str):
    text = text.lower().strip()
    notes = []

    # ✅ NEW FIX (additive, safe)
    # capture informal quantity / size phrases as notes
    qty_match = re.match(
    r'^('
    r'a\s+handful|handful|'
    r'a\s+pinch|pinch|'
    r'a\s+dash|dash|'
    r'a\s+few|few|'
    r'a\s+few\s+strands|few\s+strands|'
    r'\d+\s*inch\s+piece|inch\s+piece'
    r')'
    r'(?:\s*,?\s*(grated|crushed|chopped))?'
    r'\s*',
    text
)

    if qty_match:
        notes.append(qty_match.group(1))
        text = text[qty_match.end():].strip()

    # then remove symbols
    text = re.sub(r'^[\s,\/\-–—]+', '', text)

    # then helper words
    text = re.sub(r'^(to|and|with|a|an|of)\s+', '', text)

    # then for topping/serving/garnish
    for_match = re.match(
        r'^for\s+(topping|serving|garnish)\s+(.*)',
        text
    )
    if for_match:
        notes.append(f"for {for_match.group(1)}")
        text = for_match.group(2).strip()

    if ':' in text:
        left, right = text.split(':', 1)
        text = left.strip()
        notes.append(right.strip())

    paren_match = re.search(r'\((.*)', text)
    if paren_match:
        notes.append(paren_match.group(1).strip())
        text = text[:paren_match.start()].strip()

    omit_match = re.match(r'^omit\s+([a-z\s]+)', text)
    if omit_match:
        ingredient = omit_match.group(1).strip()
        notes.append(text)
        return ingredient, " ".join(notes)

    if " or " in text:
        parts = [p.strip() for p in text.split(" or ") if p.strip()]
        text = parts[0]
        if len(parts) > 1:
            notes.append("or " + " ".join(parts[1:]))

    text = re.sub(r'[()]', '', text)
    text = re.sub(r'[.,]+$', '', text)
    text = re.sub(r'\s+', ' ', text).strip()

    return text, " ".join(notes) if notes else None




# ------------------------------------
# INGREDIENT NAME NORMALIZATION
# ------------------------------------
def normalize_ingredient_name(name: str) -> str:
    name = name.lower().strip()

    name = re.sub(r'[\/,\-–—]+', ' ', name)

    name = re.sub(
        r'\b(roughly|finely|coarsely|chopped|cubed|sliced|minced|'
        r'crushed|grated|shredded|ground|juiced|soaked|'
        r'boiled|boiling|whole|broken|fresh|raw|optional)\b',
        '',
        name
    )

    name = re.sub(r'\s+', ' ', name).strip()

    if not name:
        return ""
    name = SPELLING_FIXES.get(name, name)

    tokens = name.split()
    if all(tok in GENERIC_BAD_TOKENS for tok in tokens):
        return ""

    return name


# ------------------------------------
# PROCESS SINGLE RECIPE (FINAL)
# ------------------------------------
def process_recipe(recipe: dict) -> dict:
    raw_ingredients = json.loads(recipe.get("ingredients_json", "[]"))
    parsed_ingredients = []

    for item in raw_ingredients:
        raw_qty = item.get("quantity", "").replace("▢", "").strip()
        raw_name = item.get("name", "").strip().lower()

        if not raw_name:
            continue

        # 🚫 HARD STOP — STEP SENTENCES NEVER ENTER PIPELINE
        if is_instruction_line(raw_name):
            continue

        clean_name, notes = split_ingredient_and_notes(raw_name)
        if not clean_name:
            continue

        clean_name = normalize_ingredient_name(clean_name)
        if not clean_name:
            continue

        raw_text = f"{raw_qty} {clean_name}".strip()
        parsed = parse_ingredient(raw_text)

        # 🚫 FINAL POST-PARSE VALIDATION (CRITICAL)
        parsed_name = parsed.get("ingredient_name", "").lower()
        if not final_is_valid_ingredient(parsed_name):
            continue

        if notes:
            parsed.setdefault("ingredient_info", {})
            parsed["ingredient_info"]["notes"] = notes

        parsed_ingredients.append(parsed)

    prep_steps = json.loads(recipe.get("prep_steps", "[]"))
    cook_steps = json.loads(recipe.get("cook_steps", "[]"))
    instructions = clean_instructions(prep_steps + cook_steps)

    time_info = normalize_times(recipe)

    return {
        "recipe_name": recipe.get("recipe_name"),
        "ingredients": parsed_ingredients,
        "instructions": instructions,
        **time_info
    }


# ------------------------------------
# MAIN PIPELINE
# ------------------------------------
def main():
    data = load_dataset()

    conn = get_connection()
    cur = conn.cursor()
    seen_recipes = set()

    for recipe in data:
        recipe_name = recipe.get("recipe_name")
        if not recipe_name or recipe_name in seen_recipes:
            continue
        seen_recipes.add(recipe_name)

        structured = process_recipe(recipe)
        recipe_id = insert_recipe(cur, structured)
        insert_recipe_ingredients(cur, recipe_id, structured["ingredients"])

        meal = {
            "name": f"{structured['recipe_name']} Meal",
            "meal_type": infer_meal_type(structured["recipe_name"]),
            "total_time_minutes": structured["total_time_minutes"]
        }

        meal_id = insert_meal(cur, meal)
        insert_meal_recipe(cur, meal_id, recipe_id, structured["recipe_name"])
        insert_meal_ingredients(cur, meal_id, structured["ingredients"])

        print(f"Inserted: {structured['recipe_name']}")

    conn.commit()
    cur.close()
    conn.close()


if __name__ == "__main__":
    main()
