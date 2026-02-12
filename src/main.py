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
from normalizers import normalize_times, extract_servings
from unit_normalizer import normalize_quantity_unit
from unit_normalizer import normalize_quantity_unit
from text_utils import universal_clean, clean_recipe_title
from rapidfuzz import fuzz

from db import get_connection
from db_insert import (
    insert_recipe,
    insert_recipe_ingredients,
    insert_meal,
    insert_meal_recipe,
    insert_meal_ingredients
)
import ai_processor
from normalizers import normalize_times, extract_servings

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
    NLP Layer: Absolute final cleanup using universal utility.
    """
    return universal_clean(name)


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
    # Layer 1: Deterministic Keywords (Fast/Reliable)
    if any(k in name for k in ["dosa", "idli", "poha", "upma", "pongal","Breakfast","paratha"]):
        return "breakfast"
    if any(k in name for k in ["rice", "biryani", "pulao", "lunch"]):
        return "lunch"
    
    # Layer 2: Semantic AI Fallback (If keywords fail)
    # This prevents "Everything is Dinner" issue
    ai_meal = ai_processor.categorize_meal(recipe_name)
    return ai_meal


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

    title = clean_recipe_title(recipe.get("recipe_name", "Unknown Recipe"))
    
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
        
        # Populate ingredient_info with unit_conversion
        if "ingredient_info" not in parsed:
            parsed["ingredient_info"] = {}
        
        # Add unit_conversion to info
        if note and note != "no conversion applied":
             parsed["ingredient_info"]["unit_conversion"] = note

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
        
        # ALLOWED LLM USAGE: Ingredient Entity Disambiguation
        if item["is_ambiguous"]:
            ai_res = ai_processor.resolve_ambiguity(parsed["ingredient_name"], recipe_context)
            if ai_res.get("confidence_score", 0) > 0.7:
                parsed["ingredient_name"] = ai_res["suggestion"]
                parsed["ai_refined"] = True
        
        # PROHIBITED LLM USAGE: Simple quantity parsing/inference is handled deterministically
        # Note: Defaulting to 1.0 is now handled inside normalize_quantity_unit to respect exemptions.
        pass

        # Final Deterministic Normalization
        q, u, n = normalize_quantity_unit(parsed["quantity"], parsed["unit"], parsed["ingredient_name"])
        parsed["quantity"] = q
        parsed["unit"] = u
        
        if n and n != "no conversion applied":
             if "ingredient_info" not in parsed:
                 parsed["ingredient_info"] = {}
             parsed["ingredient_info"]["unit_conversion"] = n
        
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
    is_ingredients_ai = any([i.get("ai_refined") for i in processed_ingredients])
    
    metadata = {
        "ai_assisted": is_ingredients_ai or is_adaptive,
        "uncertainty_rate": round(len(exception_queue) / max(len(raw_ingredients), 1), 2),
        "source_format": "adaptive_mapped" if is_adaptive else "standard"
    }

    # Instruction Logic
    def ensure_list(s):
        if isinstance(s, str):
            try: return json.loads(s)
            except: return [s]
        return s if isinstance(s, list) else []

    raw_prep = ensure_list(recipe.get("prep_steps") or recipe.get("preparation") or [])
    raw_cook = ensure_list(recipe.get("cook_steps") or recipe.get("cooking") or [])
    all_raw_steps = raw_prep + raw_cook
    
    # ALLOWED LLM USAGE: Step Classification
    ai_classification = ai_processor.classify_steps(all_raw_steps)
    
    final_prep = ai_classification.get("prep", [])
    final_cook = ai_classification.get("cook", [])
    
    # Fallback if AI fails: Use deterministic cleaning
    steps_ai_success = bool(final_prep or final_cook)
    if not final_prep and not final_cook:
        final_prep = clean_instructions(raw_prep)
        final_cook = clean_instructions(raw_cook)
    
    # Update AI flag to include steps
    metadata["ai_assisted"] = metadata["ai_assisted"] or steps_ai_success
    
    # Deduplicate steps using Fuzzy Logic (remove 90%+ similar strings)
    final_combined_list = []
    for s in (final_prep + final_cook):
        is_duplicate = False
        for existing in final_combined_list:
            # Traditional fuzzy match
            if fuzz.ratio(s.lower(), existing.lower()) > 80:
                is_duplicate = True
                break
            # Subset match (if one is almost entirely inside another)
            if s.lower() in existing.lower() or existing.lower() in s.lower():
                # Keep the more descriptive one if they are short, or the shorter one if it's cleaner
                # Actually, in recipes, usually the longer one has more detail.
                # But here we want 'summarized' so we keep the shorter one if they are >= 90% overlap
                is_duplicate = True
                break
        if not is_duplicate:
            final_combined_list.append(s)

    combined_instructions = "Total_steps: " + "\n".join(final_combined_list)

    # --- EXTRACT METADATA (DETERMINISTIC) ---
    servings = extract_servings(recipe.get("servings") or recipe.get("yield") or recipe.get("serves"))
    times = normalize_times(recipe)

    return {
        "recipe_name": title,
        "ingredients": unique_ingredients,
        "instructions": combined_instructions,
        "metadata": metadata,
        "servings": servings,
        **times
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

        is_ai = "🤖 [AI]" if structured["metadata"].get("ai_assisted") else "⚡ [Regex]"
        print(f"Inserted: {structured['recipe_name']} {is_ai}")

    conn.commit()
    cur.close()
    conn.close()


if __name__ == "__main__":
    main()
