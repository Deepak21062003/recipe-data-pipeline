import re

# ------------------------------------
# INSTRUCTION DETECTION
# ------------------------------------
def looks_like_instruction(text: str) -> bool:
    """
    Heuristically detect whether a string is an instruction
    rather than an ingredient.

    Design goals:
    - No dataset-specific hardcoding
    - Works for future recipes
    - Prefer false-negatives over false-positives
    """

    if not text:
        return True

    text = text.lower().strip()
    words = text.split()

    # --------------------------------
    # 1️⃣ Sentence-like length
    # Ingredients are usually short noun phrases
    # --------------------------------
    if len(words) > 5:
        return True

    # --------------------------------
    # 2️⃣ Imperative verb at start
    # (common cooking instructions)
    # --------------------------------
    if re.match(
        r'^(add|adding|mix|mixing|stir|stirring|'
        r'cook|cooking|boil|boiling|fry|frying|'
        r'pour|serve|make|making|heat|heating|'
        r'place|put|cover|garnish)\b',
        text
    ):
        return True

    # --------------------------------
    # 3️⃣ Instruction connectors
    # --------------------------------
    if re.search(
        r'\b(until|before|after|when|while|then|'
        r'well|carefully|slowly|immediately)\b',
        text
    ):
        return True

    # --------------------------------
    # 4️⃣ Explicit instructional phrasing
    # --------------------------------
    if text.startswith("to "):
        return True

    if "serve with" in text or "serve hot" in text:
        return True

    return False


# ------------------------------------
# INSTRUCTION CLEANER
# ------------------------------------
def clean_instructions(steps: list) -> list:
    """
    Clean and normalize instruction steps.
    Removes empty lines and trims whitespace.
    """
    cleaned = []

    for step in steps:
        if not step:
            continue

        step = step.strip()
        if step:
            cleaned.append(step)

    return cleaned
