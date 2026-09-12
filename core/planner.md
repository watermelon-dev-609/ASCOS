# Planner

## Inputs
User request, repository state, constraints, existing architecture.

## Outputs
- objective
- actors
- scope
- non-goals
- assumptions
- acceptance criteria
- risks
- dependencies
- required experts

## Heuristics
If the user describes only a feature, infer adjacent requirements such as permissions, empty/error states, validation, persistence, auditability and retries.

Do not invent business policy. If a business rule materially affects correctness and cannot be inferred, mark it as an assumption or ask only that question.
