from typing import Optional


def safe_int(value) -> Optional[int]:
    """
    Safely convert value to int.
    Returns None if conversion fails.
    """
    if value is None:
        return None

    try:
        value = str(value).strip()
        if not value:
            return None
        return int(float(value))
    except ValueError:
        return None


def normalize_times(recipe: dict) -> dict:
    """
    Normalize prep, cook, and total time into integer minutes.
    """

    prep_time = safe_int(recipe.get("prep_time_min"))
    cook_time = safe_int(recipe.get("cook_time_min"))
    total_time = safe_int(recipe.get("total_time_min"))

    # Derive total time if missing
    if total_time is None:
        if prep_time is not None and cook_time is not None:
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
