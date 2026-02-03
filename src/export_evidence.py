import csv
import os
from db import get_connection

def export_table_to_csv(table_name, output_path):
    conn = get_connection()
    cur = conn.cursor()
    
    # Get column names
    cur.execute(f"SELECT * FROM {table_name} LIMIT 0")
    colnames = [desc[0] for desc in cur.description]
    
    # Get all data
    cur.execute(f"SELECT * FROM {table_name}")
    rows = cur.fetchall()
    
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(colnames)
        writer.writerows(rows)
        
    print(f"Exported {table_name} to {output_path}")
    
    cur.close()
    conn.close()

if __name__ == "__main__":
    tables = [
        ("recipes", "output_evidence/recipes.csv"),
        ("recipe_ingredients", "output_evidence/recipe_ingredients.csv"),
        ("meals", "output_evidence/meals.csv"),
        ("meal_recipes", "output_evidence/meal_recipes.csv"),
        ("meal_ingredients", "output_evidence/meal_ingredients.csv")
    ]
    
    for table, path in tables:
        export_table_to_csv(table, path)
