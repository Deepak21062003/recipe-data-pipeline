# Recipe Data Pipeline Assessment

## Project Overview

This project implements an **end-to-end Python data pipeline** to ingest, clean, parse, normalize, and store recipe data into a **PostgreSQL database**, using the **provided dataset (Option A)**.

The pipeline converts **semi-structured and noisy recipe data** into a **structured relational format** suitable for querying and analysis, while handling:
- Inconsistent ingredient phrasing and unit formatting.
- Mixed ingredient–instruction text.
- Varied time formats and missing duration values.
- Duplicate ingredient entries within recipes.

---

## Data Source

- **Dataset**: `data/recipes.json`
- **Source**: Provided assessment dataset (Option A).
- **Format**: JSON list of recipe objects containing name, ingredients, prep steps, and cook steps.
- **Usage**: Used as the authoritative source for the pipeline.

---

## Project Structure

```text
recipe_pipeline/
├── data/
│   └── recipes.json          # Provided dataset
├── output_evidence/          # Verification screenshots
│   ├── recipes.png
│   ├── recipe_ingredients.png
│   ├── meals.png
│   ├── meal_recipes.png
│   └── meal_ingredients.png
├── src/
│   ├── main.py               # Pipeline orchestrator & final sanitation
│   ├── ingredient_parser.py  # Regex & Logic for ingredient extraction
│   ├── instruction_cleaner.py# Heuristics for instruction filtering
│   ├── unit_normalizer.py    # Unit conversion (g, ml, tsp, etc.)
│   ├── time_normalizer.py    # Time extraction and calculation
│   ├── standard_ingredients.py # Reference list for fuzzy matching
│   ├── db.py                 # PostgreSQL connection setup
│   └── db_insert.py          # Database insertion helpers
├── sql/
│   └── schema.sql            # Database schema (DDL)
├── README.md                 # Project documentation
└── requirements.txt          # Project dependencies
```

---

## Pipeline Architecture

The pipeline follows these distinct stages:

1. **Ingestion**
   - Loads `recipes.json` and performs structural validation.
   - Orchestrates the processing of each recipe record.

2. **Cleaning & Filtering**
   - **Instruction Filtering**: Uses heuristics to detect and skip lines in the ingredient list that are actually instructions (e.g., starting with "add", "mix", "pour").
   - **Sanitation**: Removes leading symbols (`/`, `-`, `,`), articles (`a`, `an`, `the`), and filler words.

3. **Parsing**
   - **Regex Extraction**: Separates quantity, unit, and ingredient name.
   - **Unicode Normalization**: Converts fractions like "½" to decimal "0.5".
   - **Fuzzy Matching**: Uses `rapidfuzz` to map raw ingredient names to a standardized library of ingredients.

4. **Normalization & Logic**
   - **Time Normalization**: Extracts `prep_time` and `cook_time` into integer minutes and derives `total_time`.
   - **Unit Normalization**: Standardizes diverse unit names (e.g., "tablespoon" -> "tbsp") and converts quantities to `g` for solids or `ml` for liquids.
   - **Deduplication**: Identifies and merges duplicate ingredients within a single recipe, summing quantities where units are compatible.

5. **Database Insertion**
   - Populates the five required PostgreSQL tables: `recipes`, `recipe_ingredients`, `meals`, `meal_recipes`, and `meal_ingredients`.

---

## Parsing Strategy

### Ingredient Parsing (`ingredient_parser.py`)

- **Quantity & Unit**: Regex-based extraction handles decimals, fractions, and ranges.
- **Preparation extraction**: Preparation verbs like `chopped`, `diced`, or `minced` are extracted into metadata, leaving only the ingredient noun.
- **Fuzzy Normalization**: Matches names like `tomatoe` to `tomato` using similarity scoring.

### Instruction Filtering (`instruction_cleaner.py`)

- Functions like `looks_like_instruction` identify sentences by length and the presence of imperative verbs at the start of strings.
- This ensures that only true ingredients reach the ingredient tables.

---

## Normalization Logic

### Ingredient Name Cleanup (`main.py`)

- Uses `final_cleanup_ingredient_name` to strip project-specific noise such as "recipe", "recipes", "inch piece", "handful", etc.
- Guarantees that the `ingredient_name` column in the database is clean and concise.

### Unit & Unit-less Normalization (`unit_normalizer.py`)

- Categorizes ingredients into **Solids** and **Liquids**.
- **Unit-less counts**: Maps items like "2 potatoes" to an estimated weight in grams based on average weights (e.g., 1 potato ≈ 150g).

---

## Meal Generation

- **Type Inference**: Categorizes recipes based on keyword matches:
  - **Breakfast**: `dosa`, `idli`, `poha`, `upma`, `pongal`.
  - **Lunch**: `rice`, `biryani`, `pulao`.
  - **Dinner**: Default fallback for other varieties.
- **Aggregation**: `meal_ingredients` table stores the total required quantities for the entire meal.

---

## Database Schema

The PostgreSQL schema (`sql/schema.sql`) includes:
- **`recipes`**: Stores metadata, timing, and cleaned instruction JSON.
- **`recipe_ingredients`**: Links ingredients to recipes with parsed info and optional flags.
- **`meals`**: High-level categorization of dishes.
- **`meal_recipes`**: Mapping table between meals and recipes.
- **`meal_ingredients`**: Normalized ingredient list for the entire meal.

---

## How to Run the Project

### Step 1: Create PostgreSQL database
Open your terminal or SQL client and create the database:
```sql
CREATE DATABASE recipe_pipeline;
```

### Step 2: Apply schema
Execute the schema script to create the necessary tables:
```bash
psql -d recipe_pipeline -f sql/schema.sql
```

### Step 3: Configure database credentials
Edit `src/db.py` with your PostgreSQL `username`, `password`, `host`, and `port`:
```python
# src/db.py
def get_connection():
    return psycopg2.connect(
        dbname="recipe_pipeline",
        user="your_username",
        password="your_password",
        host="localhost",
        port="5432"
    )
```

### Step 4: Run the pipeline
Execute the main script to process the data and populate the database:
```bash
python src/main.py
```

---

## Output Evidence

Verification of the pipeline's success is provided via screenshots in the `output_evidence/` directory:
- `recipes.png`: Populated recipe metadata.
- `recipe_ingredients.png`: Structured and cleaned ingredient list.
- `meals.png`: Categorized meals with extracted timing.
- `meal_recipes.png`: Relationship mapping.
- `meal_ingredients.png`: Final aggregated list of ingredients.

---

## Known Limitations

1. **Rule-Based Specificity**: The parsing logic is highly effective for English Indian recipes but may require adjustments for other cuisines or languages.
2. **Database Credentials**: Currently configured in `src/db.py`; should be environment-controlled for production use.
3. **Ambiguity**: Phrases like "salt to taste" are categorized as 0 quantity or optional, as they cannot be definitively quantified.
4. **LLM Usage**: **No external LLM APIs were used.** All parsing and normalization logic is entirely rule-based, deterministic, and locally executed.

---

## Assessment Coverage

- [x] **Python Pipeline**: Comprehensive ingestion, cleaning, and normalization.
- [x] **Ingredient Parsing**: Accurate extraction of names, quantities, and units.
- [x] **Instruction Detection**: Robust separation of steps from ingredient lists.
- [x] **Unit Normalization**: Conversion to standard metric units (g/ml).
- [x] **Meal Generation**: Automatic categorization and ingredient aggregation.
- [x] **Database Storage**: Full PostgreSQL relational schema implementation.
- [x] **Documentation**: Clear setup instructions and logic explanation.
