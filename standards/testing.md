# Testing Standard

Tests should cover:
- happy path
- boundary values
- invalid input
- unauthorized/forbidden access
- duplicate/retry behavior when relevant
- transaction rollback/error behavior
- concurrency-sensitive invariants when relevant

Prefer behavior-focused tests over implementation-coupled tests.
Critical business rules require tests before completion.
