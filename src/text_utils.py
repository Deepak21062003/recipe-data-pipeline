def number_to_words(n):
    """
    Simple converter for numbers to English words.
    Supports up to 999,999 for recipe quantities.
    """
    if n == 0: return "zero"
    
    units = ["", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine"]
    teens = ["ten", "eleven", "twelve", "thirteen", "fourteen", "fifteen", "sixteen", "seventeen", "eighteen", "nineteen"]
    tens = ["", "", "twenty", "thirty", "forty", "fifty", "sixty", "seventy", "eighty", "ninety"]
    
    def _to_999(num):
        words = []
        if num >= 100:
            words.append(units[int(num // 100)])
            words.append("hundred")
            num %= 100
            if num > 0:
                words.append("and")
        
        if 10 <= num < 20:
            words.append(teens[int(num - 10)])
        else:
            if num >= 20:
                words.append(tens[int(num // 10)])
                num %= 10
            if num > 0:
                words.append(units[int(num)])
        return words

    final_words = []
    
    # Thousands
    if n >= 1000:
        thousand_part = int(n // 1000)
        final_words.extend(_to_999(thousand_part))
        final_words.append("thousand")
        n %= 1000
        
    if n > 0:
        # Avoid "and" duplication if thousand part didn't end with "and"
        final_words.extend(_to_999(n))
            
    return " ".join(final_words).strip()


def fraction_to_words(f_str):
    """
    Converts fractions like '3/4' or '¾' to words.
    """
    frac_map = {
        "1/2": "one-half", "0.5": "one-half", "½": "one-half",
        "1/4": "one-quarter", "0.25": "one-quarter", "¼": "one-quarter",
        "3/4": "three-quarters", "0.75": "three-quarters", "¾": "three-quarters",
        "1/3": "one-third", "0.33": "one-third", "⅓": "one-third",
        "2/3": "two-thirds", "0.66": "two-thirds", "⅔": "two-thirds",
        "1/8": "one-eighth", "0.125": "one-eighth", "⅛": "one-eighth"
    }
    return frac_map.get(f_str, f_str)

def format_measurement_as_text(qty, unit):
    """
    Converts a quantity and unit to a clean text string.
    Example: (1.5, 'cup') -> 'one and one-half cups'
    Example: (500, 'g') -> 'five hundred g'
    """
    if qty is None:
        return unit if unit else ""
    
    if isinstance(qty, str):
        try:
            qty = float(qty)
        except ValueError:
            return f"{qty} {unit}" if unit else str(qty)

    whole = int(qty)
    frac = qty - whole
    
    parts = []
    if whole > 0:
        parts.append(number_to_words(whole))
        
    if frac > 0:
        if whole > 0:
            parts.append("and")
        # Handle common fractions
        if round(frac, 2) == 0.5: parts.append("one-half")
        elif round(frac, 2) == 0.25: parts.append("one-quarter")
        elif round(frac, 2) == 0.75: parts.append("three-quarters")
        elif round(frac, 2) == 0.33: parts.append("one-third")
        elif round(frac, 2) == 0.66: parts.append("two-thirds")
        else: parts.append(str(round(frac, 2)))
        
    result = " ".join(parts)
    if unit:
        result += f" {unit}"
        
    return result
