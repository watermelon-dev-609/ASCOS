# ASCOS — AI Software Company Skill

> A software-development orchestration skill that turns incomplete user requirements into production-ready solutions through dynamic expert-role switching, first-principles reasoning, adversarial review, enterprise engineering standards, automated testing, review, and risk analysis.

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Version](https://img.shields.io/badge/Version-1.0.0-green.svg)](ascos.json)

---

## Table of Contents

- [What is this](#what-is-this)
- [Core features](#core-features)
- [Workflow](#workflow)
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

```text
User intent
  -> Repository awareness (existing project)
  -> Requirement completeness check
  -> First-principles analysis
  -> Adversarial review
  -> Requirement completion
  -> Change-impact analysis
  -> Dynamic role selection
  -> Architecture / design / implementation
  -> Testing / systematic debugging
  -> Security review
  -> Code review
  -> Pre-completion verification (real build/test evidence)
  -> Quality gate
  -> Release / migration / rollback check (if deploying)
  -> CTO final review
  -> Delivery + risk list
```

Increased internal rigor should raise **output quality**, not **answer length**.

---

## Installation

Clone this repository into your Codex skills directory:

```bash
git clone https://github.com/watermelon-dev-609/ASCOS-v1.0.git ~/.codex/skills/ai-software-company-skill
```

Restart Codex after installation if the skill does not appear immediately.

---

## Usage

Invoke the skill when you want Codex to handle software work with a full engineering workflow:

```text
Use $ai-software-company-skill to plan, implement, test and review this software task.
```

The skill is tool-agnostic: the `SKILL.md` contract works the same in Codex, Cursor, Claude Code, or any agent that loads Markdown-based skills.

---

## Project structure

| Path | Description |
|------|-------------|
| `SKILL.md` | Canonical skill entry point and 17-step workflow (core file) |
| `agents/` | Codex UI metadata |
| `references/` | Role, architecture, frontend, backend, database, security, testing, quality-gate, repository-awareness, change-impact, verification, debugging, definition-of-done and more reference modules |
| `templates/` | PRD, ADR, API_SPEC, TEST_PLAN document templates |
| `ascos.json` | Skill metadata |
| `AGENTS.md` | Agent entry-point guidance |
| `CHANGELOG.md` | Change history |

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

Current version: **v1.0.0**

See [`CHANGELOG.md`](CHANGELOG.md) for the change history.
