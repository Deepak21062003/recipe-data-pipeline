# Adaptive Hybrid Recipe Pipeline (AI-Assisted + Deterministic)

This project implements an **Adaptive Hybrid Recipe Data Pipeline** designed to ingest, clean, normalize, and store recipe data into a **PostgreSQL database**. 

### 🎯 Executive Summary
Traditional data pipelines break when source formats shift (Schema Drift) or when linguistic ambiguity occurs. This pipeline solves these challenges using a **Layered Hybrid Architecture**: 
1. **Semantic Intelligence (LLM)** handles the "Entropy" (unknown schemas, generic ingredient names, and web noise).
2. **Deterministic Logic (Regex/Python)** handles the "Truth" (quantities, units, and structural cleaning) to ensure 0% hallucination in numeric data.

## 🚀 Key Features
- **Adaptive Mapping (Layer 0)**: Uses LLMs as a "Universal Adapter" to automatically identify ingredients and instructions in unknown data structures. Agnostic to input source keys.
- **Pure Regex extraction**: 100% deterministic parsing of quantities, units, and punctuation. Guaranteed numeric integrity.
- **Semantic Disambiguation**: Contextual resolution of generic terms (e.g., resolving "masala" to "Garam Masala" based on recipe title).
- **Intelligent Step Categorization**: Distinguishes cooking instructions from web metadata and ads semantically.
- **PostgreSQL Relational Storage**: Full ETL flow into a structured relational schema.

---

## 🏗️ Project Structure

```text
recipe_pipeline/
├── data/
│   └── recipes.json          # Target dataset
├── src/
│   ├── main.py               # Orchestrator (Multi-Layer Flow)
│   ├── ai_processor.py       # Layer 2: LLM Assistance (Disambiguation & Classification)
│   ├── normalizers.py        # Layer 1: Deterministic extractors (Time, Servings)
│   ├── ingredient_parser.py  # Layer 1: Deterministic Qty/Unit extraction
│   ├── unit_normalizer.py    # Layer 1: Metric normalization (g, ml)
│   ├── instruction_cleaner.py# NLP/Regex cleaning for steps
│   ├── db.py                 # PostgreSQL connection setup
│   ├── db_insert.py          # Relational insertion logic
│   └── test_adaptive_pipeline.py # Final verification suite
├── sql/
│   └── schema.sql            # Database schema (DDL)
└── documentation/            # Detailed compliance and workflow docs
```

---

## ⚖️ AI vs. Deterministic Boundaries (Assessment Compliance)

To meet strict technical constraints, we maintain a hard boundary between LLM and Regex:

| Task | Mechanism | Role |
| :--- | :--- | :--- |
| **Quantity Extraction** | **Pure Regex** | Extracts floats, fractions, and integers with 0% error. |
| **Unit Normalization** | **Pure Regex** | Maps symbols (tsp, kg) to standard metrics. |
| **Punctuation Cleaning** | **Pure Regex** | Strips noise and artifacts using pattern matching. |
| **Schema Mapping** | **Targeted LLM** | Identifies semantic keys in unknown source data. |
| **Entity Disambiguation**| **Targeted LLM** | Resolves "masala" -> "Garam Masala" based on context. |
| **Step Classification** | **Targeted LLM** | Separates cooking steps from web advertisements. |

---

## 🤖 How AI Assists the Pipeline

The AI in this project acts as a **Semantic Layer** that handles high-entropy (unpredictable) data, while the Python engine handles the **Structural Layer**.

1.  **Semantic sensing**: Instead of hardcoding keys for 100+ websites, the AI identifies which raw fields represent ingredients or instructions based on their meaning.
2.  **Collaborative Error Correction**: If the deterministic parser (Layer 1) fails to extract a name cleanly, the AI (Layer 2) is used as a fallback to resolve the ambiguity using recipe context (e.g., Title and other ingredients).
3.  **Intelligent Filtering**: AI distinguishes between a cooking action ("Cut the onion") and marketing noise ("Cut your costs here") which often use the same sentence structures.

**Crucially**, the AI's output is always validated by the deterministic layer before it touches the database, ensuring zero hallucination in quantities and units.

---

## 🛠️ Installation & Usage

### 1. Database Setup
```sql
-- Create the database
CREATE DATABASE recipe_pipeline;

-- Apply the schema
psql -d recipe_pipeline -f sql/schema.sql
```

### 2. Environment Configuration
Set your Google Gemini API Key to enable semantic features:
```bash
export GOOGLE_API_KEY="your_api_key_here"
```
*Note: The pipeline automatically falls back to deterministic-only mode if no API key is provided.*

### 3. Run the Pipeline
```bash
# Process and insert data
python src/main.py

# Run comprehensive verification tests
python src/test_adaptive_pipeline.py
```

---

## 📊 Output Evidence
The pipeline populates the following relational tables:
- **`recipes`**: Metadata, timing, and cleaned instructions.
- **`recipe_ingredients`**: Parsed ingredients with metric-normalized quantities.
- **`meals` & `meal_recipes`**: Automatic categorization into breakfast/lunch/dinner.
- **`meal_ingredients`**: Aggregated shopping lists for entire meals.

---

## ✅ Assessment Coverage Checklist
- [x] **Relational Schema**: Full PostgreSQL implementation with proper foreign keys.
- [x] **Multi-Layer Logic**: Layered architecture (Adaptive -> Deterministic -> Targeted AI).
- [x] **Metric Normalization**: Standardized `g` and `ml` values for all ingredients.
- [x] **Semantic Cleaning**: AI-assisted noise filtering and entity resolution.
- [x] **Robust Integration**: Exception queues and confidence thresholds for AI outputs.
- [x] **Detailed Documentation**: Clear separation of AI vs. Regex logic provided in `assessment_compliance.md`.
