from db import get_connection

def search_recipes(query: str):
    conn = get_connection()
    cur = conn.cursor()
    
    query = query.lower()
    
    # Simple Keyword Search Logic ("AI")
    
    if "how many" in query and "recipes" in query:
        cur.execute("SELECT COUNT(*) FROM recipes;")
        count = cur.fetchone()[0]
        return f"I have {count} recipes in my database."
        
    if "quick" in query or "fast" in query:
        cur.execute("SELECT name, total_time_minutes FROM recipes WHERE total_time_minutes < 30 ORDER BY total_time_minutes ASC LIMIT 5;")
        recipes = cur.fetchall()
        if not recipes:
            return "No quick recipes found."
        return "Here are some quick recipes (under 30 mins):\n" + "\n".join([f"- {r[0]} ({r[1]} mins)" for r in recipes])

    if "ingredient" in query or "with" in query:
        # Extract potential ingredient from query (naive split)
        words = query.split()
        target = words[-1] # simplistic assumption
        cur.execute(
            """
            SELECT DISTINCT r.name 
            FROM recipes r
            JOIN recipe_ingredients ri ON r.id = ri.recipe_id
            WHERE ri.ingredient_name ILIKE %s
            LIMIT 5;
            """,
            (f"%{target}%",)
        )
        recipes = cur.fetchall()
        if not recipes:
            return f"I couldn't find recipes with {target}."
        return f"Here are recipes with {target}:\n" + "\n".join([f"- {r[0]}" for r in recipes])
        
    # Default Name Search
    cur.execute("SELECT name FROM recipes WHERE name ILIKE %s LIMIT 5;", (f"%{query}%",))
    recipes = cur.fetchall()
    
    conn.close()
    
    if not recipes:
        return "I'm sorry, I couldn't find a recipe matching that."
        
    return "Here is what I found:\n" + "\n".join([f"- {r[0]}" for r in recipes])

if __name__ == "__main__":
    print("Recipe AI: Hello! Ask me anything about your recipes.")
    while True:
        user_input = input("You: ")
        if user_input.lower() in ["exit", "quit", "bye"]:
            print("Recipe AI: Goodbye!")
            break
        response = search_recipes(user_input)
        print(f"Recipe AI: {response}")
