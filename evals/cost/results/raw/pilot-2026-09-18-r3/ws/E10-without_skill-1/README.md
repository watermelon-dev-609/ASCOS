# cost-docs

A small corpus of internal documents, used as the substrate for the case that
asks for question answering over internal docs (E10).

It exists because `cost-app` has no documents in it, and that case cannot be
answered from a code tree. When a case has nothing to work on, both arms wander
outside the workspace, get denied, and stop — two arms blocked identically
cannot differ, so the pair measures nothing.

## Contents

| File | What it covers |
|---|---|
| `docs/onboarding.md` | First-week setup, who owns what |
| `docs/deployment.md` | Release process, environments, rollback |
| `docs/incident-runbook.md` | Severity levels, paging, postmortems |
| `docs/data-retention.md` | How long different data classes are kept |
| `docs/expense-policy.md` | Limits, approvals, receipts |
| `docs/api-conventions.md` | Naming, versioning, error shape |

## Notes for anyone editing this fixture

- The documents are deliberately **partly overlapping and partly out of date**,
  the way real internal docs are. That is the point: a question-answering
  system has to decide which source wins. Do not "fix" the inconsistencies.
- Keep each document short enough that a run can read all of them. If the
  corpus grows past what fits comfortably in context, the case stops measuring
  reasoning and starts measuring truncation.
- Nothing here should name a specific defect to hunt for. The fixture
  describes the material, not the answer.
