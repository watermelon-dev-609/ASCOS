# Data Retention

**Owner:** Data · **Last reviewed:** 2025-09-30

## How long we keep things

| Data class | Retention | Notes |
|---|---|---|
| Application logs | 30 days | Then deleted, not archived |
| Audit logs | 7 years | Required by contract |
| Customer records | Life of the account + 90 days | Deletion request shortens this to 30 days |
| Analytics events | 13 months | Aggregates are kept indefinitely, raw events are not |
| Backups | 35 days | Snapshots only, no point-in-time recovery |

## Deletion requests

A customer deletion request must be honoured within **30 days**. The account
record and analytics events go; audit logs do **not**, because they are kept
under a separate contractual obligation. Support should tell customers this
up front rather than after they ask.

## Conflicting older guidance

An earlier version of this document said analytics events were kept for 24
months and that deletion requests were honoured within 60 days. **Both numbers
are wrong.** The table above is current. If a system still implements the old
numbers, that is a bug worth filing.

## Who can export

Exporting customer records needs level 3 access (see `onboarding.md`) and a
second person present. Exports are logged and the log is part of the audit
trail, so it survives the 30-day application log window.
