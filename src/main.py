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
    Unified Triple-Logic Pipeline:
    Layer 1: AI (Structuring & Enrichment)
    Layer 2: NLP (Sanitizing & Filtering)
    Layer 3: Deterministic (Standardizing & Logic)
    """
    
    # --- LAYER 1: AI ---
    ai_meta = ai_processor.extract_recipe_metadata(recipe)
    
    raw_ing_data = recipe.get("ingredients_json") or recipe.get("raw_ingredients") or "[]"
    try:
        raw_ingredients = json.loads(raw_ing_data) if isinstance(raw_ing_data, str) else raw_ing_data
    except:
        raw_ingredients = []

    prep_steps = recipe.get("prep_steps") or recipe.get("preparation") or "[]"
    cook_steps = recipe.get("cook_steps") or recipe.get("cooking") or "[]"
    quick_steps = recipe.get("quick_steps") or recipe.get("summary_steps") or "[]"
    
    def parse_steps(s):
        if isinstance(s, str):
            try: return json.loads(s)
            except: return []
        return s if isinstance(s, list) else []

    prep_steps = parse_steps(prep_steps)
    cook_steps = parse_steps(cook_steps)
    quick_steps = parse_steps(quick_steps)

    ai_instruction_data = ai_processor.synthesize_instructions(prep_steps, cook_steps, quick_steps)
    ai_ingredients = ai_processor.refine_ingredients(raw_ingredients)
    
    # --- LAYER 2 & 3: HYBRID PROCESSING ---
    processed_ingredients = []
    
    if ai_ingredients:
        # Process AI-suggested ingredients through NLP & Deterministic filters
        for ing in ai_ingredients:
            # NLP Cleanup
            clean_name = final_cleanup_ingredient_name(ing.get("ingredient_name", ""))
            if not final_is_valid_ingredient(clean_name):
                continue
                
            # Deterministic Normalization
            qty, unit, note = normalize_quantity_unit(
                ing.get("quantity"),
                ing.get("unit"),
                clean_name
            )
            
            ing["ingredient_name"] = clean_name
            ing["quantity"] = qty
            ing["unit"] = unit
            if note:
                ing.setdefault("ingredient_info", {})["unit_conversion"] = note
            processed_ingredients.append(ing)
    else:
        # LLM Failed or Disabled -> Use Deterministic Fallback with NLP filtering
        for item in raw_ingredients:
            raw_name = item.get("name", "").lower().strip()
            raw_qty = item.get("quantity", "").replace("▢", "").strip()

            if not raw_name or looks_like_instruction(raw_name):
                continue

            # Layer 3: Deterministic Parser
            parsed = parse_ingredient(f"{raw_qty} {raw_name}".strip())
            
            # Layer 2: NLP Cleanup
            clean_name = final_cleanup_ingredient_name(parsed.get("ingredient_name", ""))

            if not final_is_valid_ingredient(clean_name):
                continue

            parsed["ingredient_name"] = clean_name
            
            # Layer 3: Final Normalization
            qty, unit, note = normalize_quantity_unit(parsed.get("quantity"), parsed.get("unit"), clean_name)
            parsed["quantity"] = qty
            parsed["unit"] = unit
            if note:
                parsed.setdefault("ingredient_info", {})["unit_conversion"] = note
            processed_ingredients.append(parsed)

    # Deduplication & Final Synthesis
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

    # Final Instructions Synthesis (Split & Summarized)
    final_prep_steps = ai_instruction_data.get("prep_steps", [])
    final_cook_steps = ai_instruction_data.get("cook_steps", [])
    combined_instructions = ai_instruction_data.get("summary", "")
    
    if not final_prep_steps and not final_cook_steps and not combined_instructions:
        # Fallback: Use cleaned original steps
        final_prep_steps = clean_instructions(prep_steps)
        final_cook_steps = clean_instructions(cook_steps) + clean_instructions(quick_steps)
        
        # Cleaner fallback formatting without repetitive prefixes
        fallback_parts = []
        if final_prep_steps:
            fallback_parts.append("Preparation:\n" + "\n".join([f"- {s}" for s in final_prep_steps]))
        if final_cook_steps:
            fallback_parts.append("Cooking:\n" + "\n".join([f"- {s}" for s in final_cook_steps]))
        combined_instructions = "\n\n".join(fallback_parts)

    return {
        "recipe_name": recipe.get("recipe_name"),
        "ingredients": unique_ingredients,
        "instructions": combined_instructions,
        "prep_steps": final_prep_steps,
        "cook_steps": final_cook_steps,
        "difficulty_level": ai_meta.get("difficulty_level"),
        "tags": ai_meta.get("tags"),
        "servings": ai_meta.get("servings"),
        "metadata": ai_meta, 
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
