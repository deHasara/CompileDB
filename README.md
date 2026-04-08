# CompileDB
CompileDB is a research prototype that explores the benefits of adopting the Entity–Relationship (E/R) model as a primary, user-facing abstraction for data management. Rather than requiring users to interact with relational schemas directly, CompileDB enables them to define and manipulate data using SQL over high-level conceptual constructs such as entities and relationships.

The system is implemented as a lightweight Python layer on top of an existing relational database system, currently PostgreSQL. This architecture allows CompileDB to leverage the maturity and robustness of a well-established storage engine while focusing its research contributions on schema mapping, query translation, and workload-aware, cost-based optimization of relational schemas. By bridging the gap between conceptual modeling and logical design, CompileDB provides a platform for systematically studying how high-level data models can be translated into efficient relational representations across diverse workloads while enabling full logical independence.

## Using CompileDB
