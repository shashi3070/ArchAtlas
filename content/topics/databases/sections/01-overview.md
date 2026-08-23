# Overview
Storage choice shapes everything downstream: consistency options, scaling ceiling, operational story. Three broad families cover most needs:

- **Relational (PostgreSQL, MySQL)** - tables, SQL, transactions, mature tooling. Default choice until proven insufficient.
- **Document (MongoDB, Firestore)** - JSON-ish documents, flexible schema, horizontal sharding built in.
- **Key-value / wide-column (Redis, DynamoDB, Cassandra)** - predictable O(1)/O(log n) access by key; massive scale, narrow query model.

Start relational. Its transactional guarantees and ad-hoc queryability accelerate development; migration paths to other engines exist once workload reality is measured, not guessed.
