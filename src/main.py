import json
import os
import re

from ingredient_parser import parse_ingredient
from instruction_cleaner import clean_instructions, looks_like_instruction
from time_normalizer import normalize_times
from unit_normalizer import normalize_quantity_unit

from db import get_connection
from db_insert import (
    insert_recipe,
    insert_recipe_ingredients,
    insert_meal,
    insert_meal_recipe,
    insert_meal_ingredients
)

# ------------------------------------
# FINAL INGREDIENT VALIDATOR
# ------------------------------------
def final_is_valid_ingredient(name: str) -> bool:
    if not name:
        return False

    # Reject instruction-like phrases
    if re.match(r'^(add|serve|make|mix|stir|cook|boil|fry|pour|to)\b', name):
        return False

    # Too long → not a noun
    if len(name.split()) > 3:
        return False

    return True


# ------------------------------------
# 🔧 FINAL SANITATION LAYER (AUTHORITATIVE)
# ------------------------------------
def final_cleanup_ingredient_name(name: str) -> str:
    """
    Absolute final cleanup.
    Guarantees ONLY clean ingredient nouns.
    """
    if not name:
        return ""

    name = name.lower()

    # 1️⃣ Remove ALL symbols anywhere
    name = re.sub(r'[\/,\-–—]+', ' ', name)

    # 2️⃣ Remove quantity / size words (dynamic)
    name = re.sub(
        r'\b(a\s+few|few|a\s+pinch|pinch|a\s+handful|handful|'
        r'small|medium|large|medium\s+sized|large\s+sized)\b',
        '',
        name
    )

    # 3️⃣ Remove preparation/state words
    name = re.sub(
        r'\b(whole|fresh|dried|raw|ripe|peeled|deseeded|'
        r'chopped|cubed|sliced|minced|grated|crushed|boiled|fine|finely)\b',
        '',
        name
    )

    # 4️⃣ Remove connectors
    name = re.sub(r'\b(and|or)\b', '', name)

    # 5️⃣ Normalize plurals safely - REDUNDANT with rapidfuzz standard list
    # name = re.sub(r'ies\b', 'y', name)
    # name = re.sub(r'es\b', '', name)
    # name = re.sub(r's\b', '', name)

    # 6️⃣ Collapse duplicate words
    tokens = []
    for w in name.split():
        if w not in tokens:
            tokens.append(w)
    name = " ".join(tokens)

    # 7️⃣ Final whitespace cleanup
    name = re.sub(r'\s+', ' ', name).strip()

    return name


# ------------------------------------
# LOAD DATASET
# ------------------------------------
def load_dataset():
    base_dir = os.path.dirname(__file__)
    with open(os.path.join(base_dir, "..", "data", "recipes.json")) as f:
        return json.load(f)


# ------------------------------------
# MEAL TYPE INFERENCE
# ------------------------------------
def infer_meal_type(recipe_name: str) -> str:
    name = recipe_name.lower()
    if any(k in name for k in ["dosa", "idli", "poha", "upma"]):
        return "breakfast"
    if any(k in name for k in ["rice", "biryani", "pulao"]):
        return "lunch"
    return "dinner"


# ------------------------------------
# PROCESS SINGLE RECIPE
# ------------------------------------
def process_recipe(recipe: dict) -> dict:
    parsed_ingredients = []

    raw_ingredients = json.loads(recipe.get("ingredients_json", "[]"))

    for item in raw_ingredients:
        raw_name = item.get("name", "").lower().strip()
        raw_qty = item.get("quantity", "").replace("▢", "").strip()

        if not raw_name or looks_like_instruction(raw_name):
            continue

        parsed = parse_ingredient(f"{raw_qty} {raw_name}".strip())

        # 🔥 FINAL CLEANUP
        clean_name = final_cleanup_ingredient_name(
            parsed.get("ingredient_name", "")
        )

        if not final_is_valid_ingredient(clean_name):
            continue

        parsed["ingredient_name"] = clean_name

        # Unit normalization
        qty, unit, note = normalize_quantity_unit(
            parsed.get("quantity"),
            parsed.get("unit"),
            clean_name
        )

        parsed["quantity"] = qty
        parsed["unit"] = unit

        if note:
            parsed.setdefault("ingredient_info", {})
            parsed["ingredient_info"]["unit_conversion"] = note

        parsed_ingredients.append(parsed)

    instructions = clean_instructions(
        json.loads(recipe.get("prep_steps", "[]")) +
        json.loads(recipe.get("cook_steps", "[]"))
    )

    return {
        "recipe_name": recipe.get("recipe_name"),
        "ingredients": parsed_ingredients,
        "instructions": instructions,
        **normalize_times(recipe)
    }


# ------------------------------------
# MAIN PIPELINE
# ------------------------------------
def main():
    data = load_dataset()
    conn = get_connection()
    cur = conn.cursor()
    seen = set()

    for recipe in data:
        name = recipe.get("recipe_name")
        if not name or name in seen:
            continue
        seen.add(name)

        structured = process_recipe(recipe)
        recipe_id = insert_recipe(cur, structured)

        insert_recipe_ingredients(cur, recipe_id, structured["ingredients"])

        meal_id = insert_meal(cur, {
            "name": f"{name} Meal",
            "meal_type": infer_meal_type(name),
            "total_time_minutes": structured["total_time_minutes"]
        })

        insert_meal_recipe(cur, meal_id, recipe_id, name)
        insert_meal_ingredients(cur, meal_id, structured["ingredients"])

        print(f"Inserted: {name}")

    conn.commit()
    cur.close()
    conn.close()


if __name__ == "__main__":
    main()
