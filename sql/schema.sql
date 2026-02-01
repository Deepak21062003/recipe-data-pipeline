-- =========================
-- RECIPES TABLE
-- =========================
CREATE TABLE recipes (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT,
    instructions JSONB NOT NULL,
    prep_time_minutes INTEGER,
    cook_time_minutes INTEGER,
    total_time_minutes INTEGER,
    servings INTEGER,
    difficulty_level TEXT,
    tags JSONB,
    metadata JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- =========================
-- RECIPE INGREDIENTS TABLE
-- =========================
CREATE TABLE recipe_ingredients (
    id SERIAL PRIMARY KEY,
    recipe_id INTEGER NOT NULL REFERENCES recipes(id) ON DELETE CASCADE,
    ingredient_name TEXT NOT NULL,
    ingredient_info JSONB,
    grocery_mapping JSONB,
    is_optional BOOLEAN DEFAULT FALSE,
    order_index INTEGER
);

-- =========================
-- MEALS TABLE
-- =========================
CREATE TABLE meals (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    meal_type TEXT,
    total_time_minutes INTEGER,
    estimated_cost NUMERIC
);

-- =========================
-- MEAL RECIPES TABLE
-- =========================
CREATE TABLE meal_recipes (
    id SERIAL PRIMARY KEY,
    meal_id INTEGER NOT NULL REFERENCES meals(id) ON DELETE CASCADE,
    recipe_id INTEGER NOT NULL REFERENCES recipes(id) ON DELETE CASCADE,
    recipe_name TEXT,
    order_index INTEGER,
    is_main_dish BOOLEAN DEFAULT TRUE,
    is_optional BOOLEAN DEFAULT FALSE
);

-- =========================
-- MEAL INGREDIENTS TABLE
-- =========================
CREATE TABLE meal_ingredients (
    id SERIAL PRIMARY KEY,
    meal_id INTEGER NOT NULL REFERENCES meals(id) ON DELETE CASCADE,
    ingredient_name TEXT NOT NULL,
    quantity NUMERIC,
    unit TEXT,
    is_optional BOOLEAN DEFAULT FALSE,
    order_index INTEGER
);
