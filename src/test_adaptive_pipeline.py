
import json
import os
import sys

# Add src to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), 'src')))

try:
    from main import process_recipe
    import ai_processor
except ImportError as e:
    print(f"Import Error: {e}")
    sys.exit(1)

def test_adaptive_hybrid():
    print("--- TESTING LAYER 0: ADAPTIVE MAPPING (UNKNOWN SCHEMA) ---")
    # This data structure is totally unknown to the standard pipeline
    raw_unknown_data = {
        "nombre_de_la_receta": "Arroz con Pollo",
        "lista_de_ingredientes": ["1 kg chicken", "2 cups rice", "salt to taste"],
        "pasos_preparacion": ["Cut the chicken.", "Cook the rice."]
    }

    # We mock the AI call for adaptive_map since we don't have a real API key in this environment.
    # In a real scenario, the AI would see the "Intent" and map it.
    original_map = ai_processor.adaptive_map
    ai_processor.adaptive_map = lambda x: {
        "recipe_name": x.get("nombre_de_la_receta"),
        "raw_ingredients": [{"name": i} for i in x.get("lista_de_ingredientes", [])],
        "prep_steps": x.get("pasos_preparacion"),
        "cook_steps": []
    }

    print(f"Raw Unknown Input Keys: {list(raw_unknown_data.keys())}")
    processed = process_recipe(raw_unknown_data)
    
    print("\n--- OUTPUT AFTER ADAPTIVE MAPPING ---")
    print(json.dumps(processed, indent=2))
    
    assert processed["recipe_name"] == "Arroz con Pollo"
    assert len(processed["ingredients"]) > 0
    assert processed["metadata"]["source_format"] == "adaptive_mapped"
    print("\n✅ Layer 0 Verification Successful!")

    # Restore
    ai_processor.adaptive_map = original_map

    print("\n--- TESTING LAYER 2: TARGETED AI (AMBIGUITY) ---")
    ambiguous_recipe = {
        "recipe_name": "Garam Masala Chicken",
        "raw_ingredients": [
            {"name": "chicken", "quantity": "500g"},
            {"name": "masala", "quantity": "1 tsp"}
        ]
    }
    
    # Mock ambiguity resolution
    original_resolve = ai_processor.resolve_ambiguity
    ai_processor.resolve_ambiguity = lambda name, context: {
        "suggestion": "garam masala" if name == "masala" else name,
        "confidence_score": 0.9,
        "reasoning": "Context mentions Garam Masala Chicken"
    }
    
    processed_amb = process_recipe(ambiguous_recipe)
    print(json.dumps(processed_amb, indent=2))
    
    ingredients = [i["ingredient_name"] for i in processed_amb["ingredients"]]
    assert "garam masala" in ingredients
    assert processed_amb["metadata"]["ai_assisted"] is True
    print("\n✅ Layer 2 Verification Successful!")
    
    # Restore
    ai_processor.resolve_ambiguity = original_resolve

if __name__ == "__main__":
    test_adaptive_hybrid()
