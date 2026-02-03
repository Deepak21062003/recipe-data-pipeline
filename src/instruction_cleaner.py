import re
from unit_normalizer import normalize_quantity_unit, infer_category
from text_utils import format_measurement_as_text


# ------------------------------------
# INSTRUCTION DETECTION
# ------------------------------------
def looks_like_ingredient_line(text: str) -> bool:
    """
    Detect if a line is an ingredient listing rather than a step.
    Ingredient lines usually start with a quantity or a common unit.
    """
    text = text.lower().strip()
    # Remove leading bullet points/symbols
    text = re.sub(r'^[\s\-\*▢]+', '', text)
    
    if not text:
        return False

    # Starts with a number or fraction
    if re.match(r'^[\d½¼¾⅓⅔⅛\.]+', text):
        return True
    
    # Starts with common quantity words
    if re.match(r'^(small|medium|large|few|pinch|handful|cup|tsp|tbsp|gram|ml)\b', text):
        return True
        
    return False

def clean_measurement_in_text(text: str) -> str:
    """
    Finds measurements in text, standardizes them (ml/g), and converts to words.
    Example: "add 1 cup water" -> "add two hundred forty ml water"
    """
    # Map for unit normalization before calling unit_normalizer
    norm_unit_map = {
        "teaspoon": "tsp", "teaspoons": "tsp", "tsp": "tsp",
        "tablespoon": "tbsp", "tablespoons": "tbsp", "tbsp": "tbsp",
        "cup": "cup", "cups": "cup",
        "gram": "g", "grams": "g", "g": "g",
        "ml": "ml", "liter": "l", "liters": "l", "l": "l",
        "kg": "kg"
    }
    
    # Regex to find: [quantity] [unit] [ingredient?]
    units_pattern = r'\b(cup|cups|tsp|teaspoon|teaspoons|tbsp|tablespoon|tablespoons|gram|grams|g|ml|l|liter|liters|kg|kilogram|kilograms)\b'
    
    def replace_match(match):
        qty_str = match.group(1)
        unit_raw = match.group(2).lower()
        
        # Look ahead for a potential ingredient name (up to 2 words) to help infer category
        # match.end() gives the positions after the unit
        lookahead = text[match.end():].strip().split()
        ing_hint = " ".join(lookahead[:2]) if lookahead else "generic"
        
        # Convert qty_str to float
        qty = 0.0
        frac_map = {"½": 0.5, "¼": 0.25, "¾": 0.75, "⅓": 0.33, "⅔": 0.66, "⅛": 0.125}
        for f_char, f_val in frac_map.items():
            qty_str = qty_str.replace(f_char, str(f_val))
            
        try:
            if "/" in qty_str:
                num, den = qty_str.split("/")
                qty = float(num) / float(den)
            else:
                qty = float(qty_str)
        except:
            return match.group(0)

        # Map to standard unit symbol
        unit = norm_unit_map.get(unit_raw, unit_raw)

        # Normalize using unit_normalizer
        norm_qty, norm_unit, _ = normalize_quantity_unit(qty, unit, ing_hint)
        
        if norm_qty is not None:
            return format_measurement_as_text(norm_qty, norm_unit)
        
        return match.group(0)

    # Match qty + unit
    text = re.sub(rf'(\d+(?:/\d+)?|[½¼¾⅓⅔⅛])\s*({units_pattern})', replace_match, text)
    
    # Just convert standalone fractions to words
    frac_map = {"½": "one-half", "¼": "one-quarter", "¾": "three-quarters", "⅓": "one-third", "⅔": "two-thirds", "⅛": "one-eighth"}
    for f_char, f_words in frac_map.items():
        text = text.replace(f_char, f_words)
        
    return text


def looks_like_instruction(text: str) -> bool:
    """
    Heuristically detect whether a string is an instruction.
    """
    if not text:
        return False
    
    # If it looks like an ingredient line, it's NOT an instruction
    if looks_like_ingredient_line(text):
        return False

    text_lower = text.lower().strip()
    
    # Imperative verbs / common step starts
    if re.match(
        r'^(add|mix|stir|cook|boil|fry|pour|serve|make|heat|place|put|cover|garnish|transfer|blend|roast|saute|sauté|set|cool|blend|marinate|sprinkle|regulate|taste)\b',
        text_lower
    ):
        return True

    if len(text.split()) > 5:
        return True

    return False



# ------------------------------------
# INSTRUCTION CLEANER
# ------------------------------------
def clean_instructions(steps: list) -> list:
    """
    Clean and normalize instruction steps.
    Removes ingredient lines, strips symbols, normalizes measurements.
    """
    cleaned = []

    for step in steps:
        if not step:
            continue

        # 1. Strip noisy symbols like ▢ and leading dashes
        step = re.sub(r'[▢]', '', step)
        step = re.sub(r'^\s*[\-\*]\s*', '', step)
        step = step.strip()

        if not step:
            continue

        # 2. Filter out ingredient lines
        if looks_like_ingredient_line(step):
            continue

        # 3. Ensure it looks like an instruction
        if not looks_like_instruction(step):
            continue

        # 4. Standardize measurements and convert to text
        step = clean_measurement_in_text(step)

        cleaned.append(step)

    return cleaned

