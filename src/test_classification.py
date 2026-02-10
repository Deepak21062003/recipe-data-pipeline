from ai_processor import classify_steps
import json

steps = [
    "Wash the rice",
    "Soak for 30 mins",
    "Heat water in a pot",
    "Add rice to boiling water",
    "Cook until tender",
    "Drain and serve"
]

res = classify_steps(steps)
print(json.dumps(res, indent=2))
