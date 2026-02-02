import re
from typing import Dict, Optional
from rapidfuzz import process, fuzz
from standard_ingredients import STANDARD_INGREDIENTS

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
    "teaspoon": "tsp", "teaspoons": "tsp", "tsp": "tsp",
    "tablespoon": "tbsp", "tablespoons": "tbsp", "tbsp": "tbsp",
    "cup": "cup", "cups": "cup",
    "ml": "ml", "l": "l",
    "gram": "g", "grams": "g", "g": "g",
    "kilogram": "kg", "kilograms": "kg", "kg": "kg",
    "lb": "lb", "lbs": "lb", "pound": "lb", "pounds": "lb",
    "pinch": "pinch", "pinches": "pinch"
}

OPTIONAL_KEYWORDS = {"optional", "to taste", "as needed", "as required"}

PREPARATION_WORDS = [
    "chopped", "sliced", "minced", "grated",
    "crushed", "diced", "finely chopped",
    "fresh", "dried", "whole", "raw", "ripe",
    "peeled", "deseeded", "boiled",
    "fine", "finely"
]

# -----------------------------
# Helpers
# -----------------------------
def normalize_text(text: str) -> str:
    text = text.lower().strip()
    for k, v in UNICODE_FRACTIONS.items():
        text = text.replace(k, str(v))
    return text.replace("▢", "").strip()


def extract_quantity(text: str) -> Optional[float]:
    # (divided 1+2)
    divided = re.search(r'divided\s*([\d+\.]+)', text)
    if divided:
        nums = re.findall(r'\d+(?:\.\d+)?', divided.group(1))
        return sum(map(float, nums)) if nums else None

    # 1 + 2
    if "+" in text:
        nums = re.findall(r'\d+(?:\.\d+)?', text)
        return sum(map(float, nums)) if nums else None

    # fraction 1/2
    frac = re.search(r'(\d+)\s*/\s*(\d+)', text)
    if frac:
        return float(frac.group(1)) / float(frac.group(2))

    # decimal / int
    num = re.search(r'\d+(\.\d+)?', text)
    return float(num.group()) if num else None


def extract_unit(text: str) -> Optional[str]:
    for raw, norm in UNIT_MAP.items():
        if re.search(rf"\b{raw}\b", text):
            return norm
    return None


def detect_optional(text: str) -> bool:
    return any(k in text for k in OPTIONAL_KEYWORDS)


def extract_preparation(text: str):
    prep = []
    for p in PREPARATION_WORDS:
        if p in text:
            prep.append(p)
            text = text.replace(p, "")
    return prep, text


def clean_ingredient_name(text: str) -> str:
    text = re.sub(r'\d+(\.\d+)?', '', text)
    text = re.sub(r'\d+\s*/\s*\d+', '', text)

    for raw in UNIT_MAP.keys():
        text = re.sub(rf"\b{raw}\b", "", text)

    for kw in OPTIONAL_KEYWORDS:
        text = text.replace(kw, "")

    for p in PREPARATION_WORDS:
        text = text.replace(p, "")

    text = re.sub(r'\(.*?\)', '', text)
    text = re.sub(r'\s+', ' ', text)
    text = text.strip()

    # Fuzzy matching against standard ingredients
    best_match = process.extractOne(
        text,
        STANDARD_INGREDIENTS,
        scorer=fuzz.WRatio
    )

    if best_match:
        match, score, _ = best_match
        if score >= 80:
            return match

    return text


# -----------------------------
# Main Parser
# -----------------------------
def parse_ingredient(raw_text: str) -> Dict:
    text = normalize_text(raw_text)

    is_optional = detect_optional(text)

    prep, text = extract_preparation(text)

    quantity = extract_quantity(text)
    unit = extract_unit(text)

    if quantity is None:
        unit = None

    ingredient_name = clean_ingredient_name(text)

    info = {}
    if prep:
        info["preparation"] = prep

    return {
        "ingredient_name": ingredient_name,
        "quantity": quantity,
        "unit": unit,
        "is_optional": is_optional,
        "ingredient_info": info
    }
