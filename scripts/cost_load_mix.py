"""Where the static load actually goes, file by file.

§19 established that 87% of Δinput is "which files got read" rather than "how
much work got done" -- but it did not say *which* files, and the two obvious
answers point at opposite policies. This answers it, and it turns out the
largest item by far is the entrypoint:

    SKILL.md (root)      ~53% of static load
    sub-skills           ~28%
    references           ~19%   (the L0-forbidden three: ~10%)

So "lazy-load the references" (2E) aims at the smaller half. That is not a
reason to abandon it, but it is a reason to stop assuming it is the main lever.

Two caveats that change how these numbers should be read:

* Only files a run actually opened are counted. Pricing all six sub-skills on
  every run -- which is the tempting shortcut -- overstates the static load by
  about 2.5x, because most runs load the root alone or the root plus two.
* A file is paid for on *every turn it stays in context*, not once. The root is
  loaded first, so it is re-sent on all of them; a reference opened late is
  paid for on fewer. Sizes here are therefore a lower bound on the root's share
  and an upper bound on the late references'.

Usage: python scripts/cost_load_mix.py [--dir <batch>] [--json <out>]
"""
import argparse
import collections
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from eval_common import ROOT  # noqa: E402
import cost_mechanism  # noqa: E402
import cost_report  # noqa: E402

DEFAULT_BATCH = cost_report.DEFAULT_BATCH
ROOT_SKILL = "SKILL.md"
ROOT_LABEL = "SKILL.md(根)"
ASCOS = "ascos"


# --- pure logic -----------------------------------------------------------

def skill_files():
    """{label: path} for the root and every installed sub-skill.

    Read from disk rather than listed by hand so a new sub-skill is priced
    without anyone remembering to update a constant.
    """
    out = {ROOT_LABEL: ROOT_SKILL}
    skills_dir = os.path.join(ROOT, "skills")
    if os.path.isdir(skills_dir):
        for name in sorted(os.listdir(skills_dir)):
            rel = os.path.join("skills", name, "SKILL.md")
            if os.path.isfile(os.path.join(ROOT, rel)):
                out["skill:" + name] = rel
    return out


def price(rel):
    """Token cost of a file from its real size. None if absent: an absent file
    cannot be priced, and pricing it 0 would understate the total."""
    path = os.path.join(ROOT, rel)
    if not os.path.isfile(path):
        return None
    return os.path.getsize(path) * cost_mechanism.TOKENS_PER_BYTE


def load_mix(rows, files=None):
    """Total and per-run token cost of each loaded file, over the with arm.

    Only the with arm is meaningful: the control loads none of these, so
    including it would halve every average for no reason.
    """
    files = files or skill_files()
    mix = collections.Counter()
    runs = 0
    for rec in rows:
        if rec.get("variant") != "with_skill" or not cost_report.is_valid(rec):
            continue
        runs += 1
        for skill in (rec.get("skills_loaded") or []):
            label = ROOT_LABEL if skill == ASCOS else "skill:" + skill
            rel = files.get(label)
            if rel:
                cost = price(rel)
                if cost is not None:
                    mix[label] += cost
        for ref in (rec.get("references_loaded") or []):
            cost = cost_mechanism.reference_tokens(ref)
            if cost is not None:
                mix["ref:" + ref] += cost
    return {"runs": runs, "mix": mix, "total": sum(mix.values())}


def shares(mix):
    """Split into skill / reference buckets, and the L0-forbidden slice.

    The forbidden slice is reported separately because it is the part the L0
    budget rule can actually remove, and §19.3 showed it is far smaller than
    the rule's author assumed.
    """
    total = sum(mix.values())
    if not total:
        return {"total": 0, "skill": 0, "reference": 0, "l0_forbidden": 0,
                "skill_pct": None, "reference_pct": None, "l0_forbidden_pct": None}
    skill = sum(v for k, v in mix.items() if not k.startswith("ref:"))
    forb = sum(v for k, v in mix.items()
               if k.split(":", 1)[-1] in cost_mechanism.L0_FORBIDDEN)
    return {"total": total, "skill": skill, "reference": total - skill,
            "l0_forbidden": forb,
            "skill_pct": 100 * skill / total,
            "reference_pct": 100 * (total - skill) / total,
            "l0_forbidden_pct": 100 * forb / total}


# --- rendering ------------------------------------------------------------

def render(result, title):
    runs = result["runs"]
    mix = result["mix"]
    s = shares(mix)
    L = ["# 静态加载构成 —— %s" % title, ""]
    if not runs:
        return "\n".join(L + ["没有有效的 with 臂运行，无法拆分。"])
    L.append("- with 臂有效次数：%d；静态加载合计 %.0f token（每次 %.0f）"
             % (runs, s["total"], s["total"] / runs))
    L.append("")
    L.append("| 文件 | 合计 token | 占比 | 每次 |")
    L.append("|---|---:|---:|---:|")
    for k, v in mix.most_common():
        L.append("| %s | %.0f | %.1f%% | %.0f |"
                 % (k, v, 100 * v / s["total"], v / runs))
    L.append("")
    L.append("- skill 类（根 + 子）：%.0f（**%.1f%%**）；reference 类：%.0f（%.1f%%）"
             % (s["skill"], s["skill_pct"], s["reference"], s["reference_pct"]))
    L.append("- 其中 L0 禁用的三个：%.0f（全部静态加载的 **%.1f%%**，每次 %.0f）"
             % (s["l0_forbidden"], s["l0_forbidden_pct"], s["l0_forbidden"] / runs))
    L.append("")
    L.append("**读法**：一个文件在上下文里待多少个回合，就要被付多少次。"
             "根文件最早加载、每回合都在，所以上表的根占比是**下限**。")
    return "\n".join(L)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--dir", default=DEFAULT_BATCH)
    ap.add_argument("--json", help="write the machine-readable result here")
    args = ap.parse_args(argv)

    rows = cost_report.load_records(args.dir)
    result = load_mix(rows)
    sys.stdout.write(render(result, os.path.basename(
        args.dir.rstrip(os.sep))) + "\n")
    if args.json:
        with open(args.json, "w", encoding="utf-8", newline="\n") as fh:
            json.dump({"runs": result["runs"],
                       "mix": dict(result["mix"]),
                       "shares": shares(result["mix"])},
                      fh, ensure_ascii=False, indent=1)
    return 0


if __name__ == "__main__":
    sys.exit(main())
