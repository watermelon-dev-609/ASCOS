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
        ev = cost_runner.parse_events(
            open(os.path.join(D, "events", label + ".jsonl"),
                 encoding="utf-8").read())
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

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
