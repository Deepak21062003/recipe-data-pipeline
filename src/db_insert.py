from psycopg2.extras import Json
from db import get_connection
import re

def insert_recipe(cur, recipe):
    cur.execute(
        """
        INSERT INTO recipes (
            name,
            description,
            instructions,
            prep_time_minutes,
            cook_time_minutes,
            total_time_minutes,
            servings,
            difficulty_level,
            tags,
            metadata
        )
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
        RETURNING id
        """,
        (
            recipe["recipe_name"],
            None,
            Json(recipe["instructions"]),
            recipe["prep_time_minutes"],
            recipe["cook_time_minutes"],
            recipe["total_time_minutes"],
            None,
            None,
            None,
            None
        )
    )
    return cur.fetchone()[0]


def insert_recipe_ingredients(cur, recipe_id, ingredients):
    for idx, ing in enumerate(ingredients):

        # 🔒 HARD GUARDS (CRITICAL)
        if not isinstance(ing, dict):
            continue

        name = ing.get("ingredient_name")

        # FINAL SAFETY CLEAN (DB boundary)
        if name:
            name = re.sub(r'^[,/.\-\s]+', '', name).strip()
            name = re.sub(r'^for\s+.*', '', name).strip()

        if not name:
            continue

        # Drop sentences / instruction leaks
        if len(name.split()) > 6:
            continue

        cur.execute(
            """
            INSERT INTO recipe_ingredients (
                recipe_id,
                ingredient_name,
                ingredient_info,
                is_optional,
                order_index
            )
            VALUES (%s,%s,%s,%s,%s)
            """,
            (
                recipe_id,
                name,
                Json(ing.get("ingredient_info", {})),
                ing.get("is_optional", False),
                idx
            )
        )

#meal insert functions
def insert_meal(cur, meal):
    cur.execute(
        """
        INSERT INTO meals (
            name,
            meal_type,
            total_time_minutes
        )
        VALUES (%s, %s, %s)
        RETURNING id
        """,
        (
            meal["name"],
            meal["meal_type"],
            meal["total_time_minutes"]
        )
    )
    return cur.fetchone()[0]


def insert_meal_recipe(cur, meal_id, recipe_id, recipe_name):
    cur.execute(
        """
        INSERT INTO meal_recipes (
            meal_id,
            recipe_id,
            recipe_name,
            is_main_dish
        )
        VALUES (%s, %s, %s, %s)
        """,
        (
            meal_id,
            recipe_id,
            recipe_name,
            True
        )
    )



import json

def insert_meal_ingredients(cur, meal_id, ingredients):
    for ing in ingredients:

        # 🔒 HARD GUARDS (CRITICAL)
        if not isinstance(ing, dict):
            continue

        name = ing.get("ingredient_name")
        if not name:
            continue

        if len(name.split()) > 6:
            continue

        cur.execute(
            """
            INSERT INTO meal_ingredients (
                meal_id,
                ingredient_name,
                quantity,
                unit,
                is_optional
            )
            VALUES (%s, %s, %s, %s, %s)
            """,
            (
                meal_id,
                name,
                ing.get("quantity"),
                ing.get("unit"),
                ing.get("is_optional", False),
            )
        )
