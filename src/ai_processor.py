import google.generativeai as genai
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

def resolve_ambiguity(ingredient_name: str, recipe_context: str) -> dict:
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

def adaptive_map(raw_data: dict) -> dict:
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

def summarize_steps(prep_steps: list, cook_steps: list) -> str:
    if not prep_steps and not cook_steps:
        return ""

    fallback_res = []
    if prep_steps:
        fallback_res.append("prep_steps:")
        fallback_res.extend([f"- {s}" for s in prep_steps])
    if cook_steps:
        if fallback_res: fallback_res.append("")
        fallback_res.append("quick_steps:")
        fallback_res.extend([f"- {s}" for s in cook_steps])
    
    fallback_string = "\n".join(fallback_res)

    if not model:
        return fallback_string

    prompt = f"""
    You are a professional chef. Summarize the following recipe steps into two clear and concise sections: 
    "prep_steps" and "quick_steps". 
    
    Rules:
    1. Combine multiple small actions into single, logical summarized steps.
    2. Remove any conversational filler or non-essential details.
    3. Use a professional, action-oriented tone.
    
    Raw Prep: {json.dumps(prep_steps)}
    Raw Cook: {json.dumps(cook_steps)}
    
    Format exactly as:
    prep_steps:
    - [Summarized point]
    
    quick_steps:
    - [Summarized point]
    """
    ai_response = _call_gemini(prompt)
    if not ai_response or not ai_response.strip():
        return fallback_string
    return ai_response

def draft_instructions(title: str, ingredients: list) -> dict:
    if not model:
        return {"prep_steps": ["[No instructions found]"], "quick_steps": ["[No instructions found]"]}

    ings_text = ", ".join([i.get('ingredient_name', '') for i in ingredients])

    prompt = f"""
    You are a professional recipe developer. The following recipe has a title and ingredients but NO instructions.
    
    Recipe Title: {title}
    Ingredients: {ings_text}
    
    Based on these, draft a realistic, professional, and concise 2-section guide.
    1. "prep_steps": Focus on washing, chopping, and measuring.
    2. "quick_steps": Focus on the actual cooking, assembling, or serving.
    
    Format exactly as:
    {{
        "prep_steps": ["step1", ...],
        "quick_steps": ["step2", ...]
    }}
    """
    response_text = _call_gemini(prompt)
    response_text = re.sub(r'```json\s*|\s*```', '', response_text).strip()
    try:
        data = json.loads(response_text)
        return {
            "prep_steps": data.get("prep_steps", []),
            "quick_steps": data.get("quick_steps", data.get("cook_steps", []))
        }
    except:
        return {"prep_steps": ["[Drafting failed]"], "quick_steps": ["[Drafting failed]"]}
