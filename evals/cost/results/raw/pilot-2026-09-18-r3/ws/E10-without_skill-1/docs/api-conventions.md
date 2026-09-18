# API Conventions

**Owner:** API guild · **Last reviewed:** 2026-01-08

## Naming

- Paths are plural nouns: `/orders`, not `/order`.
- Nested resources go at most two levels deep. `/orders/{id}/items` is fine;
  `/orders/{id}/items/{itemId}/parts` is not — flatten it to `/item-parts`.
- Use snake_case in request and response bodies. Query parameters are
  snake_case too. Only headers use kebab-case.

## Versioning

The version is in the path: `/v1/orders`. Breaking changes get a new major
version; the old one is supported for 12 months after the new one ships. Adding
an optional field is not breaking. Adding a required field is.

## Errors

Errors are always this shape:

```json
{ "error": { "code": "order_not_found", "message": "..." } }
```

`code` is stable and machine-readable; `message` is for humans and may change
without notice. **Clients must branch on `code`, never on `message`.**

Use 400 for a malformed request, 401 for missing credentials, 403 for present
but insufficient credentials, 404 for a missing resource, and 422 for a
well-formed request that violates a business rule. Returning 400 for a business
rule violation is the most common mistake in this codebase.

## Pagination

Cursor-based, `?cursor=` and `?limit=`, with `next_cursor` in the response.
`limit` defaults to 20 and caps at 100. Offset pagination exists on `/v1/orders`
for backwards compatibility and should not be used in new code.
