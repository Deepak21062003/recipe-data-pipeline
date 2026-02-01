import psycopg2
from psycopg2.extras import Json


def get_connection():
    return psycopg2.connect(
        dbname="recipe_pipeline",
        user="postgres",        # change if different
        password="postgres",    # change if different
        host="localhost",
        port="5432"
    )
