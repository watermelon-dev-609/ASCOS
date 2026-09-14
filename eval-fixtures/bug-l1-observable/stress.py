"""Stress harness: many rounds of concurrent charges on the same order_id.

Usage:
    python stress.py [rounds] [threads]

Appends structured events to logs/payments.log and prints a summary.
The duplicate rate is intentionally low per round - this is what makes the
bug hard to pin down with a single test.
"""

import os
import sys
import threading
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from payments import Ledger, charge

HERE = os.path.dirname(os.path.abspath(__file__))
LOG_PATH = os.path.join(HERE, "logs", "payments.log")


def run_round(order_id, threads, barrier):
    ledger = Ledger()
    results = []

    def worker():
        barrier.wait()
        results.append(charge(order_id, 49.9, ledger))

    pool = [threading.Thread(target=worker) for _ in range(threads)]
    for t in pool:
        t.start()
    for t in pool:
        t.join()

    return ledger.count(order_id)


def main():
    rounds = int(sys.argv[1]) if len(sys.argv) > 1 else 200
    threads = int(sys.argv[2]) if len(sys.argv) > 2 else 8

    os.makedirs(os.path.dirname(LOG_PATH), exist_ok=True)
    duplicates = 0
    for i in range(rounds):
        barrier = threading.Barrier(threads)
        order_id = "ORD-%05d" % i
        if run_round(order_id, threads, barrier) > 1:
            duplicates += 1

    print("rounds=%d threads=%d duplicate_rounds=%d rate=%.1f%%"
          % (rounds, threads, duplicates, 100.0 * duplicates / rounds))
    print("log: %s" % LOG_PATH)


if __name__ == "__main__":
    main()
