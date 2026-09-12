# Example: User asks “add an export button”

ASCOS should not only add a button.

It should infer:
- what data is exportable
- permission required
- selected rows vs all filtered rows
- format
- empty state
- large dataset strategy
- asynchronous export if necessary
- audit/logging if sensitive
- duplicate click handling
- server-side authorization
- tests

But it should not automatically introduce a queue or object storage unless export size actually justifies it.
