import os, sys
sys.path.append('e:/Projects/NLP')

from sample_database.setup_db import init_database
from sqlalchemy import create_engine

# Create temporary SQLite DB
sqlite_path = 'e:/Projects/NLP/college_test.sqlite'
if os.path.exists(sqlite_path):
    os.remove(sqlite_path)
engine = create_engine(f'sqlite:///{sqlite_path}')
init_database(engine, is_sqlite=True)
print('✅ SQLite DB initialized')

# Detect schema and print tables & relationships
from database.schema_detector import SchemaDetector
schema = SchemaDetector(engine).detect()
print('🗂️ Tables detected:', list(schema.tables.keys()))
print('🔗 Relationships:')
for rel in schema.relationships:
    print(f"  {rel.source_table}.{rel.source_column} -> {rel.target_table}.{rel.target_column}")

# Baseline generation for a join query
from generation.baseline_generator import BaselineSQLGenerator
question = 'Show student names and the name of their department'
baseline = BaselineSQLGenerator(schema)
res = baseline.generate(question)
print('🤖 Generated SQL (baseline):')
print(res.sql)

# Validate and execute the query
from validation.sql_validator import SQLValidator
from validation.schema_validator import SchemaValidator
sql_val = SQLValidator()
sql_res = sql_val.validate(res.sql)
print('SQL validation:', sql_res.is_valid, sql_res.error_message or 'OK')

schema_val = SchemaValidator(schema)
schema_res = schema_val.validate(sql_res)
print('Schema validation:', schema_res.is_valid, schema_res.error_message or 'OK')

if sql_res.is_valid and schema_res.is_valid:
    from database.query_executor import QueryExecutor
    executor = QueryExecutor(engine)
    exec_res = executor.execute(res.sql)
    print('⚡ Execution success:', exec_res.success, 'Rows:', exec_res.row_count)
    if exec_res.success:
        df = exec_res.to_dataframe()
        print('📊 Result preview:')
        print(df.head())
else:
    print('❌ Query not executed due to validation failures')

