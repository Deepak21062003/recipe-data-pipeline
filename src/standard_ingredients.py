# List of standard ingredient names for fuzzy matching
STANDARD_INGREDIENTS_SET = {
    "chicken", "onion", "tomato", "garlic", "ginger", "potato", "carrot",
    "capsicum", "chili", "green chili", "red chili", "turmeric", "cumin", "coriander", "salt", "sugar",
    "oil", "ghee", "butter", "milk", "curd", "yogurt", "cream", "paneer",
    "rice", "flour", "wheat", "dal", "moong dal", "urad dal", "chana dal", "toor dal", "lentil", "mustard", "fenugreek",
    "cardamom", "clove", "cinnamon", "pepper", "black pepper", "saffron", "cashew", "almond",
    "raisin", "coconut", "lemon", "lime", "water", "egg", "fish", "mutton",
    "spinach", "pea", "green peas", "bean", "cauliflower", "cabbage", "brinjal", "okra",
    "mushroom", "corn", "cheese", "bread", "mayonnaise", "ketchup", "sauce",
    "vinegar", "soy", "noodles", "pasta", "tea", "coffee", "chocolate",
    "vanilla", "baking", "yeast", "curry leaves", "mint", "cilantro",
    "instant coffee", "coffee powder", "ice cubes", "raw sugar", "instant coffee powder"
}

# Sorted by length descending to match more specific terms first
STANDARD_INGREDIENTS = sorted(list(STANDARD_INGREDIENTS_SET), key=len, reverse=True)
