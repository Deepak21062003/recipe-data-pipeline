from google import genai
import os
import json
import logging
from dotenv import load_dotenv
import re

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configure Gemini
api_key = os.getenv("GOOGLE_API_KEY")
if api_key:
    client = genai.Client(api_key=api_key)
    MODEL_ID = "gemini-flash-latest"
else:
    logger.warning("GOOGLE_API_KEY not found. AI features will be disabled (falling back to deterministic logic).")
    client = None

# Session state for AI availability
_quota_exceeded = False

def _call_gemini(prompt: str) -> str:
    global _quota_exceeded
    if not client or _quota_exceeded:
        return ""
    try:
        response = client.models.generate_content(
            model=MODEL_ID,
            contents=prompt
        )
        return response.text.strip()
    except Exception as e:
        error_msg = str(e).upper()
        if "429" in error_msg or "RESOURCE_EXHAUSTED" in error_msg:
            logger.warning("AI Quota exhausted (429). Falling back to deterministic logic for this session.")
            _quota_exceeded = True
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
    if not client or _quota_exceeded:
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
    if not client or _quota_exceeded:
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
    if not client or _quota_exceeded:
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

def summarize_steps(prep_steps: list, cook_steps: list) -> str:
    """
    LLM TASK: Instruction Summarization.
    Converts raw steps into a professional, concise summary with clear headers.
    """
    if not client or _quota_exceeded or (not prep_steps and not cook_steps):
        # Fallback: Simple structured joining
        res = []
        if prep_steps:
            res.append("prep_steps:")
            res.extend([f"- {s}" for s in prep_steps])
        if cook_steps:
            if res: res.append("")
            res.append("cook_steps:")
            res.extend([f"- {s}" for s in cook_steps])
        return "\n".join(res)

    prompt = f"""
    You are a professional chef. Summarize the following recipe steps into two clear and concise sections: 
    "Prep_steps" and "Cook_steps". 
    
    Rules:
    1. Combine multiple small actions into single, logical summarized steps.
    2. Remove any conversational filler or non-essential details.
    3. Use a professional, action-oriented tone.
    
    Raw Prep: {json.dumps(prep_steps)}
    Raw Cook: {json.dumps(cook_steps)}
    
    Format exactly as:
    prep_steps:
    - [Summarized point]
    
    cook_steps:
    - [Summarized point]
    """
    return _call_gemini(prompt)

def draft_instructions(title: str, ingredients: list) -> dict:
    """
    LLM TASK: Instruction Drafting.
    Generates realistic preparation and cooking steps when source data is empty.
    Returns: {"prep_steps": [...], "cook_steps": [...]}
    """
    if not client or _quota_exceeded:
        return {"prep_steps": ["[No instructions found]"], "cook_steps": ["[No instructions found]"]}

    # Format ingredients for context
    ings_text = ", ".join([i.get('ingredient_name', '') for i in ingredients])

    prompt = f"""
    You are a professional recipe developer. The following recipe has a title and ingredients but NO instructions.
    
    Recipe Title: {title}
    Ingredients: {ings_text}
    
    Based on these, draft a realistic, professional, and concise 2-section guide.
    1. "prep_steps": Focus on washing, chopping, and measuring.
    2. "cook_steps": Focus on the actual cooking, assembling, or serving.
    
    Return ONLY JSON:
    {{
        "prep_steps": ["step1", ...],
        "cook_steps": ["step2", ...]
    }}
    """
    response_text = _call_gemini(prompt)
    response_text = re.sub(r'```json\s*|\s*```', '', response_text).strip()
    try:
        return json.loads(response_text)
    except:
        return {"prep_steps": [], "cook_steps": []}
