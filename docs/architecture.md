# System Architecture

## Overview
The **Natural Language to MySQL Query Generator** is designed with a decoupled, modular architecture adhering to separation-of-concerns principles. The system consists of five core tiers:

```
+-----------------------------------------------------------+
|                    Presentation Tier                      |
|                  Streamlit Web Dashboard                  |
+-----------------------------------------------------------+
                              │
                              ▼
+-----------------------------------------------------------+
|                   NLP & Schema Linking                    |
|   Tokenization • Entity Grounding • Intent Classification |
+-----------------------------------------------------------+
                              │
                              ▼
+-----------------------------------------------------------+
|                   SQL Generation Tier                     |
|    Approach 1: Baseline ML   │   Approach 2: Schema LLM   |
+-----------------------------------------------------------+
                              │
                              ▼
+-----------------------------------------------------------+
|                AST Validation & Security Gate             |
|    SQLGlot MySQL Dialect Check • Schema Whitelisting      |
+-----------------------------------------------------------+
                              │
                              ▼
+-----------------------------------------------------------+
|                    Execution Engine                       |
|         SQLAlchemy • PyMySQL • Row Limit Guard            |
+-----------------------------------------------------------+
```

## Key Modules
1. **Dynamic Schema Detection (`database/schema_detector.py`)**:
   - Queries database metadata without hardcoded assumptions.
   - Models foreign keys as an undirected graph and computes shortest paths via Breadth-First Search (BFS) to discover multi-table JOIN routes automatically.
2. **Traditional NLP / ML Baseline (`generation/baseline_generator.py`)**:
   - Uses TF-IDF and Logistic Regression for intent identification.
   - Extracts numeric and string comparison slots.
   - Assembles valid SQL without depending on external generative models.
3. **Schema-Aware LLM (`generation/llm_generator.py`)**:
   - Dynamically crafts few-shot in-context prompts containing detected DDL and relationships.
   - Enforces structured JSON output.
   - Provides graceful fallback to the baseline if external APIs are unreachable.
4. **AST Security Gate (`validation/sql_validator.py` & `validation/schema_validator.py`)**:
   - Parses AST via SQLGlot.
   - Enforces read-only `SELECT` and `UNION` operations.
   - Intercepts all mutating operations (`INSERT`, `UPDATE`, `DELETE`, `DROP`, `ALTER`, `TRUNCATE`) and multi-statement queries.
   - Verifies referenced tables and columns against the active schema whitelist.
5. **Execution & Limits (`database/query_executor.py`)**:
   - Caps returned records to `max_rows` (default 100).
   - Measures generation and execution latencies independently.
