"""Nightly sweep that advances pending orders.

In production this is triggered by a Kubernetes CronJob at 02:00 every day.
The scheduler configuration lives in the infra repo, not here.
"""

BATCH_SIZE = 100


def sweep(db, batch_size=BATCH_SIZE):
    """Move every pending order to `processing`, batch by batch.

    Args:
        db: object exposing fetch_pending(limit, offset) and update_status(id, status)
        batch_size: how many rows to read per page

    Returns:
        Number of orders moved.
    """
    moved = 0
    page = 0
    while True:
        rows = db.fetch_pending(limit=batch_size, offset=page * batch_size)
        if not rows:
            break
        for row in rows:
            db.update_status(row["id"], "processing")
            moved += 1
        page += 1
    return moved
