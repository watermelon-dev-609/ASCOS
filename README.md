# ASCOS - AI Software Company OS

ASCOS is a reusable operating framework for AI coding assistants. It turns a single coding model into a dynamically coordinated software company that can plan, challenge, design, implement, review, test, deploy and improve software instead of merely generating code.

## What this repository contains

This repository packages ASCOS as a Codex-compatible skill. The canonical skill entry point is `SKILL.md`; the supporting folders contain role guidance, engineering standards, checklists, examples and tool-specific integration prompts.

## Core idea

User intent -> Planner -> First-principles analysis -> Adversarial review -> Decision Engine -> Dynamic Dispatcher -> Expert execution -> Review -> Quality Gate -> CTO review -> Delivery -> Retrospective.

ASCOS does **not** require every task to use every role. The dispatcher selects only the expertise necessary for the current task.

## Design goals

- Complete the user's objective, not merely the literal request.
- Treat requirements as incomplete by default and responsibly fill gaps.
- Prefer simple, maintainable solutions over fashionable complexity.
- Make assumptions explicit.
- Separate facts, assumptions, recommendations and trade-offs.
- Apply enterprise-grade security, testing, observability and documentation where they are proportionate.
- Avoid overengineering through KISS, DRY and YAGNI.
- Challenge unsafe or weak technical decisions rather than blindly complying.

## Installation for Codex

Clone or copy this repository into your Codex skills directory:

```bash
git clone https://github.com/watermelon-dev-609/ASCOS-v1.0.git ~/.codex/skills/ai-software-company-os
```

Restart Codex after installation if the skill does not appear immediately.

## Usage

Invoke the skill when you want Codex to handle software work with a full engineering workflow:

```text
Use $ai-software-company-os to plan, implement, test and review this software task.
```

For specific tools, see `integrations/`.

## Project structure

- `SKILL.md` - canonical Codex skill instructions.
- `agents/` - Codex UI metadata.
- `core/` - planning, dispatch, decision, review, quality and learning engines.
- `departments/` - dynamically selected expert roles.
- `standards/` - coding, security, API, DB, frontend, backend, testing and deployment rules.
- `templates/` - PRD, ADR, RFC, API, test and release templates.
- `checklists/` - concise gates for fast execution.
- `integrations/` - tool-specific adapters.
- `examples/` - examples of how ASCOS should behave.

## Operating principle

ASCOS is a framework, not a reason to produce huge answers. Internal rigor should increase output quality, not output length. Small tasks should remain small. Complex tasks should be handled comprehensively.

## Version

v1.0.0
