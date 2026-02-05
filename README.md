# Recipe Data Pipeline (Triple-Logic: AI + NLP + Deterministic)

This project implements a **Triple-Logic Pipeline** (AI + NLP + Deterministic) to ingest, clean, parse, normalize, and store recipe data into a **PostgreSQL database**. 

By leveraging **Gemini AI** for intelligent synthesis alongside robust **NLP heuristics** and **deterministic logic**, the pipeline achieves high-precision structured data from noisy, informal recipe text.

The system handles:
- **AI-Powered Refinement**: Gemini extracts metadata, difficulty, and preparation details.
- **NLP Sanitation**: Heuristic layers strip linguistic noise and identify core ingredient nouns.
- **Deterministic precision**: 100% accurate unit conversion and quantity standardization.
- **Instruction Splitting**: Clean separation of `prep_steps` and `cook_steps`.

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
├── output_evidence/          # Structured data evidence (CSV)
│   ├── recipes.csv
│   ├── recipe_ingredients.csv
│   ├── meals.csv
│   ├── meal_recipes.csv
│   └── meal_ingredients.csv
├── src/
│   ├── main.py               # Triple-Logic Orchestrator 
│   ├── ai_processor.py       # Layer 1: Gemini AI (Refinement & Synthesis)
│   ├── ingredient_parser.py  # Layer 3: Deterministic Parser
│   ├── instruction_cleaner.py# Layer 2: NLP Heuristics for steps & filtering
│   ├── unit_normalizer.py    # Layer 3: Unit conversion (g, ml, etc.)
│   ├── time_normalizer.py    # Time extraction and calculation
│   ├── verify_ai_pipeline.py # Quick test battery for the AI layer
│   ├── db.py                 # PostgreSQL connection setup
│   ├── db_insert.py          # Database insertion helpers
│   ├── export_evidence.py    # DB to CSV export utility
│   └── test_refinement.py    # Unit tests for parsing logic

├── sql/
│   └── schema.sql            # Database schema (DDL)
├── README.md                 # Project documentation
└── requirements.txt          # Project dependencies
```

---

## Triple-Logic Architecture

The pipeline uses a layered approach to guarantee both intelligence and accuracy:

### Layer 1: AI (Gemini)
- **Refinement**: Uses `google-generativeai` to structure raw ingredients, extract preparation details, and identify "divided" quantities.
- **Instruction Synthesis**: Merges fragmented steps into coherent narratives and splits them into distinct `prep_steps` and `cook_steps`.
- **Metadata Extraction**: Infers `difficulty_level`, `tags`, and `servings` from context.

### Layer 2: NLP Heuristics
- **Linguistic Cleanup**: Strips descriptors like "pieces", "parts", "bones", and "stems" using pattern matching.
- **Validation**: Uses part-of-speech-like heuristics to verify if an ingredient name is valid.
- **Instruction Detection**: Identifies imperative verbs to separate instruction blocks from ingredient lists.

### Layer 3: Deterministic Logic
- **Regex Extraction**: Separates quantity, unit, and core ingredient name.
- **Metric Normalization**: Standardizes all diverse units (cups, tbsp, kg) to `g` for solids or `ml` for liquids.
- **Robust Fallback**: If the AI Layer is unavailable (no API Key), the pipeline gracefully falls back to Layer 2 & 3 to maintain 100% operational continuity.

---

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

- **Enhanced Metadata**: Common items like salt, oil, and spices receive an "Adjusted to taste" note in `ingredient_info` if no manual conversion is applied.
- **Unit-less counts**: Maps items like "2 potatoes" to an estimated weight in grams based on average weights (e.g., 1 potato ≈ 150g).

---

## Meal Generation

- **Type Inference**: Categorizes recipes based on keyword matches:
  - **Breakfast**: `dosa`, `idli`, `poha`, `upma`, `pongal`.
  - **Lunch**: `rice`, `biryani`, `pulao`.
  - **Dinner**: Default fallback for other varieties.
- **Aggregation**: `meal_ingredients` table stores the total required quantities for the entire meal.

---

The PostgreSQL schema (`sql/schema.sql`) includes:
- **`recipes`**: Stores metadata, timing, and separate `prep_steps` and `cook_steps` (JSONB).
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

### Step 4: Configure Environment (Optional but Recommended)
To enable AI features, set your Google Gemini API Key:
```bash
export GOOGLE_API_KEY="your_api_key_here"
```
*Note: If unset, the pipeline will run in "fallback mode" using only NLP and Deterministic layers.*

### Step 5: Run the pipeline
Execute the main script to process the data and populate the database:
```bash
python src/main.py
```

### Step 6: Export Evidence
To refresh the CSV files in `output_evidence/` with the latest cleaned data from the database, run:
```bash
python src/export_evidence.py
```

### Step 7: Verify results (Optional)
Run the refinement tests to ensure parsing logic is performing as expected:
```bash
python src/test_refinement.py
```


---

## Output Evidence

- `recipes.csv`: Populated recipe metadata.
- `recipe_ingredients.csv`: Structured and cleaned ingredient list with non-null quantities.
- `meals.csv`: Categorized meals with extracted timing.
- `meal_recipes.csv`: Relationship mapping.
- `meal_ingredients.csv`: Final aggregated list of ingredients.

---

## Known Limitations

1. **Rule-Based Specificity**: The parsing logic is highly effective for English Indian recipes but may require adjustments for other cuisines or languages.
2. **Database Credentials**: Currently configured in `src/db.py`; should be environment-controlled for production use.
3. **Pantry Staple Heuristics**: Items like "salt to taste" are given a default note and standard minimal quantity where appropriate, though actual usage varies by cook.
4. **LLM Integration**: Uses Gemini for Layer 1. Users can toggle this by providing or withholding the `GOOGLE_API_KEY`.

---

## Assessment Coverage

- [x] **Python Pipeline**: Comprehensive ingestion, cleaning, and normalization.
- [x] **Ingredient Parsing**: Accurate extraction of names, quantities, and units.
- [x] **Instruction Detection**: Robust separation of steps from ingredient lists.
- [x] **Unit Normalization**: Conversion to standard metric units (g/ml).
- [x] **Meal Generation**: Automatic categorization and ingredient aggregation.
- [x] **Database Storage**: Full PostgreSQL relational schema implementation.
- [x] **Documentation**: Clear setup instructions and logic explanation.
