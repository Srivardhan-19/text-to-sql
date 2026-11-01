# Literature Review

## 1. Spider: Cross-Domain Semantic Parsing Benchmark
- **Citation**: Yu, T., Zhang, R., Yang, K., Yasunaga, M., Wang, D., Li, Z., Ma, J., Li, I., Yao, Q., Roman, S., Zhang, Z., & Radev, D. (2018). *Spider: A Large-Scale Human-Labeled Dataset for Complex and Cross-Domain Semantic Parsing and Text-to-SQL Task*. EMNLP 2018.
- **Relevance**: Established the necessity for cross-database generalization where models are evaluated on unseen database schemas. Demonstrates why hardcoded schema rules fail on new relational domains.
- **Application in Our Project**: Inspired our dynamic metadata introspection and schema-linking graph traversal, ensuring our application operates on any relational database without hardcoded table structures.

## 2. RAT-SQL: Relation-Aware Schema Encoding
- **Citation**: Wang, B., Shin, R., Liu, X., Polozov, O., & Richardson, M. (2020). *RAT-SQL: Relation-Aware Schema Encoding and Linking for Text-to-SQL Parsers*. ACL 2020.
- **Relevance**: Addressed the schema-linking problem by explicitly modeling relations between question tokens and database schema elements (columns, tables, primary/foreign keys).
- **Application in Our Project**: Informs our schema-linking module (`nlp/entity_extractor.py`) and BFS shortest-path relationship finder (`database/schema_detector.py`).

## 3. BIRD: Database Grounded Text-to-SQL
- **Citation**: Li, J., Hui, B., Qu, G., Li, B., Wang, J., Xiao, B., Feng, W., Zhao, M., Chen, L., Qin, B., & Li, R. (2023). *Can LLM Already Serve as a Database Interface? A BIg Bench for Large-Scale Database Grounded Text-to-SQLs*. NeurIPS 2023.
- **Relevance**: Emphasizes Execution Accuracy (EX) over Exact Match (EM), noting that syntactically different SQL queries can compute identical semantic result sets.
- **Application in Our Project**: We implement dual evaluation metrics (`Exact Match` via AST canonicalization and `Execution Accuracy` via result set tuple comparison).

## 4. Spider 2.0 (2024)
- **Citation**: Lei, T. et al. (2024). *Spider 2.0: Evaluating Language Models on Real-World Enterprise Text-to-SQL Workflows*.
- **Relevance**: Focuses on dialect compatibility, execution safety, and real enterprise database interaction (dialect quirks, read-only guarantees).
- **Application in Our Project**: Addressed through SQLGlot AST safety filtering, restricting statements to read-only queries, and row limit ceiling enforcement.
