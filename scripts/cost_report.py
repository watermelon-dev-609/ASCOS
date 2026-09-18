"""Aggregate a cost batch into the 2C token-attribution table.

The runner writes one record per (case, arm, run). This script turns those into
the numbers the stage actually needs: how much more ASCOS costs, and *where*
the difference sits — extra input, extra output, or extra tool calls.

Two rules from the protocol are enforced here rather than left to the reader:

* an invalid run never enters a denominator (it measured nothing);
* a cell with fewer than two valid runs is reported as `inconclusive`, never
  as a number. Three runs of the same case varied by 1.96x in the pilot, so a
  single run is not enough to say anything about that case.

Usage: python scripts/cost_report.py [--dir <batch>] [--json <out>]
"""
import argparse
import json
import os
import statistics
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from eval_common import ROOT  # noqa: E402

DEFAULT_BATCH = os.path.join(ROOT, "evals", "cost", "results", "raw", "main-2026-09-18")
RECORDS = "cost-runs.jsonl"
MIN_VALID = 2
# cache_read and num_turns are in here because total_tokens alone is blind to
# most of the prompt volume: on the baseline batch it missed ~251k tokens per
# case against a measured delta of ~11.6k. Reporting them next to the others
# is what stops a reader from reading "delta-total" as "the cost".
METRICS = ("input_tokens", "output_tokens", "total_tokens",
           "cache_read_tokens", "num_turns", "tool_calls")


# --- IO -------------------------------------------------------------------

def load_records(batch_dir):
    """Read every record file under a batch directory, newest last."""
    path = os.path.join(batch_dir, RECORDS)
    if not os.path.isfile(path):
        raise SystemExit("no %s under %s" % (RECORDS, batch_dir))
    rows = []
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


# --- pure logic -----------------------------------------------------------

def is_valid(rec):
    """A run measured something. Invalid runs carry a note saying why not."""
    return rec.get("verdict") != "invalid" and rec.get("total_tokens") is not None


def _median(values):
    return statistics.median(values) if values else None


def summarise(rows):
    """Group by (case, arm). Keeps every raw run so nothing is smoothed away."""
    cells = {}
    for rec in rows:
        key = (rec.get("case"), rec.get("variant"))
        cell = cells.setdefault(key, {"valid": [], "invalid": []})
        (cell["valid"] if is_valid(rec) else cell["invalid"]).append(rec)
    return cells


def cell_stats(recs):
    """Median per metric plus per-run raw values, or None when under-powered."""
    if len(recs) < MIN_VALID:
        return None
    stats = {"n": len(recs), "runs": {}}
    for metric in METRICS:
        values = [r.get(metric) for r in recs if r.get(metric) is not None]
        stats["runs"][metric] = sorted(values)
        stats[metric] = _median(values)
    models = sorted({r.get("model") for r in recs if r.get("model")})
    stats["models"] = models
    skills = sorted({s for r in recs for s in (r.get("skills_loaded") or [])})
    stats["skills_loaded"] = skills
    return stats


def activated(stats):
    """Did ASCOS actually load on the with_skill arm? Observed, not assumed.

    Returns None rather than False when there is nothing to observe — an
    under-powered cell has not shown that ASCOS stayed quiet, it has shown
    nothing at all, and the two must not look the same in a table.
    """
    if not stats:
        return None
    return "ascos" in stats.get("skills_loaded", [])


def build_pairs(cells, cases):
    """One row per case: with-arm, without-arm, delta, verdict."""
    out = []
    for case in cases:
        with_stats = cell_stats(cells.get((case, "with_skill"), {}).get("valid", []))
        without_stats = cell_stats(cells.get((case, "without_skill"), {}).get("valid", []))
        invalid = (len(cells.get((case, "with_skill"), {}).get("invalid", []))
                   + len(cells.get((case, "without_skill"), {}).get("invalid", [])))
        row = {
            "case": case,
            "with": with_stats,
            "without": without_stats,
            "invalid_runs": invalid,
            "activated": activated(with_stats),
        }
        if with_stats and without_stats:
            row["delta"] = {m: with_stats[m] - without_stats[m] for m in METRICS
                            if with_stats[m] is not None and without_stats[m] is not None}
            row["verdict"] = "ok"
        else:
            row["delta"] = None
            row["verdict"] = "inconclusive"
        out.append(row)
    return out


# --- rendering ------------------------------------------------------------

def render_markdown(pairs, batch_dir):
    lines = ["# 2C Token 归因 —— %s" % os.path.basename(batch_dir), ""]
    lines.append("每格取**中位数**；`n` 为有效次数；`<%d` 次记为 inconclusive，不进任何分母。"
                 % MIN_VALID)
    lines.append("")
    lines.append("| 用例 | 激活 | n(with) | n(without) | Δtotal | Δinput | Δcache读 | Δoutput | Δ回合 | Δ工具 | 结论 |")
    lines.append("|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---|")
    for row in pairs:
        d = row["delta"] or {}
        def v(metric):
            return d.get(metric)
        def n(arm):
            s = row[arm]
            return s["n"] if s else 0
        lines.append("| %s | %s | %d | %d | %s | %s | %s | %s | %s | %s | %s |" % (
            row["case"], {True: "是", False: "否", None: "—"}[row["activated"]],
            n("with"), n("without"),
            _fmt(v("total_tokens")), _fmt(v("input_tokens")),
            _fmt(v("cache_read_tokens")), _fmt(v("output_tokens")),
            _fmt(v("num_turns")), _fmt(v("tool_calls")),
            row["verdict"]))
    lines.append("")
    lines.append("Δtotal = Δinput + Δoutput，**不含缓存读取**。两者费率不同，"
                 "且本仓库无从得知该费率，故不折算成钱，只并列呈现。")
    lines.append("")
    lines.append("## 原始每次值（不做平滑）")
    lines.append("")
    for row in pairs:
        lines.append("### %s" % row["case"])
        for arm in ("with", "without"):
            stats = row[arm]
            if not stats:
                lines.append("- %s: **inconclusive**（有效次数 < %d）" % (arm, MIN_VALID))
                continue
            lines.append("- %s: n=%d model=%s skills=%s" % (
                arm, stats["n"], ",".join(stats["models"]) or "?",
                ",".join(stats["skills_loaded"]) or "—"))
            for metric in METRICS:
                lines.append("    - %s: %s（中位数 %s）" % (
                    metric, stats["runs"][metric], _fmt(stats[metric])))
        if row["invalid_runs"]:
            lines.append("- 无效次数：%d（已排除出所有分母）" % row["invalid_runs"])
        lines.append("")
    return "\n".join(lines)


def _fmt(value):
    return "—" if value is None else "%+d" % value if isinstance(value, int) else "%s" % value


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dir", default=DEFAULT_BATCH, help="batch directory")
    parser.add_argument("--json", help="write the machine-readable summary here")
    parser.add_argument("--markdown", help="write the markdown table here")
    args = parser.parse_args(argv)

    rows = load_records(args.dir)
    cases = sorted({r.get("case") for r in rows})
    cells = summarise(rows)
    pairs = build_pairs(cells, cases)

    valid = sum(1 for r in rows if is_valid(r))
    text = render_markdown(pairs, args.dir)
    header = "records=%d valid=%d invalid=%d\n\n" % (
        len(rows), valid, len(rows) - valid)
    sys.stdout.write(header + text + "\n")

    if args.json:
        with open(args.json, "w", encoding="utf-8", newline="\n") as fh:
            json.dump(pairs, fh, ensure_ascii=False, indent=1)
    if args.markdown:
        with open(args.markdown, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(text + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
