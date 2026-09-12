# Observability Standard

Production services should expose enough information to answer:
- is it up?
- is it fast enough?
- are users failing?
- which dependency is failing?
- what changed?
- can we trace a problematic request?

Use structured logs, health checks, useful metrics and correlation IDs where proportionate.
Never log secrets or unnecessary personal data.
