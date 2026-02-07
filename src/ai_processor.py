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

# --- ALLOWED LLM USAGE: Ingredient Entity Disambiguation ---

def resolve_ambiguity(ingredient_name: str, recipe_context: str) -> dict:
    """
    LLM TASK: Ingredient Entity Disambiguation.
    Resolves generic names (e.g., 'masala') to specific entities based on context.
    Regex cannot solve this as it requires semantic understanding of the recipe cuisine/title.
    """
    if not model:
        return {"suggestion": ingredient_name, "confidence_score": 0.0}

    prompt = f"""
    Context: {recipe_context}
    The ingredient listed is simply "{ingredient_name}". 
    Based on the context, what specific ingredient entity is most likely intended?
    
    Return ONLY JSON:
    {{
        "suggestion": "specific noun",
        "confidence_score": 0.0-1.0,
        "reasoning": "shorter than 10 words"
    }}
    """
    response_text = _call_gemini(prompt)
    response_text = re.sub(r'```json\s*|\s*```', '', response_text).strip()
    try:
        return json.loads(response_text)
    except:
        return {"suggestion": ingredient_name, "confidence_score": 0.0}

# --- ALLOWED LLM USAGE: Step Classification ---

def adaptive_map(raw_data: dict) -> dict:
    """
    LLM TASK: Field Classification.
    Identifies which keys in an unknown schema represent 'ingredients' and 'instructions'.
    Regex is insufficient because key names are arbitrary across different datasets.
    """
    if not model:
        return raw_data

    prompt = f"""
    Classify the following raw data keys into our target schema: 
    "recipe_name", "raw_ingredients", "instructions".
    
    Raw Data: {json.dumps(raw_data)}
    
    Return ONLY a valid JSON object mapping our keys to the raw values.
    """
    response_text = _call_gemini(prompt)
    response_text = re.sub(r'```json\s*|\s*```', '', response_text).strip()
    try:
        return json.loads(response_text)
    except:
        return raw_data

def classify_steps(raw_steps: list) -> dict:
    """
    LLM TASK: Step Classification.
    Categorizes raw strings into 'prep', 'cook', or 'noise'.
    Regex is insufficient as it cannot distinguish 'Cut the chicken' (prep) 
    from 'Fry the chicken' (cook) reliably without semantic analysis.
    """
    if not model:
        return {"prep": [], "cook": [], "noise": []}

    prompt = f"""
    Classify these recipe steps into "prep" (preparation), "cook" (cooking), or "noise" (web ads/site info).
    Steps: {json.dumps(raw_steps)}
    
    Return ONLY JSON:
    {{
        "prep": ["step1", ...],
        "cook": ["step1", ...],
        "noise": ["step1", ...]
    }}
    """
    response_text = _call_gemini(prompt)
    response_text = re.sub(r'```json\s*|\s*```', '', response_text).strip()
    try:
        return json.loads(response_text)
    except:
        return {"prep": [], "cook": [], "noise": []}
