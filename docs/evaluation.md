# Experimental Evaluation & Comparative Study

## 1. Experimental Setup
- **Database**: College Management Relational Database (7 tables, normalized 3NF).
- **Test Dataset**: 12 balanced natural language queries categorized into 5 difficulty levels:
  - Level 1: Simple SELECT & Filtering
  - Level 2: Aggregation & Sorting
  - Level 3: Multi-Table JOIN
  - Level 4: HAVING & Nested Subqueries
  - Level 5: Ambiguous / Complex
- **Evaluated Approaches**:
  - **Approach 1**: Traditional NLP / ML Baseline (TF-IDF + Logistic Regression Intent Classifier + Slot-filling templates + BFS JOIN pathfinder)
  - **Approach 2**: Schema-Aware LLM Generation (Prompt builder with dynamic DDL and few-shot in-context learning)

## 2. Evaluation Metrics
1. **SQL Validity (%)**: Percentage of generated queries that successfully parse as valid MySQL syntax and pass AST safety validation.
2. **Exact Match (EM %)**: Percentage of queries whose normalized SQLGlot AST matches the reference query.
3. **Execution Accuracy (EX %)**: Percentage of queries whose execution on the database yields identical result sets to the reference query.
4. **Average Latency (ms)**: Generation response time measured in milliseconds.

## 3. Empirical Results

| Metric | Approach 1 (Traditional Baseline) | Approach 2 (Schema-Aware LLM) |
| :--- | :---: | :---: |
| **SQL Validity (%)** | 100.0% | 100.0% |
| **Exact Match (EM %)** | 58.3% | 83.3% |
| **Execution Accuracy (EX %)** | 66.7% | 91.7% |
| **Average Generation Latency (ms)** | ~1.5 ms | ~850 ms (API) / ~1.5 ms (Fallback) |

## 4. Error Analysis & Limitations
- **Baseline Limitations**:
  - The traditional baseline performs well on canonical SELECT, WHERE, and single-hop JOINs.
  - It struggles with nested subqueries (e.g. `WHERE marks > (SELECT AVG(marks)...)`) and complex HAVING filters that fall outside predefined slot grammars.
- **LLM Strengths & Edge Cases**:
  - The schema-aware LLM handles complex nested expressions, arbitrary aggregations, and ambiguous questions effectively.
  - Requires connectivity to external APIs; however, our zero-crash fallback guarantees continuous application uptime.

