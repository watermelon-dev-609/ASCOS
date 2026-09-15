# ASCOS — AI Software Company Skill

> A software-development orchestration skill that turns incomplete user requirements into production-ready solutions through dynamic expert-role switching, first-principles reasoning, adversarial review, enterprise engineering standards, automated testing, review, and risk analysis.

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Version](https://img.shields.io/badge/Version-1.2.2-green.svg)](ascos.json)

---

## Table of Contents

- [What is this](#what-is-this)
- [Core features](#core-features)
- [Workflow](#workflow)
- [What's new in v1.1](#whats-new-in-v11)
- [Installation](#installation)
- [Usage](#usage)
- [Project structure](#project-structure)
- [Engineering standards](#engineering-standards)
- [Design principles](#design-principles)
- [Use cases](#use-cases)
- [License](#license)

---

## What is this

ASCOS (**AI Software Company Skill**) is not an OS, not a framework of dozens of independently running agents, and not a heavyweight orchestration platform. Its positioning is a **senior software-development orchestration skill (Skill)** that does one thing well:

> Turn the user's *incomplete development requirement* into a complete, enterprise-grade software engineering workflow.

It codifies a proven engineering methodology into `SKILL.md`, with supporting reference modules under `references/` and document templates under `templates/`. It is loaded and executed by AI coding assistants such as Codex.

**Key point**: ASCOS does **not** require every task to use every role. It switches only the expertise the current task actually needs — small tasks stay small, complex tasks are handled comprehensively. It also deliberately avoids overengineering: a simple requirement is never silently expanded into microservices, Redis, MQ, or Kubernetes.

---

## Core features

- **Requirements are incomplete by default — AI fills the gaps**: proactively considers boundaries, exceptions, permissions, security, performance and observability the user did not mention, instead of asking question after question.
- **Dynamic expert perspective switching**: automatically shifts between Product / Architect / Frontend / Backend / Database / AI / Security / QA / DevOps / CTO viewpoints per task — changing *how to think*, not spinning up a swarm of agents.
- **Enterprise engineering standards enforced**: interface-contract-first, unified error codes, business/IO separation, input validation, idempotency, transactions, concurrency handling, parameterized queries, server-side authN/authZ — all built in.
- **A closed loop, not "code then done"**: after implementation it must pass systematic testing, Code Review, pre-completion verification, a quality gate and CTO review, and ship a remaining-risk list.
- **Anti-overengineering**: prefer the simple solution; any new infrastructure (queue / cache / microservice / Kubernetes / vector DB) must state its benefit *and* cost.

---

## Workflow

ASCOS is an **orchestrator, not a worker**: `SKILL.md` classifies the task, then routes to capability skills. It does not carry all the knowledge itself — its core ability is knowing *who to call*.

```text
User intent
      |
   ASCOS (orchestrator)
      |
  classify + size
      |
  Skill Router
      |
  +-----------+-----------+-----------+
  |           |           |           |
requirements  architecture  implementation  debugging
  |           |           |           |
  v           v           v           v
Spec/PRD     ADR/API    TDD loop    root cause
                           |
                       code-review
                           |
                       verification -> delivery + risk list
```

| Intent | Route |
|--------|-------|
| Vague / one-line request | `requirements` -> `implementation` |
| New project | `requirements` -> `architecture` -> `implementation` |
| New feature / page / API | `requirements` -> `implementation` -> `code-review` -> `verification` |
| Bug / regression | `debugging` -> `code-review` -> `verification` |
| Refactor / tech selection | `architecture` -> `implementation` -> `verification` |
| Trivial UI text change | `implementation` -> `verification` |
| Auth / payment / public API | `requirements` -> `architecture` (+`security`) -> `implementation` -> `verification` |

Increased internal rigor should raise **output quality**, not **answer length**.

---

## What's new in v1.1

v1.1 turns ASCOS from a single large skill into a compact orchestrator with six focused capability skills:

- `requirements` completes incomplete requests and defines acceptance criteria.
- `architecture` handles design boundaries, impact analysis and ADR-worthy decisions.
- `implementation` keeps changes small, tested and aligned with the existing repository.
- `debugging` follows an evidence ladder from reproducible failures to confidence-scoped analysis.
- `code-review` checks the diff against both engineering standards and the user request.
- `verification` requires real build, test or validation evidence before claiming completion.

This release also adds a regression-evaluation suite, executable debugging fixtures, and a structural validator so future changes can be checked before release.

See [`CHANGELOG.md`](CHANGELOG.md) and [`RELEASE_NOTES.md`](RELEASE_NOTES.md) for the full v1.1.0 release details.

---

## Installation

Clone this repository into your Codex skills directory:

```bash
git clone https://github.com/watermelon-dev-609/ASCOS.git ~/.codex/skills/ai-software-company-skill
```

> The repository was renamed from `ASCOS-v1.0` to `ASCOS`. The old URL still
> redirects, but use this one as canonical.

Restart Codex after installation if the skill does not appear immediately.

---

## Usage

Invoke the skill when you want Codex to handle software work with a full engineering workflow:

```text
Use $ai-software-company-skill to plan, implement, test and review this software task.
```

Portability: the skill is **designed to be portable** — plain Markdown, no host-specific APIs.
It is **currently verified on Codex**; other hosts (Cursor, Claude Code, and any agent that loads
Markdown-based skills) are **best-effort**. Hosts differ in nested-skill loading, subagent support
and auto-trigger behaviour, so `code-review` defines an explicit fallback when subagents are
unavailable. Verified hosts are listed in [`ascos.json`](ascos.json).

---

## Project structure

| Path | Description |
|------|-------------|
| `SKILL.md` | Canonical entry point: the orchestrator (trigger -> classify -> route -> accept) |
| `skills/` | Six capability skills (**behaviour**: what to do now) — `requirements`, `architecture`, `implementation`, `debugging`, `code-review`, `verification` |
| `references/` | Knowledge modules (**what to follow**): security, frontend, backend, database, testing, release, observability, roles, context-model, non-negotiables, engineering-standards… |
| `templates/` | PRD, ADR, API_SPEC, TEST_PLAN, CONTEXT document templates |
| `evals/` | 42 cases: 22 behaviour (small / medium / large / bugs / adversarial) + 20 trigger (10 must-fire / 10 must-not-fire) |
| `scripts/` | `validate_skill.py` (structural validator), `eval_harness.py` (eval runner: check / prompt / ingest / report), `test_eval_tools.py` (unit tests) |
| `agents/` | Codex UI metadata |
| `ascos.json` | Skill metadata |
| `AGENTS.md` | Agent entry-point guidance |
| `CHANGELOG.md` | Change history |

Run the validator before committing:

```bash
python scripts/validate_skill.py --strict
python scripts/eval_harness.py check --strict
python scripts/test_eval_tools.py
```

---

## Eval evidence

Measured behaviour, with the protocols written down **before** each run so the
thresholds cannot be fitted to the results afterwards:

```bash
python scripts/eval_harness.py report --k 1 3     # evals/results/report.md
```

Recorded runs live in `evals/runs/`, raw records in `evals/results/records.jsonl`.

**Stage 1 (triggering & boundary stability) is complete and frozen at v1.2.2** —
see [`STAGE-1-ACCEPTANCE.md`](STAGE-1-ACCEPTANCE.md). The `description` is no longer
changed unless new evidence shows a stable failure mode (≥2 valid runs failing in the
same direction). Per-skill evals, forced-activation robustness, the behaviour cases,
and token/latency measurement are explicitly deferred to the next stage.

| Run | What it measured | Result |
|---|---|---|
| Round 6 · description fix | Full 20-case regression after the fix below | must-fire **12/12** (T01 3/3); must-not-fire **30/30, zero misfires** |
| Round 5 · must-fire rerun | Runs 2–3 of the 10 must-fire cases, to see whether the under-triggers were noise | **T01 3/3** under-trigger (real gap); T08 1/3 (observe); must-fire 85.2% |
| Round 4 · faithful arm | Does ASCOS fire when it should, and stay out when it shouldn't? 3 passes over the 10 near-miss cases | must-not-fire **30/30, zero misfires**; must-fire 7/10 |
| Round 3 · forced arm | Same suite, but `SKILL.md` force-loaded — measures "ASCOS always on", **not** triggering | must-fire 10/10; must-not-fire 2/10 |

Two rubric rules were tightened before Round 6 and are part of what the numbers
mean, so they belong here rather than in a footnote:

- An ASCOS deliverable is **corroboration only**. A bare model can emit a
  `剩余风险清单`; only a primary signal (declared load, routing chain, or a
  capability-specific behaviour shape) can carry a fire verdict.
- **Fewer than 2 valid runs is inconclusive**, not a rate. One observation
  cannot support a stability claim in either direction.

**Read the delta with care.** On must-fire cases the with/without delta is partly
true by construction — an arm with no ASCOS cannot fire — so it shows the arms were
isolated, not that ASCOS improved anything. The informative number is how often the
with arm fires on must-not-fire cases.

**Triggering is highly sensitive to how the skill is loaded** (0/10 · 10/10 · 7/10
across three loading mechanisms on the same 20 cases). Trigger rates are therefore
not comparable across harnesses unless the loading method is stated too. The
Round 3 headline of "2 misfires" turned out to be an artefact of force-loading and
did not reproduce in Round 4 — the corresponding rule change was withdrawn rather
than shipped.

---

## Engineering standards

ASCOS enforces the following principles during development and review:

- **Design**: high cohesion / low coupling, Single Responsibility (SRP), KISS, DRY, YAGNI; interface contract first.
- **Backend**: layered architecture, unified error codes, business/IO separation, validate all external input, idempotency, transaction rollback, concurrency handling, parameterized queries (no injection), server-side authN/authZ.
- **Frontend**: separate base from business components, Design Tokens for styling, Loading / Empty / Error / No-permission states, form validation, duplicate-submit prevention, ESC-to-close modals, XSS protection, automatic resource cleanup.
- **Security**: deny by default, object-level authZ, injection / XSS protection, IDOR protection, log desensitization, secrets via environment variables (no hardcoding).
- **Testing**: cover normal / boundary / exception scenarios; critical paths must have targeted test cases.

---

## Design principles

1. Complete the user's **objective**, not just the literal request.
2. Treat requirements as incomplete by default and responsibly fill the gaps.
3. Prefer simple, maintainable solutions over fashionable complexity.
4. Make assumptions explicit; separate facts, assumptions, recommendations and trade-offs.
5. Apply enterprise-grade security, testing, observability and documentation where proportionate.
6. Avoid overengineering through KISS / DRY / YAGNI.
7. Challenge unsafe or weak technical decisions rather than blindly complying.

---

## Use cases

- Feature / page / API development
- Architecture design and technology selection
- Bug fixing and code refactoring
- RAG / AI-feature development
- Deployment and DevOps
- Product planning and technical review
- Production-readiness work

---

## License

This project is open source under the [MIT License](LICENSE).

---

## Version

Current version: **v1.2.2**

See [`CHANGELOG.md`](CHANGELOG.md) for the change history.
