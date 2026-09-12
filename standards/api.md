# API Standard

- Define request/response contract before implementation.
- Use stable naming and versioning where public evolution is expected.
- Validate body, params, query and headers.
- Return consistent error structure and machine-readable error codes.
- Use appropriate HTTP semantics.
- Do not leak internal stack traces or sensitive details.
- Make retryable mutations idempotent where practical.
- Document pagination, sorting, filtering and limits.
- Apply authorization server-side.
