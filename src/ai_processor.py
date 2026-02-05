import google.generativeai as genai
import os
import json
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configure Gemini
api_key = os.getenv("GOOGLE_API_KEY")
if api_key:
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-1.5-flash')
else:
    logger.warning("GOOGLE_API_KEY not found. AI features will be disabled (falling back to deterministic logic).")
    model = None

def _call_gemini(prompt: str) -> str:
    if not model:
        return ""
    try:
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        logger.error(f"Error calling Gemini: {e}")
        return ""

def refine_ingredients(raw_ingredients: list) -> list:
    """
    Uses LLM to clean and structure messy ingredient strings.
    This is Layer 1 of the Triple-Logic Pipeline (AI).
    """
    if not model:
        return []

    prompt = f"""
    You are a professional chef and data scientist. 
    Clean and structure the following list of raw recipe ingredients into a clean JSON array.
    
    RULES:
    1. Extract "ingredient_name" as the clean, singular noun (e.g., "chicken", "onion").
    2. Extract "quantity" as a numeric value (convert words like "one" to 1.0).
    3. Extract "unit" as a standard abbreviation (g, ml, tsp, tbsp, cup, kg, pinch).
    4. Set "is_optional" to true if text says "optional", "to taste", or "as needed".
    5. Put preparation details (chopped, sliced, etc.) in "ingredient_info" as a dictionary.
    6. If an ingredient is "divided", note it in "ingredient_info".

    Raw Ingredients:
    {json.dumps(raw_ingredients, indent=2)}

    Return ONLY the valid JSON array of objects.
    """
    
    response_text = _call_gemini(prompt)
    if not response_text:
        return []

    # Strip markdown code blocks if present
    response_text = re.sub(r'```json\s*|\s*```', '', response_text).strip()
    
    try:
        return json.loads(response_text)
    except Exception as e:
        logger.error(f"Failed to parse AI refined ingredients: {e}")
        return []

def synthesize_instructions(prep_steps: list, cook_steps: list, quick_steps: list) -> str:
    """
    Merges and formats steps into coherent instructions.
    This is Layer 1 of the Triple-Logic Pipeline (AI).
    """
    if not model:
        return ""

    prompt = f"""
    You are an expert food writer. Synthesize the following fragmented recipe steps into a clear, 
    concise, and professionally numbered set of instructions.
    
    Instructions should:
    - Flow logically from preparation to cooking to serving.
    - Merge overlapping or redundant information.
    - Be clear and authoritative.

    Prep Steps: {json.dumps(prep_steps)}
    Cook Steps: {json.dumps(cook_steps)}
    Quick Steps: {json.dumps(quick_steps)}

    Return ONLY the final plain text instructions.
    """

    return _call_gemini(prompt)

def extract_recipe_metadata(recipe_data: dict) -> dict:
    """
    Extracts tags, difficulty level, and servings from raw recipe data.
    This is Layer 1 of the Triple-Logic Pipeline (AI).
    """
    if not model:
        return {}

    prompt = f"""
    Analyze the following recipe data and extract structured metadata:
    1. "difficulty_level": one of ["easy", "medium", "hard"]
    2. "tags": a list of relevant strings (e.g., "spicy", "vegan", "gluten-free", "indian")
    3. "servings": a numeric value (integer)

    Recipe Name: {recipe_data.get('recipe_name')}
    Description: {recipe_data.get('description', 'N/A')}

    Return ONLY a valid JSON object with the keys "difficulty_level", "tags", and "servings".
    """

    response_text = _call_gemini(prompt)
    if not response_text:
        return {}

    response_text = re.sub(r'```json\s*|\s*```', '', response_text).strip()

    try:
        return json.loads(response_text)
    except Exception as e:
        logger.error(f"Failed to parse AI extracted metadata: {e}")
        return {}
