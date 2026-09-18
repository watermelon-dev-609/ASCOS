"""Judge a lazy-loading change on what it *does*, not on what it costs.

§20 of the protocol measured this: a 24-run batch cannot adjudicate a 15%
criterion on Δtotal (power 12%, false positive 22%, 328 runs to do it
properly). The same 24 runs *can* adjudicate the mechanism, because
"did this run open the file" is a near-deterministic switch rather than a
noisy continuous quantity.

So the primary evidence for the L0/L1/L2 reasoning budget is:

* which references a run opened (`references_loaded`, read out of the event
  stream, never self-reported);
* L0 forbids `change-impact.md`, `context-model.md`, `non-negotiables.md`
  (SKILL.md §推理预算), while `non-negotiables.md` is mandatory at L1/L2
  before delivery -- which makes it the cleanest observable discriminator
  between "the model took the L0 path" and "it did not".

Token cost is then *derived* from what was loaded, using the measured slope
from §19.1, instead of being measured directly through the variance that
swamped it.

Usage: python scripts/cost_mechanism.py [--dir <new batch>] [--baseline <old batch>]
"""
import argparse
import json
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from eval_common import ROOT  # noqa: E402
import cost_report  # noqa: E402

DEFAULT_BATCH = cost_report.DEFAULT_BATCH
REFERENCES_DIR = os.path.join(ROOT, "references")

# L0 must not load these three (SKILL.md §推理预算). Keeping the list next to
# the rule it encodes is the point: if the rule changes, this is where it has
# to change with it.
L0_FORBIDDEN = ("change-impact.md", "context-model.md", "non-negotiables.md")

# Calibrated on the three files above: 337/1077, 660/2113, 922/2951 bytes all
# give 0.312. Measured rather than assumed so a file that grows is priced
# correctly, and so the numbers trace back to something inspectable.
TOKENS_PER_BYTE = 0.312


# --- pure logic -----------------------------------------------------------

def reference_tokens(name):
    """Token cost of loading one reference, from its real size on disk.

    None when the file is not there: an absent file cannot be priced, and
    pricing it 0 would silently under-state the saving.
    """
    path = os.path.join(REFERENCES_DIR, name)
    if not os.path.isfile(path):
        return None
    return os.path.getsize(path) * TOKENS_PER_BYTE


def forbidden_tokens(refs):
    """Tokens a run spent on references L0 forbids. Unpriceable ones are
    skipped rather than counted as zero."""
    total = 0.0
    for name in refs or []:
        if name in L0_FORBIDDEN:
            cost = reference_tokens(name)
            if cost is not None:
                total += cost
    return total


def loading_table(rows, arm="with_skill"):
    """Per case: how many runs opened each L0-forbidden reference.

    Only the with_skill arm is meaningful -- the control never loads ASCOS
    files, so counting it would just add 0s to the denominator.
    """
    cells = cost_report.summarise(rows)
    out = {}
    for (case, variant), cell in sorted(cells.items()):
        if variant != arm:
            continue
        recs = [r for r in cell.get("valid", [])]
        if not recs:
            continue
        counts = {name: 0 for name in L0_FORBIDDEN}
        any_forbidden = 0
        spent = []
        for r in recs:
            refs = r.get("references_loaded") or []
            hit = [n for n in refs if n in L0_FORBIDDEN]
            for n in hit:
                counts[n] += 1
            if hit:
                any_forbidden += 1
            spent.append(forbidden_tokens(refs))
        out[case] = {
            "runs": len(recs),
            "counts": counts,
            "runs_loading_any": any_forbidden,
            "tokens_spent_per_run": spent,
            "mean_tokens_per_run": (sum(spent) / len(spent)) if spent else None,
        }
    return out


def totals(table):
    """Collapse per-case counts into one batch-level count."""
    runs = sum(v["runs"] for v in table.values())
    counts = {n: sum(v["counts"][n] for v in table.values()) for n in L0_FORBIDDEN}
    any_forbidden = sum(v["runs_loading_any"] for v in table.values())
    weighted = [t for v in table.values() for t in v["tokens_spent_per_run"]]
    return {
        "runs": runs,
        "counts": counts,
        "runs_loading_any": any_forbidden,
        "mean_tokens_per_run": (sum(weighted) / len(weighted)) if weighted else None,
    }


def binom_tail_le(k, n, p):
    """P(X <= k) for X ~ Bin(n, p). The prediction is 'fewer loads'."""
    if n <= 0 or not (0.0 <= p <= 1.0):
        return None
    return sum(math.comb(n, i) * p ** i * (1 - p) ** (n - i) for i in range(0, k + 1))


def binom_tail_ge(k, n, p):
    """P(X >= k). Needed because 'no change took effect' is a real branch: if
    the model classifies these cases as L1, non-negotiables becomes mandatory
    and the count goes *up* toward n."""
    if n <= 0 or not (0.0 <= p <= 1.0):
        return None
    return sum(math.comb(n, i) * p ** i * (1 - p) ** (n - i) for i in range(k, n + 1))


def compare(baseline_rows, new_rows, arm="with_skill"):
    """Baseline rate vs new count, with both tails.

    Both tails are reported because the registered prediction has two branches
    (L0 taken -> count falls; L1 taken -> count rises toward n), and picking
    one tail after seeing the data would be fitting the test to the result.
    """
    base = totals(loading_table(baseline_rows, arm))
    new = totals(loading_table(new_rows, arm))
    nb, nn = base["runs"], new["runs"]
    out = {"baseline": base, "new": new, "per_reference": {}}
    for name in tuple(L0_FORBIDDEN) + ("__any__",):
        kb = base["runs_loading_any"] if name == "__any__" else base["counts"][name]
        kn = new["runs_loading_any"] if name == "__any__" else new["counts"][name]
        p = (kb / nb) if nb else None
        out["per_reference"][name] = {
            "baseline": "%d/%d" % (kb, nb),
            "new": "%d/%d" % (kn, nn),
            "baseline_rate": p,
            "p_le": binom_tail_le(kn, nn, p) if p is not None else None,
            "p_ge": binom_tail_ge(kn, nn, p) if p is not None else None,
        }
    return out


# --- rendering ------------------------------------------------------------

def render_single(table, title):
    L = ["# 机制判据 —— %s" % title, ""]
    L.append("L0 禁止加载：%s" % ", ".join(L0_FORBIDDEN))
    L.append("")
    L.append("| 用例 | 次数 | %s | 任一命中 | 每次花在禁用 reference 上的 token |"
             % " | ".join(n.replace(".md", "") for n in L0_FORBIDDEN))
    L.append("|---|---:|%s|---:|---:|" % ("---:|" * len(L0_FORBIDDEN)))
    for case, v in table.items():
        L.append("| %s | %d | %s | %d | %s |" % (
            case, v["runs"],
            " | ".join(str(v["counts"][n]) for n in L0_FORBIDDEN),
            v["runs_loading_any"],
            ("%.0f" % v["mean_tokens_per_run"])
            if v["mean_tokens_per_run"] is not None else "—"))
    t = totals(table)
    L.append("")
    L.append("- 合计：**%d / %d** 次运行至少加载了一个 L0 禁用 reference"
             % (t["runs_loading_any"], t["runs"]))
    if t["mean_tokens_per_run"] is not None:
        L.append("- 每次平均花在禁用 reference 上：**%.0f token**（这就是 L0 能省下的上限）"
                 % t["mean_tokens_per_run"])
    return "\n".join(L)


def render_compare(cmp_result):
    L = ["", "## 对照基线", ""]
    L.append("| 观测量 | 基线 | 新批 | P(≤) | P(≥) |")
    L.append("|---|---|---|---:|---:|")
    for name, d in cmp_result["per_reference"].items():
        label = "任一命中" if name == "__any__" else name
        L.append("| %s | %s | %s | %s | %s |" % (
            label, d["baseline"], d["new"],
            _p(d["p_le"]), _p(d["p_ge"])))
    L.append("")
    L.append("两个尾巴都给：**预测有两个分支**（L0 生效 → 计数下降；判为 L1 → 计数升向 n）。"
             "看完结果再挑一个尾巴就是把检验拟合给结果。")
    return "\n".join(L)


def _p(v):
    if v is None:
        return "—"
    return "%.1e" % v if v < 1e-3 else "%.3f" % v


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--dir", default=DEFAULT_BATCH, help="batch to judge")
    ap.add_argument("--baseline", help="baseline batch to compare against")
    ap.add_argument("--arm", default="with_skill")
    ap.add_argument("--json", help="write the machine-readable result here")
    args = ap.parse_args(argv)

    rows = cost_report.load_records(args.dir)
    table = loading_table(rows, args.arm)
    out = render_single(table, os.path.basename(args.dir.rstrip(os.sep)))
    payload = {"table": table, "totals": totals(table)}

    if args.baseline:
        base_rows = cost_report.load_records(args.baseline)
        cmp_result = compare(base_rows, rows, args.arm)
        out += "\n" + render_compare(cmp_result)
        payload["compare"] = cmp_result

    sys.stdout.write(out + "\n")
    if args.json:
        with open(args.json, "w", encoding="utf-8", newline="\n") as fh:
            json.dump(payload, fh, ensure_ascii=False, indent=1, default=str)
    return 0


if __name__ == "__main__":
    sys.exit(main())
