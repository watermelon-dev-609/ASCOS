# Changelog

## 1.1.0 - 2026-09-14

v1.1.0 refactors ASCOS from a single large skill plus many references into a compact orchestrator backed by focused capability skills.

### Added

- Six capability skills under `skills/`: `requirements`, `architecture`, `implementation`, `debugging`, `code-review`, and `verification`.
- A `SKILL.md` routing table that maps user intent and task size to the correct capability chain.
- A regression-evaluation suite under `evals/`, covering small, medium, large, debugging, and adversarial scenarios.
- Executable debugging fixtures under `eval-fixtures/` for L0/L1/L2 evidence-level cases.
- `scripts/validate_skill.py`, a structural validator for front matter, links, orphaned skill files, required sections, metadata, and size checks.
- A v1.1 baseline report at `evals/runs/2026-09-14-baseline.md` with 22 evaluated cases and seven quality metrics.

### Changed

- Slimmed `SKILL.md` down to the canonical orchestrator: trigger, classify, route, and accept.
- Moved detailed engineering rules into `references/`, keeping behaviour in `skills/` and knowledge in reference documents.
- Reworked the debugging flow around an evidence ladder:
  - L0: reproducible red loop.
  - L1: observable but not fully stable reproduction.
  - L2: static reasoning from logs, traces, or incomplete evidence.
- Made L1/L2 downgrades non-blocking when useful progress is still possible, while requiring confidence level, supporting evidence, and escalation path to be stated.
- Clarified that L2 evidence is not enough to directly modify production code.
- Extended the evaluation rubric with `Output/Scale Fit` so small tasks are not overburdened with oversized process output.

### Fixed

- Removed stale references to a non-existent RFC template in release-facing documentation.
- Clarified repository-awareness guidance so `CONTEXT.md` is checked when domain terminology affects implementation.
- Removed answer leakage from debugging fixtures by moving expected reasoning into evaluator prompts.
- Documented that executable fixtures should be run one at a time to avoid cross-case workspace pollution.
- Clarified `context-model.md` guidance: greenfield projects do not need a context model before the domain vocabulary is known, but should add one once those terms matter.

### Evaluation

- Completed all 22 regression cases.
- Baseline highlights:
  - Routing: 21/21 applicable cases.
  - Evidence discipline: 22/22.
  - False completion: 0.
  - Security misses: 0.
  - Overengineering blocks held across adversarial cases.

## 1.0.0

- Added canonical `SKILL.md`.
- Added dynamic role dispatch.
- Added planning, decision, research, reflection, and quality engines.
- Added engineering departments.
- Added coding, API, security, testing, and deployment standards.
- Added PRD, ADR, API, test, and release templates.
- Added adapters for major AI coding assistants.
