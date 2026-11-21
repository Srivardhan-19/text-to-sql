# Natural Language to MySQL Query Generator (Traditional NLP)

An academic Natural Language Processing (NLP) capstone project that translates English questions into validated MySQL queries using **traditional NLP, conventional machine learning, and rule-based query construction exclusively**—without any Large Language Models (LLMs).
---

## 🌟 Key Features

1. **Strictly Traditional NLP Pipeline**:
   - Tokenization, text normalization, and contraction expansion (`NLTK`).
   - Relational keyword preservation (retaining operators, aggregates, and topological markers).
   - WordNet lemmatization and stop-word filtering.
   - TF-IDF n-gram vectorization + Logistic Regression intent classifier (`scikit-learn`).
   - Regex-based operator, aggregate (`AVG`, `COUNT`, `SUM`, `MIN`, `MAX`), limit, and condition extraction.
   - Dynamic schema linking with string similarity (`difflib.SequenceMatcher`) across arbitrary databases.
2. **Dynamic Database Schema Discovery**:
   - Automatically inspects tables, columns, primary keys, and foreign keys via SQLAlchemy / MySQL `INFORMATION_SCHEMA`.
   - Discovers multi-table relationships and computes shortest-path JOINs using Breadth-First Search (BFS) graph traversal.
3. **Mandatory 2-Step User-Controlled Execution Workflow**:
   - **Step 1 (Generate & Preview)**: The natural language question is processed and converted into MySQL syntax. **The query is never executed automatically.**
   - **Step 2 (Preview & Edit)**: The user inspects the generated SQL in an editable code area, reviews the AST safety and schema whitelisting validation status, and can modify the SQL.
   - **Step 3 (Explicit Run)**: The user explicitly clicks **"Run Query"**. The displayed query is re-validated through SQLGlot AST checks before execution.
4. **AST Safety & Mutation Blocker**:
   - Uses SQLGlot to restrict execution strictly to read-only `SELECT` statements.
   - Blocks mutating operations (`INSERT`, `UPDATE`, `DELETE`, `DROP`, `ALTER`, `TRUNCATE`) and multi-statement queries.
5. **Zero-Configuration Demo Database**:
   - If the user does not have or connect a local MySQL server, the application automatically loads a pre-seeded, self-contained 7-table College Management demo database (`college_db.sqlite`) and prompts the user with questions tailored to it.
6. **Multi-Tab Streamlit Dashboard**:
   - Natural Language Query generator with editable SQL preview and explicit run trigger.
   - Database Schema Explorer.
   - MySQL Connection Manager.
   - Benchmark Evaluation Suite.
   - Session Query History.

---

## 🏗️ System Architecture

```text
[ User Natural Language Question ]
               │
               ▼
   [ 1. NLP Preprocessing ]
   ├── Lowercase Normalization & Contraction Expansion
   ├── Relational Keyword Preservation (more, less, top, each, avg)
   └── WordNet Lemmatization & Tokenization
               │
               ▼
   [ 2. Intent & Keyword Extraction ]
   ├── TF-IDF + Logistic Regression Intent Classifier
   └── Regex Condition, Operator, Aggregate & Limit Extractor
               │
               ▼
   [ 3. Dynamic Schema Linking & BFS JOINs ]
   ├── Lexical & Fuzzy Similarity Schema Matching
   └── Shortest-Path BFS Foreign-Key Graph Traversal
               │
               ▼
   [ 4. Rule-Based SQL Construction ]
   └── Deterministic Slot-Filling Query Assembler
               │
               ▼
   [ 5. SQLGlot AST Safety & Validation Gate ]
   ├── Restrict to SELECT Only
   └── Reject Mutations & Multiple Statements
               │
               ▼
     [ 6. SQL Preview Section ]  ◄─── (User can review, copy, and edit SQL)
               │
       [ User Clicks 'Run Query' ]
               │
               ▼
   [ 7. Safe Execution Engine & Results Display ]
   ├── Enforce Row Ceiling (LIMIT 100)
   ├── Measure Generation & Execution Latencies
   └── Render Interactive Results Table & CSV Export
```

---

## 🚀 Installation & Quick Start

### 1. Clone the Repository & Setup Virtual Environment
```powershell
git clone https://github.com/Srivardhan-19/text-to-sql.git
cd text-to-sql
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### 2. Configure Environment (Optional)
```powershell
Copy-Item .env.example .env
```
*Note: No API keys are needed! The system runs 100% locally on CPU without external AI services.*

### 3. Run the Streamlit Web Application
```powershell
streamlit run app.py
```

- If you have a local MySQL server running, configure credentials in `.env` or in the **Database Connection** tab.
- If you **do not** have MySQL running, the application will automatically initialize and load the **College Management demo database**, allowing you to ask queries immediately without any configuration.

### 4. Run Automated Tests
```powershell
pytest -v
```

---

## 📊 Benchmark Evaluation

The project includes an automated evaluation harness testing:
- **Exact Match (EM)**: AST-normalized SQL equivalence.
- **Execution Accuracy (EX)**: Result set correctness against ground-truth database records.
- **SQL Validity**: Structural and syntactical correctness via SQLGlot.
- **Latency**: Sub-50ms deterministic CPU query generation.

---

## 📚 Academic & Technical References

- **Spider Dataset & Baselines**: Tao Yu et al., *Spider: A Large-Scale Human-Labeled Dataset for Complex and Cross-Domain Semantic Parsing and Text-to-SQL Task* (EMNLP 2018).
- **RAT-SQL**: Peter Shaw et al., *Relation-Aware Schema Encoding and Linking for Text-to-SQL Parsers* (ACL 2020).
- **SQLGlot**: Toby Mao, SQL Parser, Transpiler, Optimizer, and Engine.
- **NLTK & scikit-learn**: Traditional tokenization, lemmatization, and TF-IDF linear classification.

---

## 📜 License
MIT License.
