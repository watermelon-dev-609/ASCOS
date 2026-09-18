# Deployment

**Owner:** Platform · **Last reviewed:** 2026-01-22

## Environments

| Environment | Deploy trigger | Who can deploy |
|---|---|---|
| `dev` | Every merge to `main` | Anyone |
| `staging` | Manual, from `main` | Anyone on the Platform team |
| `production` | Tag `release-*` only | Platform on-call |

## The release process

1. Merge to `main`. `dev` updates within about five minutes.
2. Run the smoke suite against `staging`. The suite is `npm run smoke:staging`.
3. Cut a `release-*` tag. Only tags matching that pattern reach production.
4. Watch the dashboards for fifteen minutes after the deploy.

## Rollback

Rollback is **re-deploying the previous tag**, not reverting the commit. The
command is `npm run deploy:rollback -- --tag release-<previous>`. Rolling back
takes roughly the same time as a deploy.

**If the database migration has run, you cannot roll back safely.** Migrations
run automatically on deploy. A release that includes a migration has to be
fixed forward instead. This is the single most common cause of a bad rollback
going worse, so check `migrations/` in the diff before you roll back.

## Known gap

There is no automated canary. An unhealthy release reaches all users at once.
Adding one has been on the roadmap since 2024 and is not scheduled.
