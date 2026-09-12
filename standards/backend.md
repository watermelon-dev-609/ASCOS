# Backend Standard

- Layer: transport → application/service → domain → repository/infrastructure where useful.
- Business logic must not depend directly on HTTP or framework globals.
- Centralize error mapping.
- Add structured logs with sensitive-field redaction.
- Authentication proves identity; authorization checks permission.
- Side effects must consider duplicate delivery/retry.
- Timeouts and external dependency failures must be handled deliberately.
