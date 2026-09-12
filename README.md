# ASCOS - AI Software Company OS

> A reusable collaboration framework for AI coding assistants. It orchestrates a single coding model into a dynamically coordinated software company that can plan, challenge, design, implement, review, test, deploy and improve software — instead of merely generating code.

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

ASCOS (**AI Software Company OS**) is not a full software framework, nor a system of dozens of independently running agents. Its positioning is a **senior software-development orchestration skill (Skill)** that does one thing well:

> Turn the user's *incomplete development requirement* into a complete, enterprise-grade software engineering workflow.

It codifies a proven engineering methodology into `SKILL.md`, and provides supporting engines, expert-role guidance, standards and document templates under `core/`, `departments/`, `standards/` and `templates/`. It is loaded and executed by AI coding assistants such as Codex.

**Key point**: ASCOS does **not** require every task to use every role. The Dispatcher selects only the expertise the current task actually needs — small tasks stay small, complex tasks are handled comprehensively.

---

## Core features

- **Requirements are incomplete by default — AI fills the gaps**: proactively considers boundaries, exceptions, permissions, security, performance and observability the user did not mention, instead of asking question after question.
- **Dynamic expert perspective switching**: automatically shifts between Product / Architect / Frontend / Backend / Database / Security / QA / DevOps / CTO viewpoints per task — changing *how to think*, not spinning up a swarm of agents.
- **Enterprise engineering standards enforced**: interface-contract-first, unified error codes, business/IO separation, input validation, idempotency, transactions, concurrency handling, parameterized queries, server-side authN/authZ — all built in.
- **A closed loop, not "code then done"**: after implementation it must pass testing, Code Review, a quality gate and CTO review, and ship a remaining-risk list.
- **Anti-overengineering**: prefer the simple solution; any new infrastructure (queue / cache / microservice / Kubernetes / vector DB) must state its benefit *and* cost.

---

## Workflow

```text
User intent
  -> Planner
  -> First-principles analysis
  -> Adversarial review
  -> Decision Engine
  -> Dynamic Dispatcher (selects the necessary roles)
  -> Expert execution
  -> Review
  -> Quality Gate
  -> CTO review
  -> Delivery
  -> Retrospective
```

Increased internal rigor should raise **output quality**, not **answer length**.

---

## Installation

Clone (or copy) this repository into your Codex skills directory:

```bash
git clone https://github.com/watermelon-dev-609/ASCOS-v1.0.git ~/.codex/skills/ai-software-company-os
```

Restart Codex after installation if the skill does not appear immediately.

---

## Usage

Invoke the skill when you want Codex to handle software work with a full engineering workflow:

```text
Use $ai-software-company-os to plan, implement, test and review this software task.
```

For tool-specific integration, see the [`integrations/`](integrations/) directory.

---

## Project structure

| Path | Description |
|------|-------------|
| `SKILL.md` | Canonical skill entry point and instructions (core file) |
| `agents/` | Codex UI metadata |
| `core/` | Planning, dispatch, decision, review, quality and learning engines |
| `departments/` | Dynamically selected expert-role guidance |
| `standards/` | Coding, security, API, database, frontend, backend, testing, deployment rules |
| `templates/` | PRD, ADR, RFC, API, test and release templates |
| `checklists/` | Concise gates for fast execution |
| `integrations/` | Tool-specific adapters |
| `examples/` | Examples of how ASCOS should behave |

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
