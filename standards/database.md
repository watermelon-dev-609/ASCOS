# Database Standard

- Enforce invariants in the database when possible.
- Use primary keys, foreign keys and unique constraints intentionally.
- Index by real query patterns.
- Use parameterized queries.
- Wrap multi-step consistency-sensitive writes in transactions.
- Protect against race conditions with constraints, locking or optimistic concurrency.
- Design migrations with forward and rollback/repair strategy.
- Avoid soft delete unless recovery/audit requirements justify it.
- Never expose raw credentials.
