# Release Notes

## v1.1.0 - 2026-09-14

ASCOS v1.1.0 is a structural release. It turns the project into a clearer software-development orchestration system: a small canonical orchestrator in `SKILL.md`, six focused capability skills in `skills/`, and knowledge references kept in `references/`.

### Highlights

- Introduced six capability skills: `requirements`, `architecture`, `implementation`, `debugging`, `code-review`, and `verification`.
- Added an intent-based routing table so tasks are classified by size and routed to the smallest useful workflow.
- Rebuilt debugging around an evidence ladder that separates reproducible failures from observable-but-flaky signals and static reasoning.
- Added regression evaluations, executable debugging fixtures, and a v1.1 baseline report.
- Added `scripts/validate_skill.py` to catch structural issues before release.
- Cleaned up stale documentation references and clarified when `CONTEXT.md` should be used.

### Compatibility

This release keeps the public skill entry point at `SKILL.md` and keeps metadata in `ascos.json`. Existing installs should continue to load the skill normally after pulling the new version.

### Validation

Before tagging this release, run:

```bash
python scripts/validate_skill.py --strict
```

The v1.1 baseline is recorded in `evals/runs/2026-09-14-baseline.md`.
