# ASCOS Agent Entry Point

Read `SKILL.md` first and treat it as the canonical operating policy.

`SKILL.md` is the **orchestrator**: it classifies the task and routes to capability skills under `skills/`.
`skills/` is behaviour ("what to do now"); `references/` is knowledge ("what to follow"); `templates/` shapes the output.

When editing this repo:
- inspect the existing repository before proposing architecture changes;
- preserve existing conventions unless they are harmful;
- make the smallest complete change that satisfies the requirement;
- update tests and documentation together with code;
- do not leave broken intermediate states;
- identify risky assumptions explicitly;
- run `python scripts/validate_skill.py` before committing;
- finish by summarizing changed files, verification performed and remaining risks.

For architecture decisions, use `templates/ADR.md`.
For large feature work, use `templates/PRD.md` and `templates/API_SPEC.md`.
Regression cases for the skill itself live in `evals/`.
