"""Report what a cost batch actually did, as opposed to what it cost.

Token counts say how expensive a run was, not whether it accomplished
anything. This is the check that caught the pilot: four runs, four permission
denials, zero files changed — a batch that would have measured planning tokens
and called it delivery.

Usage: python scripts/inspect_cost_batch.py [--dir <batch>] [--fixture <dir>]
"""
import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import cost_runner  # noqa: E402
from eval_common import ROOT  # noqa: E402

INTERESTING = ("Write", "Edit", "WebSearch", "PowerShell", "Bash", "Skill")


def tool_calls(ev, names):
    out = []
    for e in ev:
        m = e.get("message")
        if not isinstance(m, dict):
            continue
        c = m.get("content")
        if not isinstance(c, list):
            continue
        for b in c:
            if isinstance(b, dict) and b.get("type") == "tool_use" \
                    and b.get("name") in names:
                out.append(b)
    return out


def results(ev):
    out = []
    for e in ev:
        m = e.get("message")
        if not isinstance(m, dict):
            continue
        c = m.get("content")
        if isinstance(c, list):
            for b in c:
                if isinstance(b, dict) and b.get("type") == "tool_result":
                    out.append(b)
    return out


def changed_files(ws, fixture):
    """Files differing from the fixture, ignoring the injected skill dir."""
    changed, added = [], []
    for root, dirs, files in os.walk(ws):
        dirs[:] = [d for d in dirs if d != ".claude"]
        for f in files:
            full = os.path.join(root, f)
            rel = os.path.relpath(full, ws)
            src = os.path.join(fixture, rel)
            if not os.path.exists(src):
                added.append(rel)
            else:
                with open(full, encoding="utf-8", errors="replace") as fh:
                    now = fh.read()
                with open(src, encoding="utf-8", errors="replace") as fh:
                    was = fh.read()
                if now != was:
                    changed.append(rel)
    return sorted(changed), sorted(added)


DENIAL_MARKS = ("haven't granted", "denied", "statically validated",
                "requires manual approval", "permission")


def classify_failure(result: dict) -> str:
    """Split `is_error` results into refused and merely-failed.

    Conflating the two is what made the r5 fix look like it had failed: a
    command that ran and exited 1 is ordinary (sometimes it is the whole point
    of a verification step), while a command that never ran because permission
    was refused is harness friction. Friction is the thing that biased pilot r4
    14-to-2 against the arm under test, so it gets its own column.
    """
    low = json.dumps(result, ensure_ascii=False).lower()
    return "denied" if any(m in low for m in DENIAL_MARKS) else "failed"


def events_for(D: str, label: str) -> list[dict]:
    """One place that opens an event stream, so it can be the one place that
    closes it. Reading these without a `with` leaked a handle per label per
    call, which a test run turns into a wall of ResourceWarnings."""
    with open(os.path.join(D, "events", label + ".jsonl"),
              encoding="utf-8") as fh:
        return cost_runner.parse_events(fh.read())


def failure_census(D: str, labels: list[str]) -> dict:
    """Refused vs failed, per arm. Asymmetry here is a validity problem."""
    census = {}
    for label in labels:
        arm = "with" if "-with_skill" in label else "without"
        ev = events_for(D, label)
        bucket = census.setdefault(arm, {"denied": 0, "failed": 0})
        for r in results(ev):
            if r.get("is_error"):
                bucket[classify_failure(r)] += 1
    return census


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--dir", default=os.path.join(
        ROOT, "evals", "cost", "results", "raw", "pilot-2026-09-18"))
    ap.add_argument("--fixture", default=os.path.join(ROOT, "eval-fixtures",
                                                      "cost-app"))
    args = ap.parse_args()
    D, FIXTURE = args.dir, args.fixture

    labels = sorted(os.path.splitext(f)[0]
                    for f in os.listdir(os.path.join(D, "events"))
                    if f.endswith(".jsonl"))
    for label in labels:
        ev = events_for(D, label)
        models = {e["message"].get("model")
                  for e in ev
                  if isinstance(e.get("message"), dict)
                  and e["message"].get("model")}
        ws = os.path.join(D, "ws", label)
        ch, ad = changed_files(ws, FIXTURE)
        print("=== %s" % label)
        print("    model       : %s" % sorted(models))
        print("    changed     : %s" % (ch or "none"))
        print("    added       : %s" % (ad or "none"))
        for b in tool_calls(ev, INTERESTING):
            inp = b.get("input") or {}
            print("    TOOL %-10s %s" % (b.get("name"),
                                         json.dumps(inp, ensure_ascii=False)[:150]))
        for r in results(ev):
            if r.get("is_error"):
                print("    ERROR RESULT: %s" % str(r.get("content"))[:150])
        for e in ev:
            if e.get("type") == "system" and e.get("subtype") == "permission_denied":
                print("    DENIED %s | %s" % (e.get("tool_name"),
                                              str(e.get("message"))[:110]))
        print()

    census = failure_census(D, labels)
    print("=== 失败与拒绝（按臂）")
    print("    %-10s %8s %8s" % ("arm", "denied", "failed"))
    for arm in ("with", "without"):
        b = census.get(arm, {"denied": 0, "failed": 0})
        print("    %-10s %8d %8d" % (arm, b["denied"], b["failed"]))
    denied = {a: census.get(a, {}).get("denied", 0) for a in ("with", "without")}
    if denied["with"] != denied["without"]:
        print("    !! 拒绝不对称：偏倚会压在拒绝更多的那一臂上，"
              "该批次的成本与 verified 判分都不可直接采信")
    else:
        print("    拒绝对称（含同为 0）。")
    print()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
