"""
Streamlit Web Application: Natural Language to MySQL Query Generator.
Main user interface orchestrating schema detection, NLP preprocessing, generation, validation, and execution.
"""
from __future__ import annotations

import sys
import time
from pathlib import Path
from datetime import datetime
import streamlit as st
import pandas as pd
from sqlalchemy import create_engine, text

# Add workspace root to sys.path
BASE_DIR = Path(__file__).resolve().parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from config.settings import get_settings
from database.connection import ConnectionManager
from database.schema_detector import SchemaDetector
from database.schema_formatter import SchemaFormatter
from database.query_executor import QueryExecutor
from generation.baseline_generator import BaselineSQLGenerator
from generation.llm_generator import LLMGenerator
from validation.sql_validator import SQLValidator
from validation.schema_validator import SchemaValidator
from frontend.styles import CUSTOM_CSS
from frontend.components import render_header, render_explanation, render_results_table

# Configure Streamlit page
st.set_page_config(
    page_title="Text-to-SQL Generator (MySQL)",
    page_icon="🗄️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Apply CSS styling
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

# Initialize Session State
if "engine" not in st.session_state:
    st.session_state.engine = None
if "schema" not in st.session_state:
    st.session_state.schema = None
if "db_name" not in st.session_state:
    st.session_state.db_name = None
if "query_history" not in st.session_state:
    st.session_state.query_history = []
if "last_query_result" not in st.session_state:
    st.session_state.last_query_result = None

# Auto-connect to local database if not connected
if st.session_state.engine is None:
    settings = get_settings()
    # Try MySQL first if credentials exist
    try:
        mysql_url = settings.db.get_connection_url()
        mgr = ConnectionManager(settings.db)
        success, _ = mgr.test_connection(mysql_url)
        if success:
            eng = mgr.get_engine(mysql_url)
            st.session_state.engine = eng
            st.session_state.schema = SchemaDetector(eng).detect()
            st.session_state.db_name = f"MySQL: {settings.db.database}"
    except Exception:
        pass

    # Fallback to local SQLite sample database
    if st.session_state.engine is None:
        sqlite_file = BASE_DIR / "college_db.sqlite"
        if not sqlite_file.exists():
            from sample_database.setup_db import init_database
            init_database(create_engine(f"sqlite:///{sqlite_file}"), is_sqlite=True)
        eng = create_engine(f"sqlite:///{sqlite_file}")
        st.session_state.engine = eng
        st.session_state.schema = SchemaDetector(eng).detect()
        st.session_state.db_name = "SQLite: college_db.sqlite (Self-Contained Mode)"

# -------------------------------------------------------------
# Sidebar Navigation
# -------------------------------------------------------------
with st.sidebar:
    st.title("🗄️ Text-to-SQL System")
    st.caption("Academic NLP Capstone Project")
    st.markdown("---")

    page = st.radio(
        "Navigation",
        [
            "💬 Natural Language Query",
            "🔍 Database Schema Explorer",
            "🔌 Database Connection",
            "📊 Evaluation & Comparison",
            "📜 Query History"
        ],
        index=0
    )

    st.markdown("---")
    st.markdown("### Active Connection")
    if st.session_state.engine and st.session_state.schema:
        st.success(f"Connected: **{st.session_state.db_name}**")
        st.caption(f"Tables Detected: **{len(st.session_state.schema.tables)}**")
        st.caption(f"FK Relationships: **{len(st.session_state.schema.relationships)}**")
    else:
        st.error("Not Connected")

# -------------------------------------------------------------
# PAGE 1: Natural Language Query (Primary Page)
# -------------------------------------------------------------
if page == "💬 Natural Language Query":
    render_header(
        "Natural Language to MySQL Query Generator",
        "Ask questions in plain English to automatically generate, validate, and execute safe MySQL queries."
    )

    if not st.session_state.engine or not st.session_state.schema:
        st.error("Please connect to a database in the 'Database Connection' tab first.")
        st.stop()

    schema = st.session_state.schema
    engine = st.session_state.engine

    # Quick example questions
    st.markdown("##### Quick-Fill Academic Example Questions:")
    sample_queries = [
        "Show the names of students who scored more than 80 marks in DBMS.",
        "Find the average marks in DBMS.",
        "Show all students.",
        "Display the top 5 students based on cgpa.",
        "Count the number of students in each department.",
        "What is the average salary of instructors in each department?"
    ]

    selected_sample = st.selectbox("Choose a pre-built example or type your own question below:", ["-- Custom Question --"] + sample_queries)
    default_text = "" if selected_sample == "-- Custom Question --" else selected_sample

    user_question = st.text_input("Enter your natural language question:", value=default_text, placeholder="e.g. Show students who scored more than 80 marks in DBMS")

    col_approach, col_provider, col_btn = st.columns([2, 1.5, 1])
    with col_approach:
        approach = st.selectbox(
            "Generation Approach:",
            ["Approach 2: Schema-Aware LLM", "Approach 1: Traditional NLP/ML Baseline"]
        )
    with col_provider:
        provider_choice = st.selectbox(
            "LLM Provider:",
            ["gemini", "openai", "offline (forced baseline)"],
            disabled=("Baseline" in approach)
        )
    with col_btn:
        st.write("")  # spacing
        st.write("")
        generate_clicked = st.button("Generate & Run SQL", type="primary", use_container_width=True)

    if generate_clicked and user_question.strip():
        with st.spinner("Processing NLP query and synthesizing SQL..."):
            gen_start = time.perf_counter()

            # 1. SQL Generation
            if "Baseline" in approach:
                generator = BaselineSQLGenerator(schema)
                gen_result = generator.generate(user_question)
                sql_candidate = gen_result.sql
                explanation = gen_result.explanation
                tables_used = gen_result.linked_tables
                columns_used = gen_result.linked_columns
                assumptions = []
                gen_time_ms = (time.perf_counter() - gen_start) * 1000
                provider_used = "Baseline Rule/Slot Engine"
            else:
                prov = provider_choice.split()[0]
                generator = LLMGenerator(schema)
                llm_res = generator.generate(user_question, force_provider=prov)
                sql_candidate = llm_res.sql
                explanation = llm_res.explanation
                tables_used = llm_res.tables_used
                columns_used = llm_res.columns_used
                assumptions = llm_res.assumptions
                gen_time_ms = llm_res.generation_time_ms
                provider_used = llm_res.provider

        # 2. SQL Validation
        st.markdown("---")
        st.markdown("### Generated SQL Query")
        st.code(sql_candidate, language="sql")

        val_col1, val_col2, val_col3 = st.columns(3)
        sql_val = SQLValidator()
        sql_res = sql_val.validate(sql_candidate)

        schema_val = SchemaValidator(schema)
        schema_res = schema_val.validate(sql_res)

        with val_col1:
            if sql_res.is_valid:
                st.success("AST Parse & Read-Only Check: **PASSED**")
            else:
                st.error(f"AST Safety Violation: **{sql_res.error_message}**")

        with val_col2:
            if schema_res.is_valid:
                st.success("Schema Whitelist: **PASSED**")
            else:
                st.error(f"Schema Violation: **{schema_res.error_message}**")

        with val_col3:
            st.info(f"Gen Time: **{gen_time_ms:.1f} ms** ({provider_used})")

        # 3. Execution (if valid)
        if sql_res.is_valid and schema_res.is_valid:
            executor = QueryExecutor(engine)
            exec_res = executor.execute(sql_candidate)

            if exec_res.success:
                df = exec_res.to_dataframe()
                render_results_table(df, exec_res.execution_time_ms)
                render_explanation(explanation, assumptions)

                # Record in query history
                st.session_state.query_history.append({
                    "timestamp": datetime.now().strftime("%H:%M:%S"),
                    "question": user_question,
                    "approach": approach,
                    "sql": sql_candidate,
                    "status": "SUCCESS",
                    "rows": exec_res.row_count,
                    "gen_time_ms": f"{gen_time_ms:.1f}",
                    "exec_time_ms": f"{exec_res.execution_time_ms:.1f}"
                })
            else:
                st.error(f"Execution Error: {exec_res.error_message}")
                st.session_state.query_history.append({
                    "timestamp": datetime.now().strftime("%H:%M:%S"),
                    "question": user_question,
                    "approach": approach,
                    "sql": sql_candidate,
                    "status": "EXEC_ERROR",
                    "rows": 0,
                    "gen_time_ms": f"{gen_time_ms:.1f}",
                    "exec_time_ms": f"{exec_res.execution_time_ms:.1f}"
                })
        else:
            st.warning("Query execution was aborted due to safety or schema validation failure.")

# -------------------------------------------------------------
# PAGE 2: Database Schema Explorer
# -------------------------------------------------------------
elif page == "🔍 Database Schema Explorer":
    render_header("Database Schema Explorer", "Inspect detected relational tables, columns, constraints, and relationships.")
    schema = st.session_state.schema

    if not schema:
        st.warning("No database schema loaded.")
        st.stop()

    table_names = schema.get_table_names()
    selected_table = st.selectbox("Select a table to inspect:", table_names)

    if selected_table:
        tbl = schema.tables[selected_table]
        col1, col2 = st.columns([3, 2])

        with col1:
            st.markdown(f"#### Table Schema: `{selected_table}`")
            records = []
            for col in tbl.columns.values():
                records.append({
                    "Column": col.name,
                    "Data Type": col.data_type,
                    "Nullable": col.nullable,
                    "Primary Key": col.is_primary_key,
                    "Foreign Key Target": col.foreign_key_target or "-"
                })
            st.dataframe(pd.DataFrame(records), use_container_width=True)

        with col2:
            st.markdown("#### Sample Records (Top 5)")
            try:
                with st.session_state.engine.connect() as conn:
                    sample_df = pd.read_sql_query(text(f"SELECT * FROM {selected_table} LIMIT 5"), conn)
                st.dataframe(sample_df, use_container_width=True)
            except Exception as e:
                st.error(f"Could not load preview: {e}")

    st.markdown("---")
    st.markdown("#### Foreign Key Relationships Graph")
    if schema.relationships:
        rel_records = [
            {"Source": f"{r.source_table}.{r.source_column}", "Target": f"{r.target_table}.{r.target_column}"}
            for r in schema.relationships
        ]
        st.dataframe(pd.DataFrame(rel_records), use_container_width=True)
    else:
        st.info("No foreign keys detected in the active database.")

# -------------------------------------------------------------
# PAGE 3: Database Connection
# -------------------------------------------------------------
elif page == "🔌 Database Connection":
    render_header("Database Connection Manager", "Connect to a live MySQL server or toggle to the self-contained SQLite mode.")
    settings = get_settings()

    tab_mysql, tab_sqlite = st.tabs(["MySQL Server Connection", "Local SQLite Sample Database"])

    with tab_mysql:
        with st.form("mysql_conn_form"):
            c_host = st.text_input("Host", value=settings.db.host)
            c_port = st.number_input("Port", value=settings.db.port, step=1)
            c_user = st.text_input("Username", value=settings.db.user)
            c_pwd = st.text_input("Password", type="password", value=settings.db.password)
            c_db = st.text_input("Database Name", value=settings.db.database)
            btn_connect_mysql = st.form_submit_button("Test & Connect to MySQL", type="primary")

        if btn_connect_mysql:
            from config.settings import DatabaseSettings
            custom_db = DatabaseSettings(host=c_host, port=int(c_port), user=c_user, password=c_pwd, database=c_db)
            mgr = ConnectionManager(custom_db)
            success, msg = mgr.test_connection()
            if success:
                st.success("MySQL Connection Successful!")
                eng = mgr.get_engine()
                st.session_state.engine = eng
                st.session_state.schema = SchemaDetector(eng).detect()
                st.session_state.db_name = f"MySQL: {c_db}"
                st.rerun()
            else:
                st.error(f"Connection Failed: {msg}")

    with tab_sqlite:
        st.markdown("Use the bundled College Management SQLite database for instant zero-config testing without a MySQL daemon.")
        if st.button("Connect to College SQLite Database", type="secondary"):
            sqlite_file = BASE_DIR / "college_db.sqlite"
            eng = create_engine(f"sqlite:///{sqlite_file}")
            st.session_state.engine = eng
            st.session_state.schema = SchemaDetector(eng).detect()
            st.session_state.db_name = "SQLite: college_db.sqlite"
            st.success("Connected to College SQLite database!")
            st.rerun()

# -------------------------------------------------------------
# PAGE 4: Evaluation & Comparison
# -------------------------------------------------------------
elif page == "📊 Evaluation & Comparison":
    render_header("Evaluation & Comparative Analysis", "Benchmark Traditional NLP Baseline against Schema-Aware LLM generation.")

    st.markdown("""
    This section evaluates both approaches on canonical query archetypes across:
    - **Exact Match (EM)**
    - **Execution Accuracy (EX)**
    - **SQL Validity Rate**
    - **Generation Latency**
    """)

    if st.button("Run Live Benchmark Comparison", type="primary"):
        from evaluation.evaluate import run_benchmark_suite
        with st.spinner("Running benchmark suite across difficulty levels..."):
            summary_df, detailed_df = run_benchmark_suite(st.session_state.schema, st.session_state.engine)
            st.markdown("### Benchmark Summary")
            st.dataframe(summary_df, use_container_width=True)

            st.markdown("### Detailed Query Evaluation Breakdown")
            st.dataframe(detailed_df, use_container_width=True)

# -------------------------------------------------------------
# PAGE 5: Query History
# -------------------------------------------------------------
elif page == "📜 Query History":
    render_header("Session Query History", "Inspect questions asked, generated queries, and execution statuses during this session.")
    if st.session_state.query_history:
        history_df = pd.DataFrame(st.session_state.query_history)
        st.dataframe(history_df, use_container_width=True)
        if st.button("Clear Session History"):
            st.session_state.query_history = []
            st.rerun()
    else:
        st.info("No queries have been executed yet in this session.")

