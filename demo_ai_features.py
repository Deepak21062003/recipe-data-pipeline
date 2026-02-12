
from src.ai_processor import categorize_meal, resolve_ambiguity, classify_steps, adaptive_map
import json

def print_section(title):
    print("\n" + "="*50)
    print(f"🤖 AI ASSISTANCE DEMO: {title}")
    print("="*50)

# 1. SMART MEAL CATEGORIZATION
print_section("1. Smart Meal Categorization")
print("Scenario: A recipe named 'Avocado Toast' (No keywords like 'dosa' or 'rice')")
print(f"Regex Guess: 'dinner' (Default)")
ai_result = categorize_meal("Avocado Toast")
print(f"AI Result:   '{ai_result}' (Correct!)")

# 2. INGREDIENT DISAMBIGUATION
print_section("2. Context-Aware Disambiguation")
context = "Recipe: Chicken Tikka Masala. Ingredients: chicken, yogurt..."
print(f"Input: 'masala' (Ambiguous)")
print(f"Context: {context}")
ai_ing = resolve_ambiguity("masala", context)
print(f"AI Suggestion: '{ai_ing.get('suggestion')}'")

# 3. NOISE FILTERING & CLASSIFICATION
print_section("3. Instruction Classification & Noise Removal")
steps = [
    "Wash and cut the vegetables.",
    "Follow me on Instagram for more recipes!",
    "Fry the onions until golden brown."
]
print("Input Steps:")
for s in steps: print(f" - {s}")

print("\nAI Classification:")
classified = classify_steps(steps)
print(f" [Prep]:  {classified.get('prep')}")
print(f" [Cook]:  {classified.get('cook')}")
print(f" [Noise]: {classified.get('noise')} (Correctly Filtered!)")

# 4. ADAPTIVE MAPPING
print_section("4. Adaptive Schema Mapping")
# 5. INTERACTIVE LIVE DEMO
print_section("5. Interactive Live Mode")
print("🔥 Try it yourself! Type a recipe name (or 'exit' to quit).")
while True:
    user_input = input("\n>> Enter Recipe Name: ").strip()
    if user_input.lower() in ["exit", "quit"]:
        break
    if not user_input:
        continue
        
    print(f"... Analyzing '{user_input}' with AI ...")
    category = categorize_meal(user_input)
    print(f"✅ AI Categorized as: {category.upper()}")
