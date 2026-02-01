import re
from typing import Dict, Optional

# -----------------------------
# Constants
# -----------------------------

UNICODE_FRACTIONS = {
    "½": 0.5,
    "¼": 0.25,
    "¾": 0.75,
    "⅓": 0.33,
    "⅔": 0.66,
    "⅛": 0.125
}

UNIT_MAP = {
    "tablespoon": "tbsp",
    "tablespoons": "tbsp",
    "tbsp": "tbsp",
    "teaspoon": "tsp",
    "teaspoons": "tsp",
    "tsp": "tsp",
    "cup": "cup",
    "cups": "cup",
    "gram": "g",
    "grams": "g",
    "g": "g",
    "kg": "kg",
    "kilogram": "kg",
    "kilograms": "kg",
    "lb": "lb",
    "lbs": "lb",
    "pound": "lb",
    "pounds": "lb",
    "ml": "ml",
    "l": "l"
}

OPTIONAL_KEYWORDS = [
    "optional",
    "if needed",
    "to taste",
    "as required"
]

TASTE_PHRASES = [
    "to taste",
    "as needed",
    "as required"
]

SIZE_WORDS = [
    "small",
    "medium",
    "large"
]

PREPARATION_WORDS = [
    "thinly sliced",
    "finely chopped",
    "chopped",
    "sliced",
    "minced",
    "diced"
]

# -----------------------------
# Helper Functions
# -----------------------------

def normalize_text(text: str) -> str:
    text = text.lower().strip()
    for k, v in UNICODE_FRACTIONS.items():
        text = text.replace(k, str(v))
    text = text.replace("▢", "").strip()
    return text


def extract_quantity(text: str) -> Optional[float]:
    """
    Extract quantity ONLY if it is not inside brackets.
    Handles:
    - 1
    - 1.5
    - 1/2
    - 1 + 2
    """

   # Handle divided quantities like (divided 1+2)
    brackets = re.findall(r"\((.*?)\)", text)
    for bc in brackets:
        if "divided" in bc and re.search(r"\d", bc):
            nums = re.findall(r"\d+(?:\.\d+)?", bc)
            if nums:
                return sum(map(float, nums))

    # Ignore other bracket-only numeric info
    for bc in brackets:
        if re.search(r"\d", bc):
         return None


    # Handle 1 + 2
    if "+" in text:
        numbers = re.findall(r"\d+(?:\.\d+)?", text)
        if numbers:
            return sum(map(float, numbers))

    # Handle fraction 1/2
    frac_match = re.search(r"(\d+)\s*/\s*(\d+)", text)
    if frac_match:
        return float(frac_match.group(1)) / float(frac_match.group(2))

    # Handle decimal / integer
    num_match = re.search(r"\d+(\.\d+)?", text)
    if num_match:
        return float(num_match.group())

    return None


def extract_unit(text: str) -> Optional[str]:
    for raw, normalized in UNIT_MAP.items():
        if re.search(rf"\b{raw}\b", text):
            return normalized
    return None


def detect_optional(text: str) -> bool:
    return any(keyword in text for keyword in OPTIONAL_KEYWORDS)


def extract_extra_info(text: str) -> Dict:
    info = {}
    bracket_match = re.findall(r"\((.*?)\)", text)
    cleaned_notes = []

    for note in bracket_match:
        # Skip numeric-only notes
        if not re.search(r"\d", note):
            cleaned_notes.append(note.strip())

    if cleaned_notes:
        info["notes"] = " ".join(cleaned_notes)

    return info


def clean_ingredient_name(text: str) -> str:
    # Remove taste phrases
    for phrase in TASTE_PHRASES:
        text = text.replace(phrase, "")

    # Remove quantities
    text = re.sub(r"\d+(\.\d+)?", "", text)
    text = re.sub(r"\d+\s*/\s*\d+", "", text)

    # Remove unit words
    for raw in UNIT_MAP.keys():
        text = re.sub(rf"\b{raw}\b", "", text)

    # Remove size words
    for word in SIZE_WORDS:
        text = re.sub(rf"\b{word}\b", "", text)

    # Remove brackets
    text = re.sub(r"\(.*?\)", "", text)

    # Normalize spaces
    text = re.sub(r"\s+", " ", text).strip()

    # Naive singularization
    if text.endswith("s"):
        text = text[:-1]

    return text


# -----------------------------
# Main Parser
# -----------------------------

def parse_ingredient(raw_text: str) -> Dict:
    text = normalize_text(raw_text)

    extra_info = extract_extra_info(text)

    # Extract preparation words
    prep_notes = []
    for prep in PREPARATION_WORDS:
        if prep in text:
            prep_notes.append(prep)
            text = text.replace(prep, "")

    if prep_notes:
        extra_info["preparation"] = prep_notes

    quantity = extract_quantity(text)
    unit = extract_unit(text)
    is_optional = detect_optional(text)

    # Rule: No quantity → no unit
    if quantity is None:
        unit = None

    ingredient_name = clean_ingredient_name(text)

    return {
        "ingredient_name": ingredient_name,
        "quantity": quantity,
        "unit": unit,
        "is_optional": is_optional,
        "ingredient_info": extra_info
    }


# -----------------------------
# Manual Test
# -----------------------------
if __name__ == "__main__":
    samples = [
        "½ cup onions thinly sliced",
        "tablespoons oil (divided 1+2)",
        "grams (1.1 lbs.) chicken (bone-in or boneless)",
        "salt to taste"
    ]

    for s in samples:
        print(s)
        print(parse_ingredient(s))
        print("-" * 50)
