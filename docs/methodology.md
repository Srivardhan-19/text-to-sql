# Methodology

## 1. Natural Language Preprocessing
- **Text Normalization**: Queries are lowercased and contractions expanded (`won't` ➔ `will not`).
- **Relational Keyword Preservation**: Standard stopword filtering removes linguistic noise while preserving semantic relational operators (`more`, `less`, `than`, `above`, `average`, `count`, `each`, `top`).
- **Lemmatization**: WordNet lemmatizer normalizes plurals (`students` ➔ `student`) and verbs.

## 2. Intent Classification
- A TF-IDF vectorizer extracts unigrams and bigrams from the question.
- A Logistic Regression classifier categorizes intent into canonical SQL structures:
  - `SIMPLE_SELECT`
  - `FILTERED_SELECT`
  - `AGGREGATE`
  - `JOIN_QUERY`
  - `GROUP_BY_AGGREGATE`
  - `ORDERED_SELECT`

## 3. Schema Linking & Entity Grounding
- Matches tokens against introspected database schema tables and columns.
- Uses exact match, singularized normalization, and domain synonyms (`score` ➔ `marks.marks`, `dept` ➔ `departments.dept_name`).
- Automatically resolves primary-to-foreign key JOIN paths between disconnected tables.

## 4. Query Generation Strategies
### Approach 1: Traditional Baseline (Rule & Template Slot-Filling)
- Primary table selection based on highest-frequency entity match.
- Dynamic BFS graph traversal between primary and dependent tables to formulate `JOIN ... ON` clauses.
- Slot filling for numeric filters (`marks > 80`) and categorical string comparisons.

### Approach 2: Schema-Aware LLM Generation
- Injects detected schema DDL, foreign key relationships, and few-shot pairs.
- Forces structured JSON schema response with clause-by-clause natural language explanation.

## 5. Security & Safety Verification
- Parses generated queries into a concrete syntax tree (CST) using `sqlglot`.
- Walks AST nodes to verify that no node inherits from forbidden mutating expressions (`exp.Insert`, `exp.Update`, `exp.Delete`, `exp.Drop`, `exp.Alter`, `exp.TruncateTable`).
- Rejects any query containing multiple semicolons or statement chains.
