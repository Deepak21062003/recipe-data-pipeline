import re
from typing import Optional

def extract_servings(servings_str) -> Optional[int]:
    """
    Extracts a single integer serving size from a string.
    Handles: "4", "Serves: 4", "4-6 servings", "6 persons".
    Returns the lower bound if a range is provided.
    """
    if servings_str is None:
        return None
    
    if isinstance(servings_str, (int, float)):
        return int(servings_str)

    s = str(servings_str).lower().strip()
    
    # 1. Look for numbers
    match = re.search(r'(\d+)', s)
    if match:
        return int(match.group(1))
        
    return None

def extract_minutes(time_str: str) -> Optional[int]:
    """
    Extract minutes from strings like "1 hour", "45 mins", "1h 30m".
    """
    if not time_str:
        return None
    
    time_str = str(time_str).lower().strip()
    
    # 1. Total minutes match (e.g. "90")
    if time_str.isdigit():
        return int(time_str)

    total_mins = 0
    found = False

    # 2. Extract hours
    hrs_match = re.search(r'(\d+(?:\.\d+)?)\s*(?:hour|hours|hr|hrs|h)\b', time_str)
    if hrs_match:
        total_mins += int(float(hrs_match.group(1)) * 60)
        found = True

    # 3. Extract minutes
    mins_match = re.search(r'(\d+(?:\.\d+)?)\s*(?:minute|minutes|min|mins|m)\b', time_str)
    if mins_match:
        total_mins += int(float(mins_match.group(1)))
        found = True

    return total_mins if found else None

def normalize_times(recipe: dict) -> dict:
    """
    Normalize prep, cook, and total time into integer minutes.
    """
    prep_raw = recipe.get("prep_time_min") or recipe.get("prep_time") or recipe.get("preptime")
    cook_raw = recipe.get("cook_time_min") or recipe.get("cook_time") or recipe.get("cooktime")
    total_raw = recipe.get("total_time_min") or recipe.get("total_time") or recipe.get("totaltime")

    prep_time = extract_minutes(prep_raw)
    cook_time = extract_minutes(cook_raw)
    total_time = extract_minutes(total_raw)

    # Derive total time if missing
    if total_time is None and prep_time is not None and cook_time is not None:
        total_time = prep_time + cook_time

    return {
        "prep_time_minutes": prep_time,
        "cook_time_minutes": cook_time,
        "total_time_minutes": total_time
    }
if __name__ == "__main__":
    sample = {
        "prep_time_min": "20",
        "cook_time_min": "30",
        "total_time_min": ""
    }

    print(normalize_times(sample))
