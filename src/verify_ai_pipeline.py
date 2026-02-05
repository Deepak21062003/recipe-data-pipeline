import json
import os
from main import process_recipe

def verify_pipeline():
    # Sample raw recipe for testing
    sample_recipe = {
        "recipe_name": "AI Test Chicken",
        "description": "A test spicy chicken dish.",
        "ingredients_json": json.dumps([
            {"name": "messy chiken pieces with bones", "quantity": "▢ 500"},
            {"name": "some salt to taste", "quantity": ""}
        ]),
        "prep_steps": json.dumps(["Clean chicken", "Apply salt"]),
        "cook_steps": json.dumps(["Fry until golden"]),
        "quick_steps": json.dumps(["Quick fry method"]),
        "prep_time_min": "10",
        "cook_time_min": "20",
        "total_time_min": "30"
    }

    print("--- RAW RECIPE DATA ---")
    print(json.dumps(sample_recipe, indent=2))

    print("\n--- PROCESSING (Deterministic Fallback) ---")
    structured = process_recipe(sample_recipe)
    print(json.dumps(structured, indent=2))

    # Verification of key requirements
    print("\n--- VERIFICATION CHECKBOARD ---")
    print(f"Recipe Name: {structured.get('recipe_name')}")
    print(f"Ingredient Count: {len(structured.get('ingredients', []))}")
    print(f"Difficulty Level: {structured.get('difficulty_level')} (AI: {bool(os.getenv('GOOGLE_API_KEY'))})")
    print(f"Instructions synthesized: {bool(structured.get('instructions'))}")

if __name__ == "__main__":
    verify_pipeline()
