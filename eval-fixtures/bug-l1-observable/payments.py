"""Payment charging with an intentional check-then-act race."""

import json
import os
import random
import threading
import time

_HERE = os.path.dirname(os.path.abspath(__file__))
LOG_PATH = os.path.join(_HERE, "logs", "payments.log")

# How often the "external fraud check" between the read and the write is slow
# enough to let a second request pass the duplicate guard. Tunable so the
# harness can dial the reproduction rate up or down.
RACE_CHANCE = float(os.environ.get("RACE_CHANCE", "0.03"))


class Ledger:
    """Append-only in-memory ledger of successful charges."""

    def __init__(self):
        self._rows = []
        self._lock = threading.Lock()

    def has(self, order_id):
        # NOTE: reads without taking the lock, on purpose.
        return any(row["order_id"] == order_id for row in self._rows)

    def append(self, row):
        with self._lock:
            self._rows.append(row)

    def count(self, order_id):
        return sum(1 for row in self._rows if row["order_id"] == order_id)

    def rows(self):
        return list(self._rows)


def charge(order_id, amount, ledger, log_path=LOG_PATH):
    """Charge once per order_id.

    Returns "charged" on success, "skipped" when the order was already charged.
    """
    if ledger.has(order_id):          # check
        _log(log_path, {"event": "duplicate_blocked", "order_id": order_id, "amount": amount})
        return "skipped"
    if random.random() < RACE_CHANCE:
        # Simulated slow external fraud-check call between the read and the
        # write. This is the window in which a second request slips through.
        time.sleep(0.002)
    ledger.append({                   # act
        "order_id": order_id,
        "amount": amount,
        "charged_at": round(time.time(), 6),
    })
    _log(log_path, {"event": "charged", "order_id": order_id, "amount": amount})
    return "charged"


def _log(path, payload):
    payload["ts"] = round(time.time(), 6)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "a", encoding="utf-8") as fh:
        fh.write(json.dumps(payload, sort_keys=True) + "\n")
