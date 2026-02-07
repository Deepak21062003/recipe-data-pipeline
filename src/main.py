import json
import os
import re
import csv
import logging
from typing import List, Dict, Optional
import sys

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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
import ai_processor

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
    NLP Layer: Absolute final cleanup.
    Guarantees ONLY clean ingredient nouns by stripping adjectives and descriptors.
    """
    if not name:
        return ""

    name = name.lower()

    # 1. Remove "recipe" or "recipes" or "scaled" noise
    name = re.sub(r'\b(recipes?|can be scaled|about|approximately|roughly)\b', '', name)

    # 2. Remove leading articles and pronouns
    name = re.sub(r'^(a|an|the|any|some|few)\s+', '', name)

    # 3. Remove ALL symbols anywhere
    name = re.sub(r'[\\/,–—\(\)\[\]\{\}.\-:*]+', ' ', name)

    # 4. Remove quantity / size / temperature adjectives (NLP heuristics)
    name = re.sub(
        r'\b(a\s+few|few|a\s+pinch|pinch|a\s+handful|handful|'
        r'small|medium|large|medium\s+sized|large\s+sized|'
        r'lukewarm|hot|cold|warm|ice\s+cold|chilled)\b',
        '',
        name
    )

    # 5. Remove preparation/state words (NLP heuristics)
    name = re.sub(
        r'\b(whole|fresh|dried|raw|ripe|peeled|deseeded|'
        r'chopped|cubed|sliced|minced|grated|crushed|boiled|fine|finely|'
        r'roasted|toasted|fried|sauteed|sautéed|washed|cleaned|'
        r'beaten|whisked|blended|mashed|pureed|puréed|'
        r'pieces|parts|bones|bone\s+in|boneless|skinless|stems|stalks)\b',
        '',
        name
    )

    # 6. Remove connectors and miscellaneous noise
    name = re.sub(r'\b(and|or|with|for|in|as|per|into|for|to|on|of)\b', '', name)

    # 7. Collapse duplicate words
    tokens = []
    for w in name.split():
        if w not in tokens:
            tokens.append(w)
    name = " ".join(tokens)

    # 8. Final whitespace cleanup
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
    if any(k in name for k in ["dosa", "idli", "poha", "upma", "pongal", "paratha"]):
        return "breakfast"
    if any(k in name for k in ["rice", "biryani", "pulao", "lunch"]):
        return "lunch"
    return "dinner"


# ------------------------------------
# PROCESS SINGLE RECIPE (TRIPLE-LOGIC)
# ------------------------------------
def process_recipe(recipe: dict) -> dict:
    """
    Assessment-Aligned Adaptive Hybrid Pipeline:
    Layer 0: Adaptive Mapping (AI-Based Format detection)
    Layer 1: Deterministic Primary Flow (Regex/Rules)
    Layer 2: Targeted AI Assistance (Exceptions Only)
    Layer 3: Validation & Guardrails
    """
    
    # --- LAYER 0: ADAPTIVE MAPPING ---
    # Trigger AI only if the expected schema is missing
    is_adaptive = False
    if not any(k in recipe for k in ["ingredients_json", "raw_ingredients", "recipe_name"]):
        logger.info("Unknown data format detected. Invoking Layer 0 (Adaptive Mapping)...")
        recipe = ai_processor.adaptive_map(recipe)
        is_adaptive = True

    title = recipe.get("recipe_name", "Unknown Recipe")
    
    # --- LAYER 1: DETERMINISTIC PRIMARY FLOW ---
    raw_ing_data = recipe.get("ingredients_json") or recipe.get("raw_ingredients") or "[]"
    try:
        raw_ingredients = json.loads(raw_ing_data) if isinstance(raw_ing_data, str) else raw_ing_data
    except:
        raw_ingredients = []

    processed_ingredients = []
    exception_queue = []

    for item in raw_ingredients:
        raw_name = item.get("name", "").lower().strip()
        raw_qty = item.get("quantity", "").replace("▢", "").strip()

        if not raw_name or looks_like_instruction(raw_name):
            continue

        # Rule-based parsing
        parsed = parse_ingredient(f"{raw_qty} {raw_name}".strip())
        clean_name = final_cleanup_ingredient_name(parsed.get("ingredient_name", ""))

        if not final_is_valid_ingredient(clean_name):
            continue

        parsed["ingredient_name"] = clean_name
        qty, unit, note = normalize_quantity_unit(parsed.get("quantity"), parsed.get("unit"), clean_name)
        
        # Uncertainty Detection (Trigger for Layer 2)
        is_ambiguous = clean_name in {"masala", "spices", "seasoning", "powder", "mix"}
        is_missing_qty = qty is None or (isinstance(qty, float) and qty <= 0)

        if is_ambiguous or is_missing_qty:
            exception_queue.append({
                "parsed": parsed,
                "is_ambiguous": is_ambiguous,
                "is_missing_qty": is_missing_qty
            })
        else:
            parsed["quantity"] = qty
            parsed["unit"] = unit
            processed_ingredients.append(parsed)

    # --- LAYER 2: TARGETED AI ASSISTANCE ---
    recipe_context = f"Recipe: {title}. Existing: {', '.join([i['ingredient_name'] for i in processed_ingredients])}"
    
    for item in exception_queue:
        parsed = item["parsed"]
        
        if item["is_ambiguous"]:
            ai_res = ai_processor.resolve_ambiguity(parsed["ingredient_name"], recipe_context)
            if ai_res.get("confidence_score", 0) > 0.7:
                parsed["ingredient_name"] = ai_res["suggestion"]
                parsed["ai_refined"] = True
        
        if item["is_missing_qty"]:
            ai_data = ai_processor.suggest_missing_data(parsed["ingredient_name"], recipe_context)
            if ai_data.get("confidence_score", 0) > 0.7:
                parsed["quantity"] = ai_data.get("quantity")
                parsed["unit"] = ai_data.get("unit")
                parsed["ai_filled"] = True

        # Final Deterministic Normalization of AI output
        q, u, n = normalize_quantity_unit(parsed["quantity"], parsed["unit"], parsed["ingredient_name"])
        parsed["quantity"] = q
        parsed["unit"] = u
        
        if final_is_valid_ingredient(parsed["ingredient_name"]):
            processed_ingredients.append(parsed)

    # Deduplication
    unique_ingredients = []
    seen_names = {}
    for ing in processed_ingredients:
        name = ing["ingredient_name"]
        if name not in seen_names:
            seen_names[name] = ing
            unique_ingredients.append(ing)
        else:
            existing = seen_names[name]
            if existing["unit"] == ing["unit"] and existing["quantity"] and ing["quantity"]:
                existing["quantity"] += ing["quantity"]

    # --- LAYER 3: VALIDATION & GUARDRAILS ---
    # Final metadata check
    metadata = {
        "ai_assisted": len(exception_queue) > 0 or is_adaptive,
        "uncertainty_rate": round(len(exception_queue) / max(len(raw_ingredients), 1), 2),
        "source_format": "adaptive_mapped" if is_adaptive else "standard"
    }

    # Instruction Logic
    def ensure_list(s):
        if isinstance(s, str):
            try: return json.loads(s)
            except: return [s]
        return s if isinstance(s, list) else []

    prep_steps = ensure_list(recipe.get("prep_steps") or recipe.get("preparation") or [])
    cook_steps = ensure_list(recipe.get("cook_steps") or recipe.get("cooking") or [])
    
    # Smart synthesis for instructions
    ai_instruction_data = ai_processor.synthesize_instructions(prep_steps, cook_steps, [])
    combined_instructions = ai_instruction_data.get("summary", "")
    
    if not combined_instructions:
        combined_instructions = "\n".join(clean_instructions(prep_steps) + clean_instructions(cook_steps))

    return {
        "recipe_name": title,
        "ingredients": unique_ingredients,
        "instructions": combined_instructions,
        "metadata": metadata,
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
