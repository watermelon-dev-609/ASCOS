"""Can this batch size actually detect the change it is about to be judged on?

Stage 2 keeps running into the same trap from opposite ends: a batch that cost
real money and then turned out to measure nothing (pilot r4, asymmetric
permission denials), and a change that was implemented and then could not be
measured at all (2D, exhausted balance). Both are cases of *running first and
finding out later*. This script exists so the finding-out happens before the
spend.

It asks: if the change under test moves Δtotal by X%, will a batch of this
shape see it, or will it drown in run-to-run variance? Three runs of the same
case have varied by 1.96x, so this is not a rhetorical question.

Why this is analytic and not a bootstrap: the estimator takes a *median* over
three runs per cell, and bootstrapping a median of three is biased — on the
baseline batch the resampled distribution centred on +13192 while the point
estimate was +11609, nearly a full standard error high, which quietly
understates the false-positive rate. The closed form below reproduces the
bootstrap's spread to within 2% without the bias, and is deterministic, so
tests can assert on it.

Usage: python scripts/cost_resolution.py [--dir <batch>] [--effect 0.15] [--metric total_tokens]
"""
import argparse
import json
import math
import os
import statistics
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from eval_common import ROOT  # noqa: E402
import cost_report  # noqa: E402

DEFAULT_BATCH = cost_report.DEFAULT_BATCH
METRIC = "total_tokens"
DEFAULT_EFFECT = 0.15

# Two-sided alpha .05 at 80% power. A batch that sees the effect half the time
# is not a measurement, and the protocol has to know that beforehand.
POWER_Z = 1.96 + 0.8416
# SE(median of n draws) = 1.253 * sd / sqrt(n). The estimator is a median.
MEDIAN_PENALTY = 1.253


# --- pure logic -----------------------------------------------------------

def _norm_cdf(z):
    return 0.5 * (1 + math.erf(z / math.sqrt(2)))


def raw_runs(rows, metric=METRIC):
    """Per (case, arm), the raw per-run values of the metric.

    Only valid runs, and only cells cost_report would have scored at all
    (>= MIN_VALID). A cell with one run cannot contribute to a variance
    estimate any more than it could to a table.
    """
    cells = cost_report.summarise(rows)
    out = {}
    for (case, arm), cell in cells.items():
        recs = cell.get("valid", [])
        if len(recs) < cost_report.MIN_VALID:
            continue
        values = [r.get(metric) for r in recs if r.get(metric) is not None]
        if len(values) >= cost_report.MIN_VALID:
            out[(case, arm)] = sorted(values)
    return out


def case_deltas(cells):
    """Per case the protocol's estimator, plus the cells it came from.

    Cases where either arm is missing are dropped rather than substituted: a
    one-armed case has no delta, and pretending otherwise would invent
    precision the batch does not have.
    """
    out = {}
    for case in sorted({c for c, _ in cells}):
        w = cells.get((case, "with_skill"))
        o = cells.get((case, "without_skill"))
        if not w or not o:
            continue
        out[case] = statistics.median(w) - statistics.median(o)
    return out


def pooled_sd(cells):
    """Within-cell standard deviation of a single run, pooled over cells.

    This is the noise one additional replicate has to fight. Pooled rather
    than per-cell because with three runs a per-cell SD is barely a number,
    and the eight cells are replicates of the same measurement process.
    """
    groups = [v for v in cells.values() if len(v) >= 2]
    devs, dof = [], 0
    for values in groups:
        mean = statistics.fmean(values)
        devs += [(v - mean) ** 2 for v in values]
        dof += len(values) - 1
    if dof <= 0 or not devs:
        return None
    return (sum(devs) / dof) ** 0.5


def min_runs(cells):
    """Smallest cell size. Used as n, which is the conservative choice."""
    return min((len(v) for v in cells.values()), default=1)


def se_point(sd, n, n_cases):
    """SE of the reported Δ: median per cell, then mean over cases.

    Two arms per case, so per case the SE is 1.253*sd*sqrt(2/n); averaging
    over n_cases independent cases divides by sqrt(n_cases).
    """
    if not sd or n <= 0 or n_cases <= 0:
        return None
    return MEDIAN_PENALTY * sd * math.sqrt(2.0 / n) / math.sqrt(n_cases)


def se_diff(se_point_value):
    """SE of (new batch Δ − baseline batch Δ).

    The comparison is paired on the same cases, so the *between-case*
    heterogeneity cancels and only estimation noise doubles. This is the
    quantity a "did it drop by X%" criterion actually lives on, and it is
    sqrt(2) times the SE of either measurement alone.
    """
    if se_point_value is None:
        return None
    return math.sqrt(2) * se_point_value


def required_runs_from_se(se, effect, current_n):
    """Runs per arm needed, scaled off the measured SE.

    SE goes as 1/sqrt(n), so shrinking it by a factor k costs k^2 the runs.
    """
    if not se or effect <= 0:
        return None
    return math.ceil(current_n * (POWER_Z * se / effect) ** 2)


def analyse(rows, effect=DEFAULT_EFFECT, metric=METRIC):
    cells = raw_runs(rows, metric=metric)
    deltas = case_deltas(cells)
    if not deltas:
        return {"ok": False,
                "reason": "no case has both arms with >= %d valid runs"
                          % cost_report.MIN_VALID}
    baseline = statistics.fmean(deltas.values())
    sd = pooled_sd(cells)
    n = min_runs(cells)
    se = se_point(sd, n, len(deltas))
    sed = se_diff(se)
    effect_tokens = baseline * effect
    out = {
        "ok": True,
        "metric": metric,
        "cases": len(deltas),
        "runs_per_cell": sorted({len(v) for v in cells.values()}),
        "baseline_delta": baseline,
        "per_case_delta": deltas,
        "effect_fraction": effect,
        "effect_tokens": effect_tokens,
        "threshold": baseline * (1 - effect),
        "pooled_sd": sd,
        "se_point": se,
        "se_diff": sed,
        "mde": POWER_Z * sed if sed else None,
        # Two different questions. Conflating them is what made the first
        # version of this script print "resolvable" next to a power number that
        # said otherwise.
        #   power               = would a real effect this big be seen?
        #   false_positive_rate = would noise alone look like success?
        "resolvable": (effect_tokens >= POWER_Z * sed) if sed else None,
        "power": _norm_cdf(effect_tokens / sed - 1.96) if sed else None,
        "false_positive_rate": _norm_cdf(-effect_tokens / sed) if sed else None,
        "required_runs_per_arm": required_runs_from_se(sed, effect_tokens, n),
    }
    return out


# --- rendering ------------------------------------------------------------

def render(a):
    if not a.get("ok"):
        return "分辨力：无法评估 —— %s" % a["reason"]
    m = a["metric"]
    L = ["# 分辨力分析 —— Δ%s 上能不能看出 %.0f%% 的变化" % (m, 100 * a["effect_fraction"]), ""]
    L.append("- 用例数（两臂齐全）：%d；每格有效次数：%s"
             % (a["cases"], a["runs_per_cell"]))
    L.append("- 基线 Δ%s：%+.0f tokens；单次运行合并标准差：%s"
             % (m, a["baseline_delta"],
                ("%.0f" % a["pooled_sd"]) if a["pooled_sd"] else "—"))
    L.append("- 估计量标准误：%.0f（对照两批之差：%.0f）"
             % (a["se_point"], a["se_diff"]))
    L.append("- 要判定的效果：%.0f%% = %+.0f tokens（阈值 Δ%s ≤ %+.0f）"
             % (100 * a["effect_fraction"], a["effect_tokens"], m, a["threshold"]))
    L.append("- 80%% 功效下**最小可检出效果**：%.0f tokens" % a["mde"])
    L.append("")
    L.append("### 两个不同的问题")
    L.append("")
    if a["resolvable"]:
        L.append("- **功效**：能检出（效果 %.0f ≥ 最小可检出 %.0f）。"
                 % (a["effect_tokens"], a["mde"]))
    else:
        L.append("- **功效：检不出。** 真实效果 %.0f tokens，最小可检出 %.0f tokens，"
                 "检出概率仅 **%.0f%%**。"
                 % (a["effect_tokens"], a["mde"], 100 * a["power"]))
        L.append("  即：**跑完若显示『没降够 %.0f%%』，几乎什么都证明不了** —— 真的降了也大概率读不出来。"
                 % (100 * a["effect_fraction"]))
    L.append("- **误报**：什么都没变，却读到『降了 ≥%.0f%%』的概率 **%.0f%%**。"
             % (100 * a["effect_fraction"], 100 * a["false_positive_rate"]))
    L.append("  （基线本身也是这 3 次测出来的、且被拿来当阈值，回归效应会让这个数再高一些。）")
    L.append("")
    L.append("- 要按 80%% 功效做二值判定，每臂每例约需 **%d 次**（当前 %d 次），全批 ≈ %d 次。"
             % (a["required_runs_per_arm"], a["runs_per_cell"][0],
                a["required_runs_per_arm"] * 2 * a["cases"]))
    return "\n".join(L)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--dir", default=DEFAULT_BATCH, help="batch directory")
    ap.add_argument("--effect", type=float, default=DEFAULT_EFFECT,
                    help="relative change to detect, e.g. 0.15")
    ap.add_argument("--metric", default=METRIC, choices=list(cost_report.METRICS),
                    help="which delta the criterion is written against")
    ap.add_argument("--json", help="write the machine-readable analysis here")
    args = ap.parse_args(argv)

    rows = cost_report.load_records(args.dir)
    a = analyse(rows, effect=args.effect, metric=args.metric)
    sys.stdout.write(render(a) + "\n")
    if args.json:
        with open(args.json, "w", encoding="utf-8", newline="\n") as fh:
            json.dump(a, fh, ensure_ascii=False, indent=1, default=str)
    return 0 if a.get("ok") else 1


if __name__ == "__main__":
    sys.exit(main())
