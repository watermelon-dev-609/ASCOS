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

# Stage 2 (cost) keeps its own record file. A cost round ingests ~72 records
# under a different field contract; pooling them into the Stage 1 file would
# move the trigger hit rates every time a cost round was ingested.
COST_DIR = os.path.join(EVALS_DIR, "cost")
COST_RESULTS_DIR = os.path.join(COST_DIR, "results")
COST_RECORDS_FILE = os.path.join(COST_RESULTS_DIR, "cost-records.jsonl")
COST_REPORT_FILE = os.path.join(COST_RESULTS_DIR, "cost-report.md")

BEHAVIOUR_GROUPS = ("small", "medium", "large", "bugs", "adversarial")
ALL_GROUPS = BEHAVIOUR_GROUPS + ("trigger",)
SKILLS = ("requirements", "architecture", "implementation",
          "debugging", "code-review", "verification")
# `with_skill_candidate` is the v1.3 arm in the Stage 2 A/B/C regression. It is
# declared from the start so the third arm does not change the schema halfway
# through the experiment.
VARIANTS = ("with_skill", "without_skill", "with_skill_candidate")
# A run that could not measure what the case measures — e.g. an unrelated
# connector in the harness hijacked the request before ASCOS could see it.
# Excluded from every denominator: counting it as a miss would blame the
# skill for the environment, and counting it as a hit would be a lie.
INVALID = "invalid"

BEHAVIOUR_VERDICTS = ("pass", "fail", INVALID)
TRIGGER_VERDICTS = ("fire", "not_fire", INVALID)

# Shape of a must-not-fire misfire. Recording *what kind* of overreach happened
# matters more than the count: two different shapes point at two different
# rules, while the same shape across different cases points at one missing
# boundary. See evals/runs/2026-09-14-round3-triggers.md.
MISFIRE_SHAPES = ("none", "risk-tail", "router-language", "PRD-overreach",
                  "DoD-overreach", "subskill-name-leak")

# Non-misfire observation tags. A must-not-fire case can mention ASCOS while
# correctly declining it; that is the routing decision being visible, not the
# skill activating. Keeping it out of misfire_shape stops "explained why I
# won't trigger" from scoring worse than saying nothing.
OBSERVATIONS = ("negative-routing",)

# Did this run actually load SKILL.md? Reported by the run itself, and it is a
# *behaviour*, not an output shape — so it stays usable when the activation
# rubric changes. Rubric revisions keep making "did it fire" harder to compare
# across rounds; "did it open the file" does not move.
LOADED = ("yes", "no")

MIN_FIRE = 10  # the corpus must keep 10 must-fire / 10 must-not-fire or it
MIN_NOT_FIRE = 10  # stops being able to detect either kind of trigger failure

# --- Stage 2: cost & quality ---------------------------------------------
# Cost is measured, never modelled: every field below is something the run
# reports, and the aggregator only ever divides sums it was given.
COST_BUCKETS = ("small", "medium", "large")
COST_NUMERIC = ("input_tokens", "output_tokens", "total_tokens",
                "cache_read_tokens", "num_turns", "seconds", "tool_calls")
DEFECT_KEYS = ("bugs", "missed_edges", "security", "unnecessary_changes")

# Weights of the derived quality index. Registered in evals/cost/README.md
# BEFORE the first cost run — changing them re-bases every round, so they are a
# constant here rather than a flag. Defect-based only: completion is reported
# separately so a failing run is not penalised twice.
QUALITY_MAX = 100
QUALITY_WEIGHTS = {"bugs": 15, "missed_edges": 10, "security": 25,
                   "unnecessary_changes": 8}
QUALITY_FLAGS = {"over_engineering": 15, "not_verified": 20, "tests_fail": 20}


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

        if verdict == INVALID:
            # An unmeasurable run is only honest if it says why, otherwise
            # "invalid" becomes a drawer to sweep inconvenient results into.
            report.check(bool(rec.get("note")),
                         "%s explains why it is invalid" % label,
                         "an invalid run with no reason cannot be audited")
            shape = rec.get("misfire_shape")
            report.check(shape in (None, "none"),
                         "%s carries no misfire_shape" % label,
                         "nothing was observed, so no shape can be recorded, got %r"
                         % shape)
        else:
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

        obs = rec.get("observation")
        if obs is not None:
            report.check(obs in OBSERVATIONS, "%s uses a known observation tag" % label,
                         "one of %s, got %r" % (OBSERVATIONS, obs))

        loaded = rec.get("loaded")
        if loaded is not None:
            report.check(loaded in LOADED, "%s uses a known loaded value" % label,
                         "one of %s, got %r" % (LOADED, loaded))


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


# --- cost records (Stage 2) ----------------------------------------------

def load_cost_records() -> list[dict]:
    if not os.path.isfile(COST_RECORDS_FILE):
        return []
    out = []
    for line in read_text(COST_RECORDS_FILE).splitlines():
        line = line.strip()
        if line:
            out.append(json.loads(line))
    return out


def write_cost_records(records: list[dict]) -> None:
    os.makedirs(COST_RESULTS_DIR, exist_ok=True)
    with open(COST_RECORDS_FILE, "w", encoding="utf-8", newline="\n") as fh:
        for rec in records:
            fh.write(json.dumps(rec, ensure_ascii=False, sort_keys=True) + "\n")


def quality_index(rec: dict) -> int:
    """Derived composite over observed defects.

    Deliberately excludes the verdict: completion is reported beside this, and
    counting a failing run twice (once as fail, once as defects) would make the
    index move for reasons nobody can see.
    """
    score = QUALITY_MAX
    defects = rec.get("defects") or {}
    for key, weight in QUALITY_WEIGHTS.items():
        score -= weight * int(defects.get(key, 0) or 0)
    if rec.get("over_engineering"):
        score -= QUALITY_FLAGS["over_engineering"]
    if rec.get("verified") is False:
        score -= QUALITY_FLAGS["not_verified"]
    if rec.get("tests_pass") is False:
        score -= QUALITY_FLAGS["tests_fail"]
    return max(0, score)


def load_manifest(path: str | None = None) -> dict[str, dict]:
    """Bucket assignment for the cost batch; falls back to each case's group."""
    path = path or os.path.join(COST_DIR, "manifest.json")
    if not os.path.isfile(path):
        return {}
    with open(path, encoding="utf-8") as fh:
        data = json.load(fh)
    return {e["id"]: e for e in data.get("cases", []) if e.get("id")}


def cost_bucket(case_id: str, cases: dict, manifest: dict) -> str | None:
    """Size bucket for a case, or None when it is outside the cost batch."""
    entry = manifest.get(case_id or "")
    if entry and entry.get("bucket"):
        return entry["bucket"]
    group = cases.get(case_id, {}).get("group")
    return group if group in COST_BUCKETS else None


def cost_errors(rec: dict) -> list[str]:
    """Field contract for a cost record. Empty list means well formed."""
    errs = []
    for field in COST_NUMERIC:
        value = rec.get(field)
        if value is None:
            continue
        if isinstance(value, bool) or not isinstance(value, (int, float)) or value < 0:
            errs.append("%s must be a non-negative number, got %r" % (field, value))
    model = rec.get("model")
    if model is not None and not isinstance(model, str):
        errs.append("model must be a string, got %r" % model)
    for field in ("skills_loaded", "references_loaded"):
        value = rec.get(field)
        if value is not None and not (isinstance(value, list)
                                      and all(isinstance(v, str) for v in value)):
            errs.append("%s must be a list of strings, got %r" % (field, value))
    defects = rec.get("defects")
    if defects is not None:
        if not isinstance(defects, dict):
            errs.append("defects must be an object, got %r" % defects)
        else:
            for key, value in defects.items():
                if key not in DEFECT_KEYS:
                    errs.append("unknown defect key %r (allowed: %s)"
                                % (key, ", ".join(DEFECT_KEYS)))
                elif isinstance(value, bool) or not isinstance(value, int) or value < 0:
                    errs.append("defects.%s must be a non-negative int, got %r"
                                % (key, value))
    for field in ("over_engineering", "verified", "tests_pass"):
        value = rec.get(field)
        if value is not None and not isinstance(value, bool):
            errs.append("%s must be a boolean, got %r" % (field, value))
    stages = rec.get("stages")
    if stages is not None:
        if not isinstance(stages, list):
            errs.append("stages must be a list, got %r" % stages)
        else:
            for stage in stages:
                if not (isinstance(stage, dict) and stage.get("stage")
                        and isinstance(stage.get("tokens"), (int, float))
                        and not isinstance(stage.get("tokens"), bool)):
                    errs.append("each stage needs {stage, tokens}, got %r" % stage)
    return errs


def cost_records_check(report: Report, cases: list[dict]) -> None:
    by_id = {c["id"]: c for c in cases if c.get("id")}
    manifest = load_manifest()
    records = load_cost_records()
    seen: set[str] = set()
    for i, rec in enumerate(records, start=1):
        label = "cost record #%d" % i
        report.check(rec.get("case") in by_id, "%s references a known case" % label,
                     "got %r" % rec.get("case"))
        report.check(rec.get("variant") in VARIANTS, "%s declares a variant" % label,
                     "got %r" % rec.get("variant"))
        run = rec.get("run")
        report.check(isinstance(run, int) and run >= 1, "%s has run >= 1" % label,
                     "got %r" % run)
        for err in cost_errors(rec):
            report.check(False, "%s is well formed" % label, err)
        bucket = cost_bucket(rec.get("case"), by_id, manifest)
        if bucket:
            seen.add(bucket)
    # Coverage only carries information once the batch has started. Before the
    # first record exists an empty bucket means "not begun", not "missing" —
    # and CI runs this with --strict, so warning there would turn an unstarted
    # measurement into a red build.
    if not records:
        return
    for bucket in COST_BUCKETS:
        report.check(bucket in seen, "cost batch covers the %s bucket" % bucket,
                     "no cost record lands in %s yet" % bucket, level="warn")


def _bucket_stats(runs: list[dict]) -> dict:
    """Aggregate one bucket × variant cell. Invalid runs never reach a mean."""
    measured = [r for r in runs if r.get("verdict") != INVALID]
    stats: dict = {"n": len(measured), "invalid": len(runs) - len(measured),
                   "hits": 0}
    if not measured:
        return stats
    stats["hits"] = sum(1 for r in measured if r.get("verdict") == "pass")
    for key, field in (("in", "input_tokens"), ("out", "output_tokens"),
                       ("total", "total_tokens"), ("sec", "seconds"),
                       ("tools", "tool_calls")):
        values = [r[field] for r in measured if r.get(field) is not None]
        stats[key] = _mean(values)
    stats["qi"] = _mean([quality_index(r) for r in measured])
    ref_counts = [len(r.get("references_loaded") or [])
                  for r in measured if r.get("references_loaded") is not None]
    stats["refs"] = _mean(ref_counts)
    stats["defects"] = {k: _mean([int((r.get("defects") or {}).get(k, 0) or 0)
                                  for r in measured]) for k in DEFECT_KEYS}
    flags = {}
    for key in ("over_engineering", "verified", "tests_pass"):
        values = [r[key] for r in measured if isinstance(r.get(key), bool)]
        flags[key] = (sum(1 for v in values if v) / len(values)) if values else None
    stats["flags"] = flags
    return stats


def _pct(value: float | None) -> str:
    return "—" if value is None else "%.0f%%" % (100.0 * value)


def _num(value: float | None) -> str:
    """Token-scale numbers: two decimals there is noise, not precision."""
    return "—" if value is None else "%.0f" % value


def _attribution_section(records: list[dict]) -> list[str]:
    """Where the tokens actually went (Stage 2C)."""
    totals: dict[str, float] = {}
    traced = 0
    for rec in records:
        stages = rec.get("stages") or []
        if stages:
            traced += 1
        for stage in stages:
            totals[stage["stage"]] = totals.get(stage["stage"], 0) + stage["tokens"]
    if not totals:
        return []
    overall = sum(totals.values())
    out = ["", "## Token attribution", "",
           "| stage | tokens | share |", "|---|:--:|:--:|"]
    for stage, tokens in sorted(totals.items(), key=lambda kv: -kv[1]):
        out.append("| %s | %d | %.0f%% |"
                   % (stage, tokens, 100.0 * tokens / overall))
    out += ["", "Only the %d record(s) carrying a `stages` trace contribute; the "
                "rest are not counted as zero stages, they are simply absent."
                % traced, ""]
    return out


def _load_frequency_section(grouped: dict) -> list[str]:
    """What each bucket actually loaded (the lazy-load question in 2E)."""
    rows: list[tuple[str, str, int]] = []
    for bucket in COST_BUCKETS:
        tally: dict[str, int] = {}
        for runs in (grouped.get(bucket) or {}).values():
            for rec in runs:
                for ref in rec.get("references_loaded") or []:
                    tally[ref] = tally.get(ref, 0) + 1
        for ref, count in tally.items():
            rows.append((bucket, ref, count))
    if not rows:
        return []
    out = ["", "## Reference load frequency", "",
           "A reference showing up under `small` is the 2E question answered "
           "with counts rather than intuition.", "",
           "| bucket | reference | loads |", "|---|:--:|:--:|"]
    for bucket, ref, count in sorted(rows, key=lambda r: (COST_BUCKETS.index(r[0]),
                                                          -r[2], r[1])):
        out.append("| %s | %s | %d |" % (bucket, ref, count))
    out += [""]
    return out


# --- subcommands ----------------------------------------------------------

def cmd_check(args) -> int:
    report = Report()
    cases = load_cases()
    report.check(bool(cases), "eval corpus is not empty")
    corpus_check(report, cases)
    records_check(report, cases)
    cost_records_check(report, cases)

    print("ASCOS eval harness — %d checks run (%d cases, %d records, %d cost records)"
          % (len(report.checks), len(cases), len(load_records()),
             len(load_cost_records())))
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
    # Stage 2 records live apart from Stage 1: same shape of file, different
    # field contract, and pooling them would move the trigger hit rates.
    sink = COST_RECORDS_FILE if args.cost else RECORDS_FILE
    existing = load_cost_records() if args.cost else load_records()
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
        if rec.get("verdict") == INVALID and not rec.get("note"):
            errors.append("#%d: an invalid record must say why in `note`" % i)
        if rec.get("observation") is not None and rec.get("observation") not in OBSERVATIONS:
            errors.append("#%d: observation must be one of %s"
                          % (i, OBSERVATIONS))
        if rec.get("loaded") is not None and rec.get("loaded") not in LOADED:
            errors.append("#%d: loaded must be one of %s" % (i, LOADED))
        if args.cost:
            for err in cost_errors(rec):
                errors.append("#%d: %s" % (i, err))
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
    if args.cost:
        write_cost_records(existing)
    else:
        write_records(existing)
    print("ingested %d record(s) → %s (%d total)"
          % (len(incoming), rel(sink), len(existing)))
    return 0


def cmd_cost(args) -> int:
    """Stage 2: what ASCOS costs, and whether the spend was worth it."""
    cases = {c["id"]: c for c in load_cases() if c.get("id")}
    manifest = load_manifest(args.manifest)
    records = load_cost_records()
    if not records:
        print("no cost records yet — ingest with `ingest --cost --file <runs.jsonl>`")
        return 0

    grouped: dict[str, dict[str, list[dict]]] = {}
    for rec in records:
        bucket = cost_bucket(rec.get("case"), cases, manifest)
        if bucket and rec.get("variant") in VARIANTS:
            grouped.setdefault(bucket, {}).setdefault(rec["variant"], []).append(rec)

    lines = ["# ASCOS Stage 2 — cost report", "",
             "Generated from `%s` (%d records). Every figure is measured: the "
             "aggregator only divides sums it was given."
             % (rel(COST_RECORDS_FILE), len(records)), ""]

    cols = ["bucket", "variant", "runs", "invalid", "completion", "in", "out",
            "total", "seconds", "tools", "refs", "defects b/e/s/u",
            "over-eng", "verified", "tests", "QI"]
    lines += ["## Cost & quality by bucket", "",
              "`defects b/e/s/u` = bugs / missed edges / security / unnecessary "
              "changes, per run. `invalid` runs are excluded from every mean.", "",
              "| " + " | ".join(cols) + " |",
              "|" + "|".join(":--:" for _ in cols) + "|"]
    for bucket in COST_BUCKETS:
        for variant in VARIANTS:
            runs = (grouped.get(bucket) or {}).get(variant) or []
            if not runs:
                continue
            s = _bucket_stats(runs)
            if not s["n"]:
                continue
            defects = "/".join(_fmt(s["defects"][k]) for k in DEFECT_KEYS)
            flags = s["flags"]
            lines.append("| %s | %s | %d | %d | %s | %s | %s | %s | %s | %s | %s "
                         "| %s | %s | %s | %s | %s |" % (
                             bucket, variant, s["n"], s["invalid"],
                             _pct(s["hits"] / s["n"]), _num(s["in"]),
                             _num(s["out"]), _num(s["total"]), _fmt(s["sec"]),
                             _fmt(s["tools"]), _fmt(s["refs"]), defects,
                             _pct(flags["over_engineering"]),
                             _pct(flags["verified"]), _pct(flags["tests_pass"]),
                             _fmt(s["qi"])))
    lines += [""]

    baseline = args.baseline
    lines += ["## Delta vs `%s`" % baseline, "",
              "QG/TC = quality gain % ÷ token cost %. Blank when either side is "
              "unmeasured; `free` when quality rose without spending tokens.", "",
              "| bucket | variant | Δtokens | ΔQI (pts) | Δquality % | QG/TC |",
              "|---|:--:|:--:|:--:|:--:|:--:|"]
    for bucket in COST_BUCKETS:
        variants = grouped.get(bucket) or {}
        base = _bucket_stats(variants.get(baseline) or [])
        if not base["n"]:
            continue
        for variant in VARIANTS:
            if variant == baseline or not variants.get(variant):
                continue
            s = _bucket_stats(variants[variant])
            if not s["n"]:
                continue
            tb, tv = base.get("total"), s.get("total")
            qb, qv = base.get("qi"), s.get("qi")
            dtok = (100.0 * (tv - tb) / tb) if (tb and tv is not None) else None
            dpts = (qv - qb) if (qb is not None and qv is not None) else None
            dq = (100.0 * dpts / qb) if (dpts is not None and qb) else None
            if dtok is None or dq is None:
                ratio = "—"
            elif dtok <= 0:
                ratio = "free" if dq > 0 else "—"
            else:
                ratio = "%.2f" % (dq / dtok)
            lines.append("| %s | %s | %s | %s | %s | %s |" % (
                bucket, variant,
                "—" if dtok is None else "%+.0f%%" % dtok,
                "—" if dpts is None else "%+.1f" % dpts,
                "—" if dq is None else "%+.1f%%" % dq, ratio))
    lines += [""]

    lines += _attribution_section(records)
    lines += _load_frequency_section(grouped)

    weights = ", ".join("−%d per %s" % (w, k)
                        for k, w in sorted(QUALITY_WEIGHTS.items()))
    flags = ", ".join("−%d if %s" % (w, k) for k, w in sorted(QUALITY_FLAGS.items()))
    lines += ["## Method", "",
              "QI starts at %d and subtracts: %s; %s. Clamped at 0." % (
                  QUALITY_MAX, weights, flags),
              "",
              "Weights are registered in `evals/cost/README.md` before the first "
              "run and are not fitted to these results: changing them re-bases "
              "every round, which is why they are a constant and not a flag.",
              "",
              "Completion is reported next to QI, never inside it: a failing run "
              "should not be penalised twice for the same failure.", ""]

    os.makedirs(COST_RESULTS_DIR, exist_ok=True)
    with open(COST_REPORT_FILE, "w", encoding="utf-8", newline="\n") as fh:
        fh.write("\n".join(lines))

    print("\n".join(lines))
    print("\nwrote %s" % rel(COST_REPORT_FILE))
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


def _observation_section(by_case: dict) -> list[str]:
    """Non-misfire observation tags.

    Reported beside the misfire table, never inside it: a negative-routing
    statement is the routing decision being legible, which is the opposite of
    a misfire.
    """
    tally: dict[str, list[str]] = {}
    for cid in sorted(by_case):
        for variant in VARIANTS:
            for rec in by_case[cid].get(variant, []):
                tag = rec.get("observation")
                if tag:
                    tally.setdefault(tag, []).append(cid)
    if not tally:
        return []
    out = ["## Observations (recorded, not counted as misfires)", ""]
    for tag, cids in sorted(tally.items(), key=lambda kv: (-len(kv[1]), kv[0])):
        out.append("- `%s` — %d record(s) across %s"
                   % (tag, len(cids), ", ".join(sorted(set(cids)))))
    out += [""]
    return out


def _loaded_section(cases: dict[str, dict], by_case: dict) -> list[str]:
    """How many runs actually opened SKILL.md.

    A rubric decides whether an *answer* looks like activation, so every rubric
    revision silently moves that number. Loading the file is a behaviour the
    run either performed or did not, which makes the must-not-fire half of
    this table a safety check that survives a rubric change.
    """
    tally: dict[tuple[str, str], int] = {}
    recorded = 0
    for cid in sorted(by_case):
        expect = cases.get(cid, {}).get("expect", "?")
        for variant in VARIANTS:
            for rec in by_case[cid].get(variant, []):
                if rec.get("loaded") in LOADED:
                    recorded += 1
                if rec.get("loaded") == "yes":
                    tally[(expect, variant)] = tally.get((expect, variant), 0) + 1
    if not recorded:
        return []
    out = ["## Loaded SKILL.md (behaviour, not an output judgement)", ""]
    out.append("| expectation | variant | runs that loaded |")
    out.append("|---|:--:|:--:|")
    for key in sorted(tally):
        out.append("| %s | %s | %d |" % (key[0], key[1], tally[key]))
    out += ["", "%d record(s) carry a `loaded` value; the rest were recorded "
                "before the field existed." % recorded, ""]
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
    invalids: list[tuple[str, str, object, str]] = []
    for cid in sorted(by_case):
        case = cases.get(cid, {})
        expect = case.get("expect", "pass")
        lines.append("## %s · %s · expect=%s" % (cid, case.get("group", "?"), expect))
        lines.append("")
        cols = (["variant", "measured", "hits", "invalid"]
                + ["pass@%d" % k for k in ks]
                + ["mean s", "mean tokens"])
        lines.append("| " + " | ".join(cols) + " |")
        lines.append("|" + "|".join(":--:" for _ in cols) + "|")
        for variant in VARIANTS:
            runs = by_case[cid].get(variant, [])
            if not runs:
                continue
            # Invalid runs never reach the denominator: they measured the
            # environment, not the skill.
            measured = [r for r in runs if r.get("verdict") != INVALID]
            dropped = len(runs) - len(measured)
            hits = sum(1 for r in measured if r.get("verdict") == expect)
            n = len(measured)
            row = [variant, str(n), ("%d/%d" % (hits, n)) if n else "—", str(dropped)]
            row += [_fmt(pass_at_k(n, hits, k)) for k in ks]
            row.append(_fmt(_mean([r["seconds"] for r in measured if "seconds" in r])))
            row.append(_fmt(_mean([r["tokens"] for r in measured if "tokens" in r])))
            lines.append("| " + " | ".join(row) + " |")
            agg = overall.setdefault(variant, {"n": 0, "hits": 0, "sec": [], "tok": [],
                                               "invalid": 0})
            agg["n"] += n
            agg["hits"] += hits
            agg["invalid"] += dropped
            agg["sec"] += [r["seconds"] for r in measured if "seconds" in r]
            agg["tok"] += [r["tokens"] for r in measured if "tokens" in r]
            for rec in [r for r in runs if r.get("verdict") == INVALID]:
                invalids.append((cid, variant, rec.get("run"), rec.get("note", "")))
        lines.append("")

    misfire = _misfire_section(cases, by_case)
    if misfire:
        lines += misfire
    lines += _observation_section(by_case)
    lines += _loaded_section(cases, by_case)
    if invalids:
        lines += ["## Not measurable (excluded from every rate)", "",
                  "| case | variant | run | reason |", "|---|:--:|:--:|---|"]
        for cid, variant, run, note in invalids:
            lines.append("| %s | %s | %s | %s |" % (cid, variant, run, note))
        lines += [""]

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
    p.add_argument("--cost", action="store_true",
                   help="ingest into the Stage 2 cost record file instead")
    p.set_defaults(func=cmd_ingest)

    p = sub.add_parser("cost", help="Stage 2 cost/quality report")
    p.add_argument("--baseline", choices=VARIANTS, default="without_skill",
                   help="variant every delta is measured against")
    p.add_argument("--manifest",
                   help="bucket manifest (default: evals/cost/manifest.json)")
    p.set_defaults(func=cmd_cost)

    p = sub.add_parser("report", help="aggregate records into a report")
    p.add_argument("--k", type=int, nargs="+", default=[1, 3],
                   help="values of k for pass@k (default: 1 3)")
    p.set_defaults(func=cmd_report)

    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
