# Recipe Data Pipeline Assessment

## Project Overview

This project implements an **end-to-end Python data pipeline** to ingest, clean, parse, normalize, and store recipe data into a **PostgreSQL database**, using the **provided dataset (Option A)**.

The pipeline converts **semi-structured and noisy recipe data** into a **structured relational format** suitable for querying and analysis, while handling:
- inconsistent ingredient phrasing
- mixed ingredient–instruction text
- varied step formats
- missing or ambiguous values

---

## Data Source

- **Dataset**: `data/recipes.json`
- **Source**: Provided assessment dataset (Option A)
- **Format**: JSON list of recipe objects
- **Usage**: Used as-is (no external scraping or augmentation)

---

## Project Structure

recipe_pipeline/
├── data/
│ └── recipes.json # Provided dataset
│
├── output_evidence/ # SQL query screenshots
│ ├── recipes.png
│ ├── recipe_ingredients.png
│ ├── meals.png
│ ├── meal_recipes.png
│ └── meal_ingredients.png
│
├── src/
│ ├── main.py # Pipeline orchestrator
│ ├── ingredient_parser.py # Ingredient parsing logic
│ ├── instruction_cleaner.py # Instruction cleaning
│ ├── time_normalizer.py # Time normalization
│ ├── db.py # PostgreSQL connection
│ └── db_insert.py # DB insert helpers
│
├── sql/
│ └── schema.sql # Database schema (DDL)
│
├── README.md
└── requirements.txt



---

## Pipeline Architecture

The pipeline follows these stages:

1. **Ingestion**
   - Loads `recipes.json`
   - Validates dataset structure

2. **Cleaning**
   - Removes instruction-like lines from ingredient lists
   - Normalizes symbols, casing, and punctuation

3. **Parsing**
   - Extracts ingredient name, quantity, and unit
   - Separates preparation/context into metadata

4. **Normalization**
   - Normalizes ingredient spellings and formats
   - Converts time fields into minutes
   - Deduplicates recipes by name

5. **Database Insertion**
   - Inserts records into PostgreSQL tables:
     - `recipes`
     - `recipe_ingredients`
     - `meals`
     - `meal_recipes`
     - `meal_ingredients`

---

## Parsing Strategy

### Ingredient Parsing

- Splits raw text into:
  - **ingredient_name** (clean noun phrase)
  - **ingredient_info** (notes, preparation, alternatives)

**Examples:**
- `to onion` → `onion`
- `coffee powder for strong coffee`  
  → ingredient: `coffee powder`  
  → notes: `for strong coffee`
- `add milk to saucepan`  
  → ingredient: `milk`  
  → notes: `add milk to saucepan`

### Instruction Filtering

- Lines starting with verbs such as:
  - `add`, `pour`, `serve`, `make`, `cover`, etc.
- These lines are **never treated as ingredients**.

---

## Normalization Logic

### Ingredient Normalization

- Removes:
  - leading symbols (`/`, `-`, `,`)
  - filler phrases (`a pinch`, `a handful`, `inch piece`)
- Standardizes spelling:
  - `tomatoe` → `tomato`
  - `chilie` → `chili`
  - `curry leave` → `curry leaves`

### Time Normalization

- Converts time information into:
  - `prep_time_minutes`
  - `cook_time_minutes`
  - `total_time_minutes`

### Time Conversion Assumptions and Rounding Rules

- All time-related fields (`prep_time_min`, `cook_time_min`, `total_time_min`) are assumed to be expressed in **minutes** in the provided dataset.
- Time values may appear as strings, floats, or be missing.
- Non-numeric or empty values are treated as `NULL`.
- If `total_time` is missing but both `prep_time` and `cook_time` are present, total time is derived as:

### total_time = prep_time + cook_time
#### Rounding Rules
- Time values are converted using **floor conversion**:
- `"30.9"` → `30`
- `"45.0"` → `45`
- No rounding up is performed.
- This ensures consistent integer-minute representation across all records.

---

## Meal Generation

- Meal type inferred from recipe name:
  - **Breakfast** → dosa, idli, upma, pongal, etc.
  - **Lunch** → rice, biryani, pulao
  - **Dinner** → default fallback
- Each recipe generates a corresponding meal
- Meal–ingredient relationships are derived from recipe ingredients

---

## Database Schema

The PostgreSQL schema is defined in:
##sql/schema.sql
Tables created:
- `recipes`
- `recipe_ingredients`
- `meals`
- `meal_recipes`
- `meal_ingredients`

All required tables are populated by the pipeline.

---

## How to Run the Project

### Install dependencies
```bash
pip install -r requirements.txt

###Create database schema
psql -d recipe_pipeline -f sql/schema.sql

##Run the pipeline
python src/main.py

##Verification Queries
SELECT COUNT(*) FROM recipes;
SELECT COUNT(*) FROM recipe_ingredients;
SELECT COUNT(*) FROM meals;
SELECT COUNT(*) FROM meal_recipes;
SELECT COUNT(*) FROM meal_ingredients;

##Output Evidence
Screenshots demonstrating successful execution are available in output_evidence/:
    .recipes.png
    .recipe_ingredients.png
    .meals.png
    .meal_recipes.png
    .meal_ingredients.png

##Known Limitations
1.Ambiguous ingredient descriptions
  Phrases such as a pinch, inch piece, or a few leaves are preserved when ambiguity exists.
  The pipeline prioritizes recall over aggressive deletion.

2.Heuristic-based parsing
  Ingredient vs instruction detection relies on rule-based logic and may not cover all edge cases.

##LLM Usage
  .No external LLM APIs were used.
  .All parsing and normalization logic is rule-based and deterministic.

###Assessment Coverage Summary
  .Python ingestion → cleaning → parsing → normalization → DB insertion
  .SQL schema (DDL)
  .Inserted records in all required tables
  .Output evidence screenshots
  .Cross-format and inconsistent phrasing handled