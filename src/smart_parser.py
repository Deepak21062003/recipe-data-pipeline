import re
import json
from typing import List, Dict, Any, Optional
from ingredient_parser import parse_ingredient
from instruction_cleaner import clean_instructions

class LocalIngredientRefiner:
    """
    Local replacement for LLM ingredient refiner.
    Uses basic parsing rules and existing deterministic logic.
    """
    @staticmethod
    def refine(raw_ingredients: list) -> list:
        refined = []
        for item in raw_ingredients:
            if isinstance(item, str):
                parsed = parse_ingredient(item)
            elif isinstance(item, dict):
                name = item.get("name") or item.get("ingredient_name") or ""
                qty = item.get("quantity") or ""
                unit = item.get("unit") or ""
                combined = f"{qty} {unit} {name}".strip()
                parsed = parse_ingredient(combined)
            else:
                continue
            
            if parsed and parsed.get("ingredient_name"):
                refined.append(parsed)
        return refined

class LocalInstructionSynthesizer:
    """
    Local replacement for LLM instruction synthesizer.
    Focuses on cleaning and basic merging.
    """
    @staticmethod
    def synthesize(prep_steps: list, cook_steps: list, quick_steps: list) -> dict:
        clean_prep = clean_instructions(prep_steps)
        clean_cook = clean_instructions(cook_steps)
        clean_quick = clean_instructions(quick_steps)
        
        # Merge quick steps into cook steps if they aren't duplicates
        combined_cook = list(clean_cook)
        for step in clean_quick:
            if step not in combined_cook:
                combined_cook.append(step)
        
        # Build narrative summary
        summary_parts = []
        if clean_prep:
            summary_parts.append("Preparation:\n" + "\n".join([f"- {s}" for s in clean_prep]))
        if combined_cook:
            summary_parts.append("Cooking:\n" + "\n".join([f"- {s}" for s in combined_cook]))
            
        return {
            "prep_steps": clean_prep,
            "cook_steps": combined_cook,
            "summary": "\n\n".join(summary_parts)
        }

class LocalMetadataExtractor:
    """
    Local replacement for LLM metadata extraction.
    Infere stats based on ingredient count and total time.
    """
    @staticmethod
    def extract(recipe_data: dict) -> dict:
        name = recipe_data.get("recipe_name", "").lower()
        description = recipe_data.get("description", "").lower()
        
        # Difficulty inference
        ing_count = len(recipe_data.get("raw_ingredients", []))
        if ing_count > 12:
            difficulty = "hard"
        elif ing_count > 6:
            difficulty = "medium"
        else:
            difficulty = "easy"
            
        # Tag inference
        tags = []
        tag_map = {
            "spicy": ["spicy", "chili", "pepper", "hot"],
            "vegan": ["vegan"],
            "vegetarian": ["veg", "vegetarian", "paneer", "dal"],
            "indian": ["indian", "masala", "curry"],
            "healthy": ["healthy", "salad", "protein"]
        }
        
        for tag, keywords in tag_map.items():
            if any(k in name or k in description for k in keywords):
                tags.append(tag)
        
        # Default servings
        servings = 2
        serv_match = re.search(r'(\d+)\s*servings?', name + description)
        if serv_match:
            servings = int(serv_match.group(1))
            
        return {
            "difficulty_level": difficulty,
            "tags": tags,
            "servings": servings
        }
