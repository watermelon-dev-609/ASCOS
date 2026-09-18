# Incident Runbook

**Owner:** Platform · **Last reviewed:** 2026-02-11

## Severity levels

| Sev | Definition | Paging | Postmortem required |
|---|---|---|---|
| 1 | Complete outage or data loss | Page immediately, any hour | Yes, within 3 days |
| 2 | Major feature broken, no workaround | Page during business hours | Yes, within 7 days |
| 3 | Broken with a workaround | Message the owning team | No |
| 4 | Cosmetic | Ticket only | No |

**Sev 1 and Sev 2 are the only levels that page.** Anything lower goes to the
owning team as a message. If you are unsure, declare the higher severity and
downgrade later — downgrading is free, declaring late is not.

## During an incident

- One incident commander at a time. Say who it is in channel before you start.
- Communicate every twenty minutes even when there is no news.
- Mitigate first, diagnose second. Rollback is a valid mitigation; see
  `deployment.md` for when it is not.

## Postmortems

Postmortems are **blameless** and go in the `postmortems/` repository. A
postmortem that names an individual rather than a condition gets sent back.
Action items need an owner and a date, or they are not action items.

## On-call handoff

Handoff happens at 09:00 local time. The outgoing person writes the handoff
note, not the incoming one. A handoff with no open incidents still needs a note
saying so.
