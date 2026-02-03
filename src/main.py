import json
import os
import re

from ingredient_parser import parse_ingredient
from instruction_cleaner import clean_instructions, looks_like_instruction
from time_normalizer import normalize_times
from unit_normalizer import normalize_quantity_unit

from rapidfuzz import process, fuzz
from standard_ingredients import STANDARD_INGREDIENTS
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
    if re.match(r'^(add|serve|make|mix|stir|cook|boil|fry|pour|to|when|in|heat|after|while|let|once|easily|halve|roughly|finely)\b', name):
        return False

    # Too long → not a noun
    if len(name.split()) > 3:
        return False
        
    # Block ambiguous/incomplete words
    if name in {"baking", "recipe", "recipes", "mix", "powder"}:
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

    # 1️⃣ Remove "recipe" or "recipes" noise
    name = re.sub(r'\b(recipes?)\b', '', name)

    # 1.1️⃣ Remove "can be scaled" noise
    name = re.sub(r'\bcan\s+be\s+scaled\b', '', name)

    # 2️⃣ Remove leading articles
    name = re.sub(r'^(a|an|the)\s+', '', name)

    # 3️⃣ Remove ALL symbols anywhere (enhanced)
    # Put hyphen at the end to avoid creating a range (comma to en-dash swallowed letters!)
    name = re.sub(r'[\\/,–—\(\)\[\]\{\}-]+', ' ', name)

    # 4️⃣ Remove quantity / size words (dynamic)
    name = re.sub(
        r'\b(a\s+few|few|a\s+pinch|pinch|a\s+handful|handful|'
        r'small|medium|large|medium\s+sized|large\s+sized)\b',
        '',
        name
    )

    # 5️⃣ Remove preparation/state words
    name = re.sub(
        r'\b(whole|fresh|dried|raw|ripe|peeled|deseeded|'
        r'chopped|cubed|sliced|minced|grated|crushed|boiled|fine|finely)\b',
        '',
        name
    )

    # 6️⃣ Remove connectors
    name = re.sub(r'\b(and|or|with)\b', '', name)

    # 7️⃣ Collapse duplicate words
    tokens = []
    for w in name.split():
        if w not in tokens:
            tokens.append(w)
    name = " ".join(tokens)

    # 8️⃣ Final whitespace cleanup
    name = re.sub(r'\s+', ' ', name).strip()

    # 9️⃣ Fuzzy matching against standard ingredients
    if len(name) > 3:
        best_match = process.extractOne(
            name,
            STANDARD_INGREDIENTS,
            scorer=fuzz.WRatio
        )
        if best_match:
            match, score, _ = best_match
            if score >= 85:
                name = match

    # 🔟 Rejection of noise-only strings (e.g. ".", "-", "▢")
    if not name or len(name) < 2 or re.match(r'^[\W_]+$', name):
        return ""

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
    ingredients_json = recipe.get("ingredients_json", "[]")

    try:
        items = json.loads(ingredients_json)
        for item in items:
            raw_name = item.get("name", "").strip()
            raw_qty = item.get("quantity", "").strip()
            
            # Clean "▢" noise early
            raw_name = raw_name.replace("▢", "").strip()
            raw_qty = raw_qty.replace("▢", "").strip()

            # Robust join
            combined = f"{raw_qty} {raw_name}".strip()
            if not combined:
                continue

            parsed = parse_ingredient(combined)
            
            # 🔥 FINAL CLEANUP
            clean_name = final_cleanup_ingredient_name(
                parsed.get("ingredient_name", "")
            )
            
            if not clean_name or not final_is_valid_ingredient(clean_name):
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

            # MERGE DUPLICATES
            found = False
            for existing in parsed_ingredients:
                if existing["ingredient_name"] == clean_name:
                    found = True
                    if existing["unit"] == unit:
                        if existing["quantity"] is not None and qty is not None:
                            existing["quantity"] += qty
                        elif qty is not None:
                             existing["quantity"] = qty
                    elif existing["unit"] is None and unit is not None:
                        existing["unit"] = unit
                        existing["quantity"] = qty
                        if note:
                            existing.setdefault("ingredient_info", {})
                            existing["ingredient_info"]["unit_conversion"] = note
                    break
            
            if not found:
                 parsed_ingredients.append(parsed)

    except (json.JSONDecodeError, TypeError):
        pass

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
