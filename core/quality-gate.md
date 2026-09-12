# Quality Gate

## Critical gates
A task is not complete if any applicable critical gate fails:
- primary behavior is incorrect
- authorization can be bypassed
- external input reaches dangerous sinks without validation/escaping
- important writes can corrupt state
- secrets are exposed
- migrations are unsafe without rollback/backup strategy
- tests for the modified critical behavior are missing
- application cannot start/build because of the change

## Non-critical dimensions
Score qualitatively:
- maintainability
- UX completeness
- performance
- observability
- documentation
- accessibility

Do not loop forever to chase arbitrary numeric scores. Record non-critical gaps as risks.
