#!/usr/bin/env python3
"""ASCOS eval harness.

validate_skill.py answers "is the package structurally sound?". This answers
"does the package actually change behaviour?" — by making the measurement
repeatable instead of a matter of taste.

Subcommands
    check    lint the eval corpus (and any ingested records)
    prompt   export runnable prompts
    ingest   validate and store run records (JSONL in, one file out)
    report   aggregate stored records into evals/results/report.md

What this deliberately does NOT do
    - no live mode, no network, no API calls. A eval that silently degrades to
      "the model said it's fine" is worse than no eval.
    - no scoring of its own. Verdicts are produced by whatever ran the case and
      are ingested as data; this tool only checks, stores and aggregates them.

Run records (JSONL, one object per line):
    {"case": "E01", "variant": "with_skill", "run": 1, "verdict": "pass",
     "seconds": 41.2, "tokens": 9130, "transcript": "path/or/url", "note": ""}

Must-not-fire trigger cases add `misfire_shape` (one of MISFIRE_SHAPES).
It is required there: "did it misfire" without "what shape was it" cannot
tell a one-off slip from a rule that is missing its boundary.
"""

from __future__ import annotations

import argparse
import json
import os
import sys

from eval_common import (  # noqa: E402  (script lives next to eval_common)
    EVALS_DIR, RESULTS_DIR, ROOT, Report, load_cases, read_text, rel,
)

RECORDS_FILE = os.path.join(RESULTS_DIR, "records.jsonl")
REPORT_FILE = os.path.join(RESULTS_DIR, "report.md")

BEHAVIOUR_GROUPS = ("small", "medium", "large", "bugs", "adversarial")
ALL_GROUPS = BEHAVIOUR_GROUPS + ("trigger",)
SKILLS = ("requirements", "architecture", "implementation",
          "debugging", "code-review", "verification")
VARIANTS = ("with_skill", "without_skill")
BEHAVIOUR_VERDICTS = ("pass", "fail")
TRIGGER_VERDICTS = ("fire", "not_fire")

# Shape of a must-not-fire misfire. Recording *what kind* of overreach happened
# matters more than the count: two different shapes point at two different
# rules, while the same shape across different cases points at one missing
# boundary. See evals/runs/2026-09-14-round3-triggers.md.
MISFIRE_SHAPES = ("none", "risk-tail", "router-language", "PRD-overreach",
                  "DoD-overreach", "subskill-name-leak")

MIN_FIRE = 10  # the corpus must keep 10 must-fire / 10 must-not-fire or it
MIN_NOT_FIRE = 10  # stops being able to detect either kind of trigger failure


# --- corpus ---------------------------------------------------------------

def _section(body: str, heading: str) -> str:
    """Text of a `## heading` section, up to the next heading of any level."""
    start = body.find("## %s" % heading)
    if start == -1:
        return ""
    rest = body[start + len(heading) + 3:]
    stop = rest.find("\n## ")
    return (rest[:stop] if stop != -1 else rest).strip()


def case_prompt(case: dict) -> str:
    """The exact text a runner sends to the agent.

    `>` blockquotes inside the 输入 section are grader notes — which fixture to
    use, how to set the environment up. Sending them would leak the grading
    setup into the prompt, the same way a fixture README once leaked the root
    cause and turned an L0 case into dictation.
    """
    body = _section(case["_body"], "输入")
    lines = [l for l in body.splitlines() if not l.lstrip().startswith("> ")]
    return "\n".join(lines).strip()


def corpus_check(report: Report, cases: list[dict]) -> None:
    seen: dict[str, str] = {}
    counts = {"fire": 0, "not_fire": 0, "behaviour": 0}

    for case in cases:
        tag = case.get("id") or case["_rel"]
        where = case["_rel"]

        report.check(bool(case.get("id")), "%s declares an id" % where)
        if not case.get("id"):
            continue
        cid = case["id"]
        report.check(cid not in seen, "id %s is unique" % cid,
                     "also declared by %s" % seen.get(cid, "?"))
        seen[cid] = where

        group = case.get("group", "")
        report.check(group in ALL_GROUPS, "%s has a known group" % cid,
                     "got %r" % group)

        expect = case.get("expect", "")
        report.check(expect in ("pass", "fire", "not_fire"),
                     "%s declares a valid expect" % cid, "got %r" % expect)

        if group == "trigger":
            if expect == "fire":
                counts["fire"] += 1
            elif expect == "not_fire":
                counts["not_fire"] += 1
            evidence = case.get("evidence")
            report.check(isinstance(evidence, list) and len(evidence) > 0,
                         "%s lists evidence anchors" % cid,
                         "a trigger case with no observable anchors cannot be graded")
            if expect == "fire":
                report.check(bool(case.get("route")),
                             "%s declares the route it should take" % cid)
            else:
                report.check(bool(case.get("near_miss")),
                             "%s declares why it is a near miss" % cid)
        else:
            counts["behaviour"] += 1
            report.check(bool(case.get("route")), "%s declares expected route" % cid)
            for skill in (case.get("route") or "").split(" → "):
                if skill.strip():
                    report.check(skill.strip() in SKILLS,
                                 "%s route names a real skill" % cid, "got %r" % skill)
            report.check("判定" in case["_body"], "%s declares pass/fail criteria" % cid)

        report.check(bool(case_prompt(case)), "%s has an extractable input" % cid,
                     "no `## 输入` section — prompt export would emit nothing")

    report.check(counts["fire"] >= MIN_FIRE,
                 "corpus has at least %d must-fire trigger cases" % MIN_FIRE,
                 "%d found" % counts["fire"])
    report.check(counts["not_fire"] >= MIN_NOT_FIRE,
                 "corpus has at least %d must-not-fire trigger cases" % MIN_NOT_FIRE,
                 "%d found" % counts["not_fire"])
    report.check(counts["behaviour"] >= 20,
                 "corpus has at least 20 behaviour cases",
                 "%d found" % counts["behaviour"], level="warn")


def records_check(report: Report, cases: list[dict]) -> None:
    known = {c["id"] for c in cases if c.get("id")}
    for i, rec in enumerate(load_records(), start=1):
        label = "record #%d" % i
        report.check(rec.get("case") in known, "%s references a known case" % label,
                     "got %r" % rec.get("case"))
        report.check(rec.get("variant") in VARIANTS, "%s declares a variant" % label,
                     "got %r" % rec.get("variant"))
        run = rec.get("run")
        report.check(isinstance(run, int) and run >= 1, "%s has run >= 1" % label,
                     "got %r" % run)
        verdict = rec.get("verdict")
        expect = next((c.get("expect") for c in cases if c.get("id") == rec.get("case")), None)
        if expect in ("fire", "not_fire"):
            report.check(verdict in TRIGGER_VERDICTS, "%s verdict matches its case type" % label,
                         "trigger case expects fire/not_fire, got %r" % verdict)
        else:
            report.check(verdict in BEHAVIOUR_VERDICTS, "%s verdict matches its case type" % label,
                         "behaviour case expects pass/fail, got %r" % verdict)

        shape = rec.get("misfire_shape")
        if expect == "not_fire":
            report.check(shape in MISFIRE_SHAPES,
                         "%s records a misfire_shape" % label,
                         "must-not-fire records need one of %s, got %r"
                         % (MISFIRE_SHAPES, shape))
            if shape in MISFIRE_SHAPES:
                consistent = ((verdict == "not_fire" and shape == "none")
                              or (verdict == "fire" and shape != "none"))
                report.check(consistent, "%s shape agrees with its verdict" % label,
                             "verdict=%r but shape=%r" % (verdict, shape))
        elif shape is not None:
            report.check(shape == "none",
                         "%s has no shape to record" % label,
                         "only must-not-fire cases carry a misfire_shape, got %r" % shape)


# --- records --------------------------------------------------------------

def load_records() -> list[dict]:
    if not os.path.isfile(RECORDS_FILE):
        return []
    out = []
    for line in read_text(RECORDS_FILE).splitlines():
        line = line.strip()
        if line:
            out.append(json.loads(line))
    return out


def write_records(records: list[dict]) -> None:
    os.makedirs(RESULTS_DIR, exist_ok=True)
    with open(RECORDS_FILE, "w", encoding="utf-8", newline="\n") as fh:
        for rec in records:
            fh.write(json.dumps(rec, ensure_ascii=False, sort_keys=True) + "\n")


# --- statistics -----------------------------------------------------------

def _comb(n: int, k: int) -> int:
    """n choose k, integer-exact."""
    if k > n:
        return 0
    out = 1
    for i in range(1, min(k, n - k) + 1):
        out = out * (n - i + 1) // i
    return out


def pass_at_k(n: int, hits: int, k: int) -> float | None:
    """Fraction of k-sample draws that contain at least one pass.

    None when there are fewer runs than k — reporting a number there would be
    a guess dressed up as a measurement.
    """
    if n < k:
        return None
    if n - hits < k:
        return 1.0
    return 1.0 - _comb(n - hits, k) / _comb(n, k)


def _fmt(value: float | None) -> str:
    return "—" if value is None else "%.2f" % value


def _mean(values: list[float]) -> float | None:
    return sum(values) / len(values) if values else None


# --- subcommands ----------------------------------------------------------

def cmd_check(args) -> int:
    report = Report()
    cases = load_cases()
    report.check(bool(cases), "eval corpus is not empty")
    corpus_check(report, cases)
    records_check(report, cases)

    print("ASCOS eval harness — %d checks run (%d cases, %d records)"
          % (len(report.checks), len(cases), len(load_records())))
    for level, msg in report.findings:
        print("  %s %s" % ("✗" if level == "error" else "!", msg))
    if not report.findings:
        print("\n✓ Eval corpus is valid")
    return 1 if report.errors or (args.strict and report.warnings) else 0


def select(cases: list[dict], args) -> list[dict]:
    if args.id:
        return [c for c in cases if c.get("id") == args.id]
    if args.group:
        return [c for c in cases if c.get("group") == args.group]
    return cases


def cmd_prompt(args) -> int:
    cases = select(load_cases(), args)
    if not cases:
        print("no case matched", file=sys.stderr)
        return 1
    out = []
    for case in cases:
        prompt = case_prompt(case)
        if args.format == "jsonl":
            out.append(json.dumps({
                "id": case.get("id"), "group": case.get("group"),
                "expect": case.get("expect"), "route": case.get("route", ""),
                "variant": args.variant, "prompt": prompt,
            }, ensure_ascii=False))
        else:
            head = "# %s · %s · expect=%s" % (case.get("id"), case.get("group"),
                                              case.get("expect"))
            if case.get("route"):
                head += " · route=%s" % case["route"]
            note = "variant=%s — %s" % (
                args.variant,
                "ASCOS loaded in the session; send the text below as-is"
                if args.variant == "with_skill"
                else "no ASCOS in the session; send the text below as-is")
            out.append("%s\n> %s\n\n%s" % (head, note, prompt))
    print("\n\n".join(out))
    return 0


def cmd_ingest(args) -> int:
    incoming = []
    for line in read_text(args.file).splitlines():
        line = line.strip()
        if line:
            incoming.append(json.loads(line))
    if not incoming:
        print("nothing to ingest", file=sys.stderr)
        return 1

    cases = load_cases()
    known = {c["id"]: c for c in cases if c.get("id")}
    existing = load_records()
    index = {(r.get("case"), r.get("variant"), r.get("run")): i
             for i, r in enumerate(existing)}

    errors = []
    for i, rec in enumerate(incoming, start=1):
        if rec.get("case") not in known:
            errors.append("#%d: unknown case %r" % (i, rec.get("case")))
            continue
        if rec.get("variant") not in VARIANTS:
            errors.append("#%d: variant must be one of %s" % (i, VARIANTS))
        if not isinstance(rec.get("run"), int) or rec.get("run") < 1:
            errors.append("#%d: run must be an int >= 1" % i)
        expect = known[rec["case"]].get("expect")
        allowed = TRIGGER_VERDICTS if expect in TRIGGER_VERDICTS else BEHAVIOUR_VERDICTS
        if rec.get("verdict") not in allowed:
            errors.append("#%d: verdict must be one of %s for this case" % (i, allowed))
        if expect == "not_fire":
            shape = rec.get("misfire_shape")
            if shape not in MISFIRE_SHAPES:
                errors.append("#%d: misfire_shape must be one of %s for a "
                              "must-not-fire case" % (i, MISFIRE_SHAPES))
            elif ((rec.get("verdict") == "not_fire" and shape != "none")
                  or (rec.get("verdict") == "fire" and shape == "none")):
                errors.append("#%d: verdict=%r and misfire_shape=%r contradict "
                              "each other" % (i, rec.get("verdict"), shape))
        elif rec.get("misfire_shape", "none") != "none":
            errors.append("#%d: only must-not-fire cases carry a misfire_shape, "
                          "got %r" % (i, rec.get("misfire_shape")))
        key = (rec.get("case"), rec.get("variant"), rec.get("run"))
        if key in index and not args.replace:
            errors.append("#%d: %s run %s already recorded (use --replace)"
                          % (i, rec.get("case"), rec.get("run")))
    if errors:
        for err in errors:
            print("✗ %s" % err, file=sys.stderr)
        return 1

    for rec in incoming:
        key = (rec.get("case"), rec.get("variant"), rec.get("run"))
        if key in index:
            existing[index[key]] = rec
        else:
            existing.append(rec)
    write_records(existing)
    print("ingested %d record(s) → %s (%d total)"
          % (len(incoming), rel(RECORDS_FILE), len(existing)))
    return 0


def _misfire_section(cases: dict[str, dict], by_case: dict) -> list[str]:
    """Aggregate must-not-fire records by shape.

    Deliberately reports counts only. Whether a count crosses the fix
    threshold is a decision registered in the run protocol before the run,
    not something the aggregator gets to decide after seeing the numbers.
    """
    rows: list[tuple[str, str, int, int, list[str]]] = []
    # Keyed by variant: "the same shape across cases" only counts as one
    # systemic problem within an arm. Pooling arms would let a without-arm
    # slip look like evidence about the with-arm rules.
    tally: dict[tuple[str, str], list[str]] = {}
    for cid in sorted(by_case):
        if cases.get(cid, {}).get("expect") != "not_fire":
            continue
        for variant in VARIANTS:
            runs = by_case[cid].get(variant, [])
            if not runs:
                continue
            fires = [r for r in runs if r.get("verdict") == "fire"]
            shapes = [r.get("misfire_shape", "?") for r in runs]
            for shape in shapes:
                if shape != "none":
                    tally.setdefault((variant, shape), []).append(cid)
            rows.append((cid, variant, len(runs), len(fires), shapes))

    if not rows:
        return []

    out = ["## Misfire shapes (must-not-fire cases)", "",
           "Counts only — the fix threshold is registered in the run protocol, "
           "not derived here.", "",
           "| case | variant | runs | fires | shapes |",
           "|---|:--:|:--:|:--:|---|"]
    for cid, variant, n, fires, shapes in rows:
        out.append("| %s | %s | %d | %d | %s |"
                   % (cid, variant, n, fires, ", ".join(shapes)))
    out += [""]
    if tally:
        # The cross-case criterion asks *which* cases share a shape, so the
        # tally has to name them — a bare count forces a manual lookup.
        out += ["| variant | shape | occurrences | cases |", "|---|:--:|:--:|---|"]
        for (variant, shape), cids in sorted(tally.items(),
                                             key=lambda kv: (-len(kv[1]), kv[0])):
            out.append("| %s | %s | %d | %s |"
                       % (variant, shape, len(cids), ", ".join(sorted(set(cids)))))
    else:
        out += ["No misfire recorded in this batch."]
    out += [""]
    return out


def cmd_report(args) -> int:
    cases = {c["id"]: c for c in load_cases() if c.get("id")}
    records = load_records()
    if not records:
        print("no records yet — run `ingest` first")
        return 0

    ks = sorted({int(k) for k in args.k if int(k) >= 1})
    by_case: dict[str, dict[str, list[dict]]] = {}
    for rec in records:
        by_case.setdefault(rec["case"], {}).setdefault(rec["variant"], []).append(rec)

    lines = ["# ASCOS eval report", "",
             "Generated from `%s` (%d records). Verdicts come from whatever ran "
             "each case; this file only aggregates them."
             % (rel(RECORDS_FILE), len(records)), ""]

    overall: dict[str, dict] = {}
    for cid in sorted(by_case):
        case = cases.get(cid, {})
        expect = case.get("expect", "pass")
        lines.append("## %s · %s · expect=%s" % (cid, case.get("group", "?"), expect))
        lines.append("")
        cols = (["variant", "runs", "hits"]
                + ["pass@%d" % k for k in ks]
                + ["mean s", "mean tokens"])
        lines.append("| " + " | ".join(cols) + " |")
        lines.append("|" + "|".join(":--:" for _ in cols) + "|")
        for variant in VARIANTS:
            runs = by_case[cid].get(variant, [])
            if not runs:
                continue
            hits = sum(1 for r in runs if r.get("verdict") == expect)
            n = len(runs)
            row = [variant, str(n), "%d/%d" % (hits, n)]
            row += [_fmt(pass_at_k(n, hits, k)) for k in ks]
            row.append(_fmt(_mean([r["seconds"] for r in runs if "seconds" in r])))
            row.append(_fmt(_mean([r["tokens"] for r in runs if "tokens" in r])))
            lines.append("| " + " | ".join(row) + " |")
            agg = overall.setdefault(variant, {"n": 0, "hits": 0, "sec": [], "tok": []})
            agg["n"] += n
            agg["hits"] += hits
            agg["sec"] += [r["seconds"] for r in runs if "seconds" in r]
            agg["tok"] += [r["tokens"] for r in runs if "tokens" in r]
        lines.append("")

    misfire = _misfire_section(cases, by_case)
    if misfire:
        lines += misfire

    lines.append("## Totals")
    lines.append("")
    lines.append("| variant | records | hit rate | mean s | mean tokens |")
    lines.append("|---|:--:|:--:|:--:|:--:|")
    for variant in VARIANTS:
        agg = overall.get(variant)
        if not agg:
            continue
        lines.append("| %s | %d | %.0f%% | %s | %s |" % (
            variant, agg["n"], 100.0 * agg["hits"] / agg["n"],
            _fmt(_mean(agg["sec"])), _fmt(_mean(agg["tok"]))))
    with_skill = overall.get("with_skill")
    without = overall.get("without_skill")
    if with_skill and without:
        delta = (100.0 * with_skill["hits"] / with_skill["n"]
                 - 100.0 * without["hits"] / without["n"])
        lines += ["", "**Behaviour delta (with_skill − without_skill): %+.0f pp**" % delta, "",
                  "> On must-fire cases this delta is largely true by construction: "
                  "an arm with no ASCOS in it cannot fire. It shows the two arms were "
                  "actually isolated, not that ASCOS made the answers better. The "
                  "informative half is how often the with arm fires on must-not-fire "
                  "cases — see the misfire table above.", ""]
    else:
        lines += ["", "_Behaviour delta needs both variants recorded._", ""]

    lines.append("pass@k is blank (—) when a case has fewer runs than k: an "
                 "aggregate over fewer samples than k is not a measurement.")
    lines.append("")

    os.makedirs(RESULTS_DIR, exist_ok=True)
    with open(REPORT_FILE, "w", encoding="utf-8", newline="\n") as fh:
        fh.write("\n".join(lines))

    print("\n".join(lines))
    print("\nwrote %s" % rel(REPORT_FILE))
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = parser.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("check", help="lint the eval corpus")
    p.add_argument("--strict", action="store_true", help="warnings also fail")
    p.set_defaults(func=cmd_check)

    p = sub.add_parser("prompt", help="export runnable prompts")
    p.add_argument("--id", help="a single case id, e.g. E14")
    p.add_argument("--group", choices=ALL_GROUPS, help="every case in a group")
    p.add_argument("--variant", choices=VARIANTS, default="with_skill")
    p.add_argument("--format", choices=("plain", "jsonl"), default="plain")
    p.set_defaults(func=cmd_prompt)

    p = sub.add_parser("ingest", help="store run records from a JSONL file")
    p.add_argument("--file", required=True, help="path to a JSONL run file")
    p.add_argument("--replace", action="store_true",
                   help="overwrite an existing (case, variant, run) triple")
    p.set_defaults(func=cmd_ingest)

    p = sub.add_parser("report", help="aggregate records into a report")
    p.add_argument("--k", type=int, nargs="+", default=[1, 3],
                   help="values of k for pass@k (default: 1 3)")
    p.set_defaults(func=cmd_report)

    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
