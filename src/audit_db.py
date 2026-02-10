from db import get_connection

def audit():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT count(*) FROM recipes WHERE instructions IS NULL OR instructions = '';")
    empty_count = cur.fetchone()[0]
    print(f"Total recipes with empty/null instructions: {empty_count}")

    cur.execute("SELECT id, name, instructions FROM recipes ORDER BY id DESC LIMIT 5;")
    rows = cur.fetchall()
    
    for row in rows:
        print(f"\nID: {row[0]} | Name: {row[1]}")
        print("-" * 20)
        # Use repr to see newlines clearly
        print(repr(row[2]))
        print("-" * 20)
        
    cur.close()
    conn.close()

if __name__ == "__main__":
    audit()
