import re
from typing import List


# -----------------------------
# Filters & Keywords
# -----------------------------

# Lines that are clearly NOT cooking steps
NOISE_KEYWORDS = [
    "follow us",
    "instagram",
    "facebook",
    "twitter",
    "youtube",
    "pinterest",
    "note:",
    "notes:",
    "substitute",
    "substitution",
    "you may",
    "you can",
    "if using",
    "optional:",
    "read notes",
    "tips:",
    "tip:",
    "variation",
    "for garnish",
    "to garnish",
    "adjust to taste",
    "skip if",
]

# Common cooking verbs (keep lines containing these)
COOKING_VERBS = [
    "heat",
    "add",
    "saute",
    "sauté",
    "fry",
    "cook",
    "boil",
    "simmer",
    "roast",
    "blend",
    "grind",
    "mix",
    "stir",
    "pour",
    "transfer",
    "serve",
    "garnish",
    "cover",
    "reduce",
    "bring",
]

# -----------------------------
# Helper Functions
# -----------------------------

def normalize_step(text: str) -> str:
    text = text.lower().strip()

    # Remove bullets and weird characters
    text = re.sub(r"[▢•–]", "", text)

    # Remove extra spaces
    text = re.sub(r"\s+", " ", text)

    return text


def is_ingredient_line(text: str) -> bool:
    """
    Detect ingredient-only lines.
    """
    # Starts with quantity/unit patterns
    if re.match(r"^\d", text):
        return True

    if any(unit in text for unit in ["cup", "cups", "tbsp", "tablespoon", "teaspoon", "grams", "kg", "ml"]):
        return True

    return False


def is_noise(text: str) -> bool:
    return any(keyword in text for keyword in NOISE_KEYWORDS)


def is_cooking_step(text: str) -> bool:
    return any(verb in text for verb in COOKING_VERBS)


# -----------------------------
# Main Cleaner
# -----------------------------

def clean_instructions(raw_steps: List[str]) -> List[str]:
    """
    Input: raw steps from dataset (prep_steps / cook_steps)
    Output: clean cooking steps only
    """

    clean_steps = []

    for step in raw_steps:
        text = normalize_step(step)

        # Skip empty
        if not text:
            continue

        # Remove ingredient lines
        if is_ingredient_line(text):
            continue

        # Remove noise
        if is_noise(text):
            continue

        # Keep only cooking actions
        if not is_cooking_step(text):
            continue

        # Capitalize first letter for readability
        clean_steps.append(text.capitalize())

    return clean_steps


# -----------------------------
# Manual Test
# -----------------------------
if __name__ == "__main__":
    sample_steps = [
        "▢ 500 grams (1.1 lbs.) chicken (bone-in or boneless)",
        "▢ ¾ cup onions (thinly sliced)",
        "Heat a pan on a low flame.",
        "Add onions & fry until golden.",
        "Follow us on Instagram",
        "Serve with rice or roti."
    ]

    cleaned = clean_instructions(sample_steps)
    for step in cleaned:
        print(step)


if __name__ == "__main__":
    import os
    import json

    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    DATA_PATH = os.path.join(BASE_DIR, "data", "recipes.json")

    with open(DATA_PATH, "r") as f:
        data = json.load(f)

    recipe = data[0]  # first recipe only

    prep_steps = json.loads(recipe["prep_steps"])

    cleaned = clean_instructions(prep_steps)

    print("\nCLEANED STEPS:\n")
    for step in cleaned[:10]:
        print("-", step)


