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

def synthesize_instructions(prep_steps: list, cook_steps: list, quick_steps: list) -> dict:
    """
    Merges and formats steps into prep_steps, cook_steps, and a coherent summary.
    This is Layer 1 of the Triple-Logic Pipeline (AI).
    """
    if not model:
        return {"prep_steps": [], "cook_steps": [], "summary": ""}

    prompt = f"""
    You are an expert food writer. Process the following recipe steps into a structured JSON object.
    
    EXPECTED JSON STRUCTURE:
    {{
        "prep_steps": ["list of preparation steps"],
        "cook_steps": ["list of cooking steps"],
        "summary": "A professional, coherent, and summarized single string of the entire recipe flow."
    }}

    RULES:
    - "prep_steps": List individual actions for prep (chopping, measuring, etc.).
    - "cook_steps": List individual actions for cooking (boiling, frying, etc.).
    - "summary": Combine everything into a clean, narrative-style multi-line string. Do NOT prefix every line with "PREP" or "COOK". Use logical flow.
    - Merge overlapping or redundant information.
    - Be clear and authoritative.

    Raw Data:
    Prep Steps: {json.dumps(prep_steps)}
    Cook Steps: {json.dumps(cook_steps)}
    Quick Steps: {json.dumps(quick_steps)}

    Return ONLY the valid JSON object.
    """

    response_text = _call_gemini(prompt)
    if not response_text:
        return {"prep_steps": [], "cook_steps": [], "summary": ""}

    response_text = re.sub(r'```json\s*|\s*```', '', response_text).strip()

    try:
        return json.loads(response_text)
    except Exception as e:
        logger.error(f"Failed to parse AI synthesized instructions: {e}")
        return {"prep_steps": [], "cook_steps": [], "summary": ""}

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

def synthesize_instructions(prep_steps: list, cook_steps: list, quick_steps: list) -> dict:
    """
    Layer 2: Instruction Synthesis.
    Combines and cleans multiple instruction sources into a coherent summary.
    """
    if not model:
        return {"summary": "", "prep_steps": prep_steps, "cook_steps": cook_steps}

    prompt = f"""
    Synthesize these recipe steps into a clear, professional instruction summary.
    Prep: {json.dumps(prep_steps)}
    Cook: {json.dumps(cook_steps)}
    Quick: {json.dumps(quick_steps)}
    
    Return ONLY JSON:
    {{
        "summary": "Full instruction string",
        "prep_steps": ["cleaned prep list"],
        "cook_steps": ["cleaned cook list"]
    }}
    """
    response_text = _call_gemini(prompt)
    response_text = re.sub(r'```json\s*|\s*```', '', response_text).strip()
    try:
        return json.loads(response_text)
    except:
        return {"summary": "", "prep_steps": prep_steps, "cook_steps": cook_steps}

def adaptive_map(raw_data: dict) -> dict:
    """
    Layer 0: Semantic Mapper.
    Maps unknown recipe data structures to our standard internal format.
    """
    if not model:
        return raw_data

    prompt = f"""
    You are a data architect. Map the following unknown recipe data to our internal schema.
    
    Raw Data: {json.dumps(raw_data)}
    
    Target Internal Schema:
    {{
        "recipe_name": "string",
        "raw_ingredients": ["list of messy ingredient strings"],
        "prep_steps": ["list of strings"],
        "cook_steps": ["list of strings"]
    }}
    
    Return ONLY a valid JSON object.
    """
    response_text = _call_gemini(prompt)
    response_text = re.sub(r'```json\s*|\s*```', '', response_text).strip()
    try:
        return json.loads(response_text)
    except:
        return raw_data

def resolve_ambiguity(ingredient_name: str, recipe_context: str) -> dict:
    """
    Layer 2: Ambiguity Resolution.
    Classifies generic terms (e.g., "masala" -> "garam masala") based on context.
    """
    if not model:
        return {"suggestion": ingredient_name, "confidence_score": 0.0}

    prompt = f"""
    The ingredient "{ingredient_name}" is ambiguous in this recipe context: "{recipe_context}".
    Suggest the most likely specific ingredient intended.
    
    Return ONLY JSON:
    {{
        "suggestion": "specific ingredient name",
        "confidence_score": 0.0 to 1.0,
        "reasoning": "brief explanation"
    }}
    """
    response_text = _call_gemini(prompt)
    response_text = re.sub(r'```json\s*|\s*```', '', response_text).strip()
    try:
        return json.loads(response_text)
    except:
        return {"suggestion": ingredient_name, "confidence_score": 0.0}

def suggest_missing_data(ingredient_name: str, recipe_context: str) -> dict:
    """
    Layer 2: Missing Data Suggestion.
    Provides reasonable defaults for missing quantities.
    """
    if not model:
        return {"quantity": None, "unit": None, "confidence_score": 0.0}

    prompt = f"""
    The ingredient "{ingredient_name}" has no quantity in context: "{recipe_context}".
    What is a reasonable default quantity/unit for 4 servings?
    
    Return ONLY JSON:
    {{
        "quantity": float,
        "unit": "standard unit (g, ml, tsp, tbsp, etc.)",
        "confidence_score": 0.0 to 1.0
    }}
    """
    response_text = _call_gemini(prompt)
    response_text = re.sub(r'```json\s*|\s*```', '', response_text).strip()
    try:
        return json.loads(response_text)
    except:
        return {"quantity": None, "unit": None, "confidence_score": 0.0}

def clean_noise_dynamically(raw_text: str) -> str:
    """
    Layer 2: Dynamic Cleaning.
    Removes web residues and noise based on semantic intent.
    """
    if not model:
        return raw_text

    prompt = f"""
    Clean this recipe text. Remove HTML, ads, and unrelated site noise. 
    Keep only the relevant recipe instruction or ingredient text.
    
    Text: {raw_text}
    
    Return ONLY the cleaned text string.
    """
    return _call_gemini(prompt) or raw_text
