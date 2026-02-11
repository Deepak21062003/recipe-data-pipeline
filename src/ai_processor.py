import google.generativeai as genai
import os
import re
import json
import logging
from dotenv import load_dotenv

load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configure Gemini
api_key = os.getenv("GOOGLE_API_KEY")
if api_key:
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-flash-latest')
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
        if "429" in str(e):
            logger.warning("Gemini Quota Exceeded (429). Falling back to Regex logic for this recipe.")
        else:
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
    Classify these recipe steps into:
    1. "prep": Preparation actions (chopping, measuring, preheating).
    2. "cook": Cooking actions (frying, boiling, baking).
    3. "noise": Web advertisements, social media links, site credits, redundant metadata, or low-value commentary.
    
    CLEANING RULES:
    - If a step is a near-duplicate, put the redundant copy in "noise".
    - Filter out sentences that don't contain a cooking command.
    - STRIP FLUFF: Remove flowery adjectives (e.g., "beautifully", "perfectly", "deliciously") if they don't add technical value to the step.
    - Focus on the core action (e.g., "Fry until golden" instead of "Fry until they are beautifully golden and crispy").
    
    Steps: {json.dumps(raw_steps)}
    
    Return ONLY JSON:
    {{
        "prep": ["clean_step", ...],
        "cook": ["clean_step", ...],
        "noise": ["removed_step", ...]
    }}
    """
    response_text = _call_gemini(prompt)
    response_text = re.sub(r'```json\s*|\s*```', '', response_text).strip()
    try:
        return json.loads(response_text)
    except:
        return {"prep": [], "cook": [], "noise": []}
