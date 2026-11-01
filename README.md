# Natural Language to MySQL Query Generator (Text-to-SQL)

An academic Natural Language Processing (NLP) capstone project that translates English questions into validated MySQL queries, dynamically inspects relational schemas, executes permitted queries, and explains the SQL logic in plain English.

---

## 🌟 Key Features

1. **Automatic Schema Discovery**: Introspects connected MySQL or SQLite databases via SQLAlchemy metadata without hardcoded tables or columns.
2. **Dual-Approach SQL Generation**:
   - **Approach 1 (Baseline)**: Lightweight rule-based slot-filling with TF-IDF intent classification and BFS multi-table JOIN path discovery.
   - **Approach 2 (Advanced)**: Schema-aware LLM generation with few-shot prompting and structured JSON output (supporting Google Gemini and OpenAI).
   - **Zero-Crash Offline Fallback**: Automatically cascades to the baseline if external APIs are unavailable.
3. **AST Safety & Validation Guard**: Uses SQLGlot to strictly enforce read-only `SELECT` queries, blocking any destructive mutations (`INSERT`, `UPDATE`, `DELETE`, `DROP`, `ALTER`, `TRUNCATE`) and SQL injections.
4. **Schema Whitelisting**: Intercepts and rejects queries referencing hallucinated tables or columns before reaching the database.
5. **Interactive Streamlit Web Dashboard**: Includes Database Explorer, live Query Generator with execution preview, Performance Benchmarking, and Query History.

---

## 🏗️ System Architecture

```
[ User English Question ]
           │
           ▼
[ 1. NLP Preprocessing ]
├── Text Normalization & Contraction Expansion
├── Relational Keyword Preservation (more than, top, avg, each)
└── WordNet Lemmatization & Tokenization
           │
           ▼
[ 2. Schema Linking & Relationship Graph ]
├── Dynamic Table & Column Introspection
└── BFS Shortest-Path Multi-Table JOIN Discovery
           │
           ├───► [ Approach 1: Traditional NLP Baseline ]
           │     ├── TF-IDF Intent Classifier
           │     └── Slot-Filling Relational Templates
           │
           └───► [ Approach 2: Schema-Aware LLM ]
                 ├── Dynamic Schema In-Context Prompting
                 └── Structured JSON Parser & Explainer
           │
           ▼
[ 3. SQLGlot AST Safety & Validation Gate ]
├── Restrict to SELECT / UNION Only
├── Reject Mutating Operations & Multi-Statement Queries
└── Schema Whitelist Verification (Tables & Columns)
           │
           ▼
[ 4. Safe Query Execution Engine ]
├── Automatic Row Capping (LIMIT 100)
└── Latency Measurement (Gen vs Exec Time)
           │
           ▼
[ 5. Results & Interactive Presentation ]
```

---

## 📂 Project Structure

```text
├── app.py                     # Streamlit multi-page web application
├── requirements.txt           # Pinned project dependencies
├── .env.example               # Environment configuration template
├── .gitignore                 # Protects virtual environments and credentials
│
├── config/
│   └── settings.py            # Strongly-typed configuration dataclasses
│
├── database/
│   ├── connection.py          # SQLAlchemy connection & health checks
│   ├── schema_detector.py     # Dynamic introspection & BFS JOIN path finder
│   ├── schema_formatter.py    # DDL prompt formatter & Markdown serializer
│   └── query_executor.py      # Safe execution wrapper with row capping
│
├── nlp/
│   ├── preprocessing.py       # Normalization, tokenization & lemmatization
│   ├── keyword_extraction.py  # Numeric conditions, operators & aggregates
│   ├── intent_classifier.py   # TF-IDF + Logistic Regression classifier
│   └── entity_extractor.py    # Lexical and synonym-based schema linker
│
├── generation/
│   ├── baseline_generator.py  # Traditional slot-filling baseline
│   ├── llm_generator.py       # Configurable LLM client (Gemini / OpenAI / Offline)
│   ├── prompt_builder.py      # In-context few-shot prompt assembler
│   └── response_parser.py     # Markdown sanitizer & JSON output parser
│
├── validation/
│   ├── sql_validator.py       # SQLGlot AST parser & mutation blocker
│   └── schema_validator.py    # Schema table and column reference whitelister
│
├── evaluation/
│   ├── dataset_loader.py      # Benchmark dataset manager
│   ├── exact_match.py         # AST-normalized SQL Exact Match (EM)
│   ├── execution_accuracy.py  # Result set Execution Accuracy (EX)
│   └── evaluate.py            # Comparative evaluation harness
│
├── datasets/
│   └── custom_questions.json  # 5-tier evaluation dataset
│
├── sample_database/
│   ├── schema.sql             # 7-table College Management relational DDL
│   ├── sample_data.sql        # Realistic sample seed records
│   └── setup_db.py            # MySQL & SQLite dual-mode database initializer
│
├── frontend/
│   ├── components.py          # Reusable UI widgets
│   └── styles.py              # Custom CSS styling
│
└── tests/                     # Automated pytest test suites
```

---

## 🚀 Installation & Quick Start

### 1. Clone & Setup Virtual Environment
```powershell
git clone <your-repo-url>
cd <repo-folder>
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### 2. Environment Configuration
Copy `.env.example` to `.env`:
```powershell
cp .env.example .env
```
*(Optional)* Add your MySQL password or Google Gemini API key if testing with live services.

### 3. Initialize Sample Database
```powershell
# Option A: Initialize local SQLite database (Zero-configuration mode)
.\.venv\Scripts\python.exe sample_database/setup_db.py --sqlite

# Option B: Initialize live MySQL database
.\.venv\Scripts\python.exe sample_database/setup_db.py
```

### 4. Run the Streamlit Application
```powershell
.\.venv\Scripts\streamlit run app.py
```

### 5. Run Automated Tests
```powershell
.\.venv\Scripts\pytest -v
```

---

## 📊 Completed Implementation Phases

- **Phase 1: Project Setup & Core Configuration** (Directory layout, dependencies, `.env`, test harness)
- **Phase 2: Sample Database** (7 normalized tables, realistic seed records, dual-engine loader)
- **Phase 3: Automatic Schema Detection** (Metadata reflection, BFS shortest-path JOIN discovery)
- **Phase 4: NLP Preprocessing & Baseline** (Tokenization, keyword extraction, intent classifier, template baseline)
- **Phase 5: Schema-Aware LLM Generation** (In-context prompt builder, Gemini/OpenAI integration, offline fallback)
- **Phase 6: SQL Validation & Safe Execution** (SQLGlot AST parser, mutation interceptor, schema whitelisting, row capping)
- **Phase 7: Streamlit Web Interface** (5-tab dashboard: Query Generator, Schema Explorer, Connection Manager, Benchmark, History)
- **Phase 8: Evaluation & Comparative Study** (Benchmark dataset, Exact Match & Execution Accuracy harnesses)
- **Phase 9: Documentation & Academic Review** (Architecture docs, literature survey, methodology)
