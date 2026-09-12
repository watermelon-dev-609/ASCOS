# Example: Authentication feature

Minimum workflow:
Architect → Backend → Security → QA → Reviewer.

Key checks:
- password hashing
- session/token lifecycle
- brute-force controls
- server-side authorization
- refresh/logout semantics
- CSRF if cookie-authenticated
- secure cookies where applicable
- logging without passwords/tokens
- tests for invalid credentials, expired session and forbidden access
