# Security Standard

Threat-model trust boundaries.

Always consider:
- authentication
- authorization / horizontal and vertical privilege escalation
- SQL/NoSQL/command injection
- XSS
- CSRF where cookie/session auth applies
- SSRF
- path traversal
- unsafe file upload
- secret exposure
- insecure direct object reference
- brute-force / abuse controls
- sensitive log data
- secure password hashing
- token expiry/revocation where required
- dependency vulnerabilities
- security headers and CSP where applicable

Frontend visibility is not authorization.
