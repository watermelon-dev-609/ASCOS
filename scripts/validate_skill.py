#!/usr/bin/env python3
"""ASCOS structure validator.

Checks the skill package for structural integrity so a bad edit fails fast:
front-matter, naming, dead links, orphan skills, required sections, size and
duplicated rules across files.

Usage:
    python scripts/validate_skill.py            # human readable report
    python scripts/validate_skill.py --strict   # warnings also fail the run
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys

# Shared corpus primitives live in one place; see eval_common.py for why.
from eval_common import (  # noqa: E402  (sys.path is the script's own dir)
    ROOT, SKIP_DIRS, Report, markdown_files, parse_front_matter, read_text, rel,
)
SKILLS_DIR = os.path.join(ROOT, "skills")
REFS_DIR = os.path.join(ROOT, "references")
TEMPLATES_DIR = os.path.join(ROOT, "templates")

REPORT = Report()

MAX_ROOT_SKILL_LINES = 160  # root holds only trigger/classify/route/accept; new knowledge goes to skills/ or references/
MAX_SKILL_LINES = 260
MAX_REFERENCE_LINES = 140
MIN_DESCRIPTION_CHARS = 40

# --- Rule Drift Detection --------------------------------------------------
# Structural checks answer "is the file there?" but not "does this rule exist
# in two versions?". Both P0s in the v1.1.1 review were drift, not gaps:
#   - the root debugging contract still said "no red loop -> stop" while
#     skills/debugging had moved to an explicit evidence ladder
#   - verification restated a risk-list rule that non-negotiables.md owns
#
# Each rule declares its single source and the phrases that, *co-occurring* in
# some other file, mean that file restated the rule. Co-occurrence is the whole
# trick: a pointer ("见 non-negotiables.md 第 2 条") never trips it, only a
# copy does. A single-phrase list means "this exact wording anywhere else is
# drift" — that is how the already-happened-once case below is pinned.
#
# Kept as Python rather than YAML because CI runs this on a bare interpreter
# with no PyYAML; the shape mirrors the YAML spec one-to-one.
CANONICAL_RULES = [
    {
        "name": "剩余风险清单",
        "source": "references/non-negotiables.md",
        "forbidden_duplicates": ["越权 / 未授权访问", "并发竞态", "依赖与供应链"],
    },
    {
        "name": "证据阶梯降级规则",
        "source": "skills/debugging/SKILL.md",
        "forbidden_duplicates": ["无法构建能变红的反馈环"],
        "message": "contradicts the evidence ladder: when L0 is unavailable it "
                   "must degrade explicitly (L1/L2), not stop",
    },
    {
        "name": "安全审查触发条件",
        "source": "references/security.md",
        "forbidden_duplicates": ["默认拒绝", "对象级鉴权", "日志脱敏"],
    },
]

# A worked example exists to *apply* every rule end to end, so naming them is
# its job, not a second source of truth. Evals likewise name concepts in order
# to state expectations.
DRIFT_EXEMPT = {"references/worked-example.md", "evals/README.md"}


def check(ok: bool, label: str, detail: str = "", level: str = "error") -> bool:
    """Record one check result."""
    return REPORT.check(ok, label, detail, level)


def validate_root_skill() -> None:
    path = os.path.join(ROOT, "SKILL.md")
    check(os.path.isfile(path), "root SKILL.md exists")
    if not os.path.isfile(path):
        return
    text = read_text(path)
    fm = parse_front_matter(text)
    check(fm is not None, "root SKILL.md has YAML front-matter")
    if fm:
        check(fm.get("name") == "ai-software-company-skill",
              "root SKILL.md front-matter name", str(fm.get("name")))
        desc = fm.get("description", "")
        check(len(desc) >= MIN_DESCRIPTION_CHARS,
              "root description >= %d chars" % MIN_DESCRIPTION_CHARS, "%d chars" % len(desc))
        check("Use when" in desc, "root description contains 'Use when' trigger")
    for section in ("Skill Routing Table", "Skill 契约", "反模式", "核心信念"):
        check(section in text, "root SKILL.md contains %r" % section)
    lines = text.count("\n") + 1
    check(lines <= MAX_ROOT_SKILL_LINES,
          "root SKILL.md <= %d lines" % MAX_ROOT_SKILL_LINES, "%d lines" % lines, level="warn")


def validate_skills() -> list[str]:
    names = []
    if not os.path.isdir(SKILLS_DIR):
        check(False, "skills/ directory exists")
        return names
    for entry in sorted(os.listdir(SKILLS_DIR)):
        skill_dir = os.path.join(SKILLS_DIR, entry)
        if not os.path.isdir(skill_dir):
            continue
        names.append(entry)
        path = os.path.join(skill_dir, "SKILL.md")
        check(os.path.isfile(path), "skills/%s/SKILL.md exists" % entry)
        if not os.path.isfile(path):
            continue
        text = read_text(path)
        fm = parse_front_matter(text)
        check(fm is not None, "skills/%s has YAML front-matter" % entry)
        if fm:
            check(fm.get("name") == entry,
                  "skills/%s front-matter name matches directory" % entry, str(fm.get("name")))
            desc = fm.get("description", "")
            check(len(desc) >= MIN_DESCRIPTION_CHARS,
                  "skills/%s description >= %d chars" % (entry, MIN_DESCRIPTION_CHARS),
                  "%d chars" % len(desc))
            check("Use when" in desc, "skills/%s description has 'Use when' trigger" % entry)
        check("## 契约" in text, "skills/%s declares its contract (## 契约)" % entry)
        check("失败状态" in text, "skills/%s declares failure states" % entry)
        lines = text.count("\n") + 1
        check(lines <= MAX_SKILL_LINES, "skills/%s <= %d lines" % (entry, MAX_SKILL_LINES),
              "%d lines" % lines, level="warn")
    check(len(names) > 0, "at least one capability skill exists")
    return names


def validate_references() -> None:
    if not os.path.isdir(REFS_DIR):
        check(False, "references/ directory exists")
        return
    for name in sorted(os.listdir(REFS_DIR)):
        if not name.endswith(".md"):
            continue
        path = os.path.join(REFS_DIR, name)
        text = read_text(path)
        fm = parse_front_matter(text)
        check(fm is not None, "references/%s has YAML front-matter" % name)
        if fm:
            check(fm.get("name") == name[:-3],
                  "references/%s front-matter name matches filename" % name, str(fm.get("name")))
            check(len(fm.get("description", "")) > 10,
                  "references/%s has a description" % name)
        lines = text.count("\n") + 1
        check(lines <= MAX_REFERENCE_LINES, "references/%s <= %d lines" % (name, MAX_REFERENCE_LINES),
              "%d lines" % lines, level="warn")


def validate_links(skill_names: list[str]) -> None:
    # lookbehind avoids matching install paths such as ~/.codex/skills/<name>
    pattern = re.compile(r"(?<![\w~/.-])(references|templates|skills)/([A-Za-z0-9_\-]+)(\.md)?")
    for path in markdown_files():
        text = read_text(path)
        for match in pattern.finditer(text):
            kind, target, suffix = match.groups()
            if kind == "skills" and not suffix:
                if target not in skill_names:
                    check(False, "skill reference resolves",
                          "%s -> unknown skill '%s'" % (rel(path), target))
                continue
            candidate = os.path.join(ROOT, kind, target + (suffix or ".md"))
            check(os.path.isfile(candidate), "link resolves",
                  "%s -> %s/%s%s missing" % (rel(path), kind, target, suffix or ".md"))


def validate_root_routes(skill_names: list[str]) -> None:
    path = os.path.join(ROOT, "SKILL.md")
    if not os.path.isfile(path):
        return
    text = read_text(path)
    for name in skill_names:
        check(name in text, "routing table mentions skills/%s" % name)


def validate_metadata() -> None:
    path = os.path.join(ROOT, "ascos.json")
    check(os.path.isfile(path), "ascos.json exists")
    if os.path.isfile(path):
        try:
            data = json.loads(read_text(path))
        except ValueError as exc:
            check(False, "ascos.json is valid JSON", str(exc))
            data = {}
        if data:
            for field in ("name", "version", "entrypoint"):
                check(field in data, "ascos.json has %s" % field)
            check(re.match(r"^\d+\.\d+\.\d+$", str(data.get("version", ""))) is not None,
                  "ascos.json version is semver", str(data.get("version")))
            entry = data.get("entrypoint", "")
            check(os.path.isfile(os.path.join(ROOT, entry)), "ascos.json entrypoint exists", entry)

    yaml_path = os.path.join(ROOT, "agents", "openai.yaml")
    check(os.path.isfile(yaml_path), "agents/openai.yaml exists")
    if os.path.isfile(yaml_path):
        text = read_text(yaml_path)
        for field in ("display_name", "short_description", "allow_implicit_invocation"):
            check(field in text, "agents/openai.yaml has %s" % field)


def validate_templates() -> None:
    check(os.path.isdir(TEMPLATES_DIR), "templates/ directory exists")
    if os.path.isdir(TEMPLATES_DIR):
        names = sorted(os.listdir(TEMPLATES_DIR))
        check(len(names) > 0, "templates/ is not empty")
        for name in names:
            if name.endswith(".md"):
                check(len(read_text(os.path.join(TEMPLATES_DIR, name)).strip()) > 0,
                      "templates/%s is not empty" % name)


def validate_eval_cases() -> None:
    evals_dir = os.path.join(ROOT, "evals")
    check(os.path.isdir(evals_dir), "evals/ directory exists")
    if not os.path.isdir(evals_dir):
        return
    total = 0
    for base, dirs, files in os.walk(evals_dir):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS and d != "runs"]
        for name in files:
            if not name.endswith(".md") or name == "README.md":
                continue
            total += 1
            text = read_text(os.path.join(base, name))
            check("期望路由" in text, "%s declares expected routing" % name)
            check("判定" in text, "%s declares pass/fail criteria" % name)
    check(total >= 20, "at least 20 eval cases exist", "%d found" % total, level="warn")


def validate_duplicate_rules() -> None:
    """Same bullet rule repeated across files usually means a DRY leak."""
    seen: dict[str, set[str]] = {}
    for path in markdown_files():
        if os.path.dirname(path) == TEMPLATES_DIR:
            continue  # templates legitimately echo examples from references
        for line in read_text(path).splitlines():
            stripped = line.strip()
            if stripped.startswith("- ") and len(stripped) >= 24:
                seen.setdefault(stripped, set()).add(rel(path))
    dupes = {text: paths for text, paths in seen.items() if len(paths) > 1}
    check(not dupes, "no duplicated rules across files",
          "; ".join("%r in %s" % (t[:40], sorted(p)) for t, p in list(dupes.items())[:5]),
          level="warn")


def validate_rule_drift() -> None:
    """Catch a rule living in two places, or two versions of the same rule."""
    cache: dict[str, str] = {}

    def body(path: str) -> str:
        if path not in cache:
            cache[path] = read_text(path)
        return cache[path]

    for rule in CANONICAL_RULES:
        source_abs = os.path.abspath(os.path.join(ROOT, rule["source"]))
        if not os.path.isfile(source_abs):
            check(False, "canonical rule %r points at an existing source" % rule["name"],
                  "%s is missing" % rule["source"])
            continue
        offenders = [
            rel(path) for path in markdown_files()
            if os.path.abspath(path) != source_abs
            and rel(path) not in DRIFT_EXEMPT
            and all(marker in body(path) for marker in rule["forbidden_duplicates"])
        ]
        detail = rule.get("message") or "reference the source instead of copying it"
        check(not offenders,
              "%s is the sole source of %r" % (rule["source"], rule["name"]),
              "restated in %s — %s" % (", ".join(offenders), detail))


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate the ASCOS skill package.")
    parser.add_argument("--strict", action="store_true", help="treat warnings as failures")
    args = parser.parse_args()

    validate_root_skill()
    skill_names = validate_skills()
    validate_references()
    validate_links(skill_names)
    validate_root_routes(skill_names)
    validate_metadata()
    validate_templates()
    validate_eval_cases()
    validate_duplicate_rules()
    validate_rule_drift()

    errors = REPORT.errors
    warnings = REPORT.warnings

    print("ASCOS validator — %d checks run" % len(REPORT.checks))
    if errors:
        print("\n✗ Errors (%d):" % len(errors))
        for msg in errors:
            print("  ✗ %s" % msg)
    if warnings:
        print("\n! Warnings (%d):" % len(warnings))
        for msg in warnings:
            print("  ! %s" % msg)
    if not errors and not warnings:
        print("\n✓ All checks passed")

    if errors or (args.strict and warnings):
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
