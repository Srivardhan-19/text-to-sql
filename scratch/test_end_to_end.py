import os, sys
sys.path.append('e:/Projects/NLP')
from sample_database.setup_db import init_database
from sqlalchemy import create_engine
sqlite_path = 'e:/Projects/NLP/college_db_test.sqlite'
if os.path.exists(sqlite_path):
    os.remove(sqlite_path)
engine = create_engine(f'sqlite:///{sqlite_path}')
init_database(engine, is_sqlite=True)
print('DB initialized')
# Detect schema
from database.schema_detector import SchemaDetector
schema = SchemaDetector(engine).detect()
print('Tables:', [t.name for t in schema.tables])
# Baseline generation
from generation.baseline_generator import BaselineSQLGenerator
question = 'Show all students'
gen = BaselineSQLGenerator(schema)
res = gen.generate(question)
print('Generated SQL:', res.sql)
# Execute
from database.query_executor import QueryExecutor
executor = QueryExecutor(engine)
exec_res = executor.execute(res.sql)
print('Exec success:', exec_res.success, 'Rows:', exec_res.row_count)
if exec_res.success:
    df = exec_res.to_dataframe()
    print(df.head())

