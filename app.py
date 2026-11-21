"""
Streamlit Web Application: Natural Language to MySQL Query Generator.
Strict Traditional NLP Architecture (No LLMs / Generative AI).
Enforces mandatory 2-step workflow: Generate & Preview SQL -> Review / Edit -> User Explicitly Runs Query.
Includes zero-config fallback to self-contained demo database.
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
from validation.sql_validator import SQLValidator
from validation.schema_validator import SchemaValidator
from frontend.styles import CUSTOM_CSS
from frontend.components import render_header, render_explanation, render_results_table

# Configure Streamlit page
st.set_page_config(
    page_title="Text-to-SQL Generator (Traditional NLP)",
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
if "is_demo_db" not in st.session_state:
    st.session_state.is_demo_db = False
if "query_history" not in st.session_state:
    st.session_state.query_history = []
if "generated_sql" not in st.session_state:
    st.session_state.generated_sql = ""
if "sql_explanation" not in st.session_state:
    st.session_state.sql_explanation = ""
if "gen_time_ms" not in st.session_state:
    st.session_state.gen_time_ms = 0.0
if "last_question" not in st.session_state:
    st.session_state.last_question = ""
if "last_exec_res" not in st.session_state:
    st.session_state.last_exec_res = None

# Auto-connect: Try MySQL first; fallback to local demo SQLite database
if st.session_state.engine is None:
    settings = get_settings()
    # Try MySQL if credentials are set
    try:
        mysql_url = settings.db.get_connection_url()
        mgr = ConnectionManager(settings.db)
        success, _ = mgr.test_connection(mysql_url)
        if success:
            eng = mgr.get_engine(mysql_url)
            st.session_state.engine = eng
            st.session_state.schema = SchemaDetector(eng).detect()
            st.session_state.db_name = f"MySQL: {settings.db.database}"
            st.session_state.is_demo_db = False
    except Exception:
        pass

    # Fallback to local demo SQLite database
    if st.session_state.engine is None:
        sqlite_file = BASE_DIR / "college_db.sqlite"
        if not sqlite_file.exists():
            from sample_database.setup_db import init_database
            init_database(create_engine(f"sqlite:///{sqlite_file}"), is_sqlite=True)
        eng = create_engine(f"sqlite:///{sqlite_file}")
        st.session_state.engine = eng
        st.session_state.schema = SchemaDetector(eng).detect()
        st.session_state.db_name = "College Management DB (Demo Mode)"
        st.session_state.is_demo_db = True

# -------------------------------------------------------------
# Sidebar Navigation & Connection Status
# -------------------------------------------------------------
with st.sidebar:
    st.title("🗄️ Text-to-SQL System")
    st.caption("Traditional NLP & Rule-Based Semantic Parsing")
    st.markdown("---")

    page = st.radio(
        "Navigation",
        [
            "💬 Natural Language Query",
            "🔍 Database Schema Explorer",
            "🔌 Database Connection",
            "📊 Benchmark Evaluation",
            "📜 Query History"
        ],
        index=0
    )

    st.markdown("---")
    st.markdown("### Active Database")
    if st.session_state.engine and st.session_state.schema:
        if st.session_state.is_demo_db:
            st.info(f"Database: **{st.session_state.db_name}**")
            st.caption("ℹ️ Local demo mode active. You can connect your live MySQL server in the Database Connection tab.")
        else:
            st.success(f"Connected: **{st.session_state.db_name}**")
        st.caption(f"Tables Detected: **{len(st.session_state.schema.tables)}**")
        st.caption(f"FK Relationships: **{len(st.session_state.schema.relationships)}**")
    else:
        st.error("Not Connected")

# -------------------------------------------------------------
# PAGE 1: Natural Language Query (Mandatory 2-Step Workflow)
# -------------------------------------------------------------
if page == "💬 Natural Language Query":
    render_header(
        "Natural Language to MySQL Query Generator",
        "Translate English questions into safe, validated MySQL queries using traditional NLP & rule-based synthesis."
    )

    if not st.session_state.engine or not st.session_state.schema:
        st.error("Please connect to a database in the 'Database Connection' tab first.")
        st.stop()

    schema = st.session_state.schema
    engine = st.session_state.engine

    # Notice banner if demo database is active
    if st.session_state.is_demo_db:
        st.info(
            "💡 **Demo Database Active (College Management System)**\n\n"
            "No MySQL server was connected, so the system is running against the pre-loaded 7-table demo database "
            "(`students`, `departments`, `instructors`, `courses`, `enrollments`, `marks`, `classrooms`). "
            "Feel free to ask questions about students, departments, instructor salaries, courses, or marks!"
        )

    # Pre-built academic example questions
    st.markdown("##### Quick-Fill Academic Example Questions:")
    sample_queries = [
        "Show all students.",
        "Show the names of students who scored more than 80 marks in DBMS.",
        "What is the average marks in DBMS?",
        "Display the top 5 students based on cgpa.",
        "Count the number of students in each department.",
        "What is the average salary of instructors in each department?",
        "Find instructors with salary greater than 85000.",
        "Show all courses."
    ]

    selected_sample = st.selectbox(
        "Choose a pre-built example or type your own question below:",
        ["-- Custom Question --"] + sample_queries
    )
    default_text = "" if selected_sample == "-- Custom Question --" else selected_sample

    # Natural Language Input
    user_question = st.text_input(
        "Enter your natural language question:",
        value=default_text,
        placeholder="e.g. Show students who scored more than 80 marks in DBMS"
    )

    # Step 1 Action: Generate SQL Only (Does NOT Execute!)
    col_gen, col_info = st.columns([1.5, 3])
    with col_gen:
        generate_clicked = st.button("Generate SQL", type="primary", use_container_width=True)
    with col_info:
        st.caption("🔒 **Safety Note**: SQL generation and execution are strictly decoupled. Generating SQL will never execute against the database until you review and approve it.")

    if generate_clicked and user_question.strip():
        with st.spinner("Processing question with Traditional NLP pipeline (Tokenization, TF-IDF Intent, Schema Linking)..."):
            t0 = time.perf_counter()
            generator = BaselineSQLGenerator(schema)
            gen_result = generator.generate(user_question)
            gen_time_ms = (time.perf_counter() - t0) * 1000

            st.session_state.generated_sql = gen_result.sql
            st.session_state.sql_explanation = gen_result.explanation
            st.session_state.gen_time_ms = gen_time_ms
            st.session_state.last_question = user_question
            st.session_state.last_exec_res = None  # Clear previous results

    # -------------------------------------------------------------
    # Step 2: SQL Preview & User-Controlled Execution Section
    # -------------------------------------------------------------
    if st.session_state.generated_sql:
        st.markdown("---")
        st.markdown("### 📝 SQL Query Preview (Review & Edit)")
        st.success("✅ **SQL generated successfully.** Review or modify the query below, then click **'Run Query'** to execute it.")

        # Editable code editor for the user
        edited_sql = st.text_area(
            "Generated SQL Query (Editable):",
            value=st.session_state.generated_sql,
            height=130,
            help="You can manually modify the SQL query before executing it."
        )

        # Validation status of currently displayed SQL
        sql_val = SQLValidator()
        sql_res = sql_val.validate(edited_sql)
        schema_val = SchemaValidator(schema)
        schema_res = schema_val.validate(sql_res)

        val_col1, val_col2, val_col3 = st.columns(3)
        with val_col1:
            if sql_res.is_valid:
                st.success("AST Parse & Read-Only Check: **PASSED**")
            else:
                st.error(f"AST Safety: **{sql_res.error_message}**")

        with val_col2:
            if schema_res.is_valid:
                st.success("Schema Whitelist: **PASSED**")
            else:
                st.error(f"Schema Violation: **{schema_res.error_message}**")

        with val_col3:
            st.info(f"NLP Synthesis Time: **{st.session_state.gen_time_ms:.1f} ms**")

        # Step 3: Explicit Execution Trigger
        run_clicked = st.button("🚀 Run Query", type="primary")

        if run_clicked:
            # Re-validate immediately prior to execution
            recheck_sql = sql_val.validate(edited_sql)
            recheck_schema = schema_val.validate(recheck_sql)

            if recheck_sql.is_valid and recheck_schema.is_valid:
                with st.spinner("Executing query against database..."):
                    executor = QueryExecutor(engine)
                    exec_res = executor.execute(edited_sql)
                    st.session_state.last_exec_res = exec_res

                    # Log to history
                    st.session_state.query_history.append({
                        "timestamp": datetime.now().strftime("%H:%M:%S"),
                        "question": st.session_state.last_question or user_question,
                        "sql": edited_sql,
                        "status": "SUCCESS" if exec_res.success else "EXEC_ERROR",
                        "rows": exec_res.row_count,
                        "gen_time_ms": f"{st.session_state.gen_time_ms:.1f}",
                        "exec_time_ms": f"{exec_res.execution_time_ms:.1f}"
                    })
            else:
                err_msg = recheck_sql.error_message or recheck_schema.error_message
                st.error(f"Execution rejected by safety validator: {err_msg}")
                st.session_state.last_exec_res = None

        # Display results if query was executed
        if st.session_state.last_exec_res:
            exec_res = st.session_state.last_exec_res
            if exec_res.success:
                df = exec_res.to_dataframe()
                render_results_table(df, exec_res.execution_time_ms)
                render_explanation(st.session_state.sql_explanation)
            else:
                st.error(f"Execution Error: {exec_res.error_message}")
        elif not run_clicked:
            st.caption("⏸️ Query is waiting for your approval. Click **'Run Query'** above to execute.")

# -------------------------------------------------------------
# PAGE 2: Schema Explorer
# -------------------------------------------------------------
elif page == "🔍 Database Schema Explorer":
    render_header("Database Schema Explorer", "Inspect discovered tables, columns, data types, and primary/foreign keys.")
    if st.session_state.schema:
        schema = st.session_state.schema
        tables = schema.get_table_names()
        st.write(f"Total Discovered Tables: **{len(tables)}**")

        tabs = st.tabs(tables)
        for tab, tbl_name in zip(tabs, tables):
            with tab:
                tbl = schema.tables[tbl_name]
                col_data = []
                for c_name, c_schema in tbl.columns.items():
                    col_data.append({
                        "Column": c_name,
                        "Type": c_schema.data_type,
                        "Primary Key": "✅" if c_schema.is_primary_key else "",
                        "Foreign Key": "🔗 " + (c_schema.foreign_key_target or "") if c_schema.is_foreign_key else "",
                        "Nullable": c_schema.nullable
                    })
                st.dataframe(pd.DataFrame(col_data), use_container_width=True)

        st.markdown("---")
        st.markdown("### Discovered Foreign Key Relationships")
        if schema.relationships:
            rel_data = [{
                "Source Table": r.source_table,
                "Source Column": r.source_column,
                "Target Table": r.target_table,
                "Target Column": r.target_column
            } for r in schema.relationships]
            st.dataframe(pd.DataFrame(rel_data), use_container_width=True)
        else:
            st.info("No foreign key constraints defined.")

# -------------------------------------------------------------
# PAGE 3: Connection Manager
# -------------------------------------------------------------
elif page == "🔌 Database Connection":
    render_header("MySQL Database Connection Manager", "Connect to any local or remote MySQL database.")
    settings = get_settings()

    col1, col2 = st.columns(2)
    with col1:
        host = st.text_input("MySQL Host", value=settings.db.host)
        port = st.number_input("Port", value=settings.db.port)
        user = st.text_input("User", value=settings.db.user)
    with col2:
        password = st.text_input("Password", type="password", value=settings.db.password)
        database = st.text_input("Database Name", value=settings.db.database)

    col_btn1, col_btn2 = st.columns(2)
    with col_btn1:
        if st.button("Test & Connect to MySQL", type="primary", use_container_width=True):
            from database.connection import DatabaseSettings as DBSettings
            d_cfg = DBSettings(host=host, port=int(port), user=user, password=password, database=database)
            mgr = ConnectionManager(d_cfg)
            conn_url = d_cfg.get_connection_url()
            success, err = mgr.test_connection(conn_url)
            if success:
                st.session_state.engine = mgr.get_engine(conn_url)
                st.session_state.schema = SchemaDetector(st.session_state.engine).detect()
                st.session_state.db_name = f"MySQL: {database}"
                st.session_state.is_demo_db = False
                st.success(f"Successfully connected to MySQL database '{database}'!")
                st.rerun()
            else:
                st.error(f"Connection Failed: {err}")

    with col_btn2:
        if st.button("Use Pre-Loaded Demo Database (SQLite)", use_container_width=True):
            sqlite_file = BASE_DIR / "college_db.sqlite"
            if not sqlite_file.exists():
                from sample_database.setup_db import init_database
                init_database(create_engine(f"sqlite:///{sqlite_file}"), is_sqlite=True)
            eng = create_engine(f"sqlite:///{sqlite_file}")
            st.session_state.engine = eng
            st.session_state.schema = SchemaDetector(eng).detect()
            st.session_state.db_name = "College Management DB (Demo Mode)"
            st.session_state.is_demo_db = True
            st.success("Connected to local demo database!")
            st.rerun()

# -------------------------------------------------------------
# PAGE 4: Benchmark Evaluation
# -------------------------------------------------------------
elif page == "📊 Benchmark Evaluation":
    render_header("Traditional NLP Benchmark Evaluation", "Evaluate the rule-based semantic parser on benchmark questions.")
    if st.button("Run Benchmark Test Suite", type="primary"):
        with st.spinner("Running evaluation benchmark suite..."):
            from evaluation.evaluate import run_benchmark_suite
            summary_df, detailed_df = run_benchmark_suite(st.session_state.schema, st.session_state.engine)

            if not summary_df.empty:
                row = summary_df.iloc[0]
                m1, m2, m3, m4 = st.columns(4)
                with m1:
                    st.metric("Total Test Questions", int(row["Total Evaluated"]))
                with m2:
                    st.metric("SQL Validity", f"{row['SQL Validity (%)']:.1f}%")
                with m3:
                    st.metric("Exact Match (EM)", f"{row['Exact Match (EM %)']:.1f}%")
                with m4:
                    st.metric("Execution Accuracy (EX)", f"{row['Execution Accuracy (EX %)']:.1f}%")

            st.markdown("---")
            st.markdown("### Detailed Benchmark Predictions")
            display_cols = ["id", "difficulty", "question", "predicted_sql", "gold_sql", "is_valid", "exact_match", "execution_accuracy", "gen_time_ms"]
            available_cols = [c for c in display_cols if c in detailed_df.columns]
            st.dataframe(detailed_df[available_cols], use_container_width=True)

# -------------------------------------------------------------
# PAGE 5: Query History
# -------------------------------------------------------------
elif page == "📜 Query History":
    render_header("Session Query History", "Log of questions and generated SQL queries executed during this session.")
    if st.session_state.query_history:
        st.dataframe(pd.DataFrame(st.session_state.query_history), use_container_width=True)
    else:
        st.info("No queries executed in this session yet.")
