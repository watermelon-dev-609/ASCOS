#!/usr/bin/env python3
"""Shared primitives for the ASCOS tooling.

Two consumers justified extracting this: `validate_skill.py` (structure lint)
and `eval_harness.py` (behaviour evals) both need to walk the same markdown
corpus and read the same front-matter. Keeping one copy is what stops the two
tools from drifting apart on what counts as an eval case.

Stdlib only — the whole toolchain must run on a bare Python with no install.
"""

from __future__ import annotations

import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

SKIP_DIR_PREFIXES = (".", "__")  # dot-dirs (.git, .workbuddy*) and dunder dirs are never skill content
# eval-fixtures/ holds deliberately broken test data; linting it as documentation
# would produce false positives (missing links, duplicated rule-like lines).
SKIP_DIRS = {"node_modules", "eval-fixtures", "results"}

EVALS_DIR = os.path.join(ROOT, "evals")
RESULTS_DIR = os.path.join(EVALS_DIR, "results")
# Generated artefacts, not authored content: observed run logs and the
# aggregated report. Neither is a spec, so neither is linted as one.
EVAL_AUX_DIRS = {"runs", "results"}

# Front-matter keys every eval case must declare so the harness can aggregate.
REQUIRED_CASE_KEYS = ("id", "group", "expect")


class Report:
    """Collects check results so callers decide how strict to be."""

    def __init__(self) -> None:
        self.checks: list[str] = []
        self.findings: list[tuple[str, str]] = []  # (level, message); level in {error, warn}

    def check(self, ok: bool, label: str, detail: str = "", level: str = "error") -> bool:
        self.checks.append(label)
        if not ok:
            self.findings.append((level, "%s%s" % (label, (" — " + detail) if detail else "")))
        return ok

    @property
    def errors(self) -> list[str]:
        return [msg for level, msg in self.findings if level == "error"]

    @property
    def warnings(self) -> list[str]:
        return [msg for level, msg in self.findings if level == "warn"]


def read_text(path: str) -> str:
    with open(path, encoding="utf-8") as fh:
        return fh.read()


def parse_front_matter(text: str) -> dict | None:
    """Parse the flat YAML front-matter used across this repo.

    Supports two shapes and nothing else — this is not a YAML parser:

        key: value
        key:
          - item one
          - item two
    """
    if not text.startswith("---\n"):
        return None
    end = text.find("\n---\n", 4)
    if end == -1:
        return None
    data: dict = {}
    current_list: list[str] | None = None
    for line in text[4:end].splitlines():
        if current_list is not None:
            item = re.match(r"^\s+-\s+(.*)$", line)
            if item:
                current_list.append(item.group(1).strip().strip('"').strip("'"))
                continue
            current_list = None
        match = re.match(r"^([A-Za-z_][A-Za-z0-9_]*):\s*(.*)$", line)
        if not match:
            continue
        key, raw = match.group(1), match.group(2).strip()
        if raw == "":
            current_list = []
            data[key] = current_list
        else:
            data[key] = raw.strip('"').strip("'")
    return data


def markdown_files() -> list[str]:
    """Every markdown file that counts as package content, sorted."""
    found = []
    for base, dirs, files in os.walk(ROOT):
        dirs[:] = [d for d in dirs
                   if d not in SKIP_DIRS and not d.startswith(SKIP_DIR_PREFIXES)]
        for name in files:
            if name.endswith(".md"):
                found.append(os.path.join(base, name))
    return sorted(found)


def markdown_files_under(directory: str) -> list[str]:
    for base, dirs, files in os.walk(directory):
        dirs[:] = [d for d in dirs if not d.startswith(SKIP_DIR_PREFIXES)]
        for name in sorted(files):
            if name.endswith(".md") and name != "README.md":
                yield os.path.join(base, name)


def rel(path: str) -> str:
    return os.path.relpath(path, ROOT).replace("\\", "/")


def _eval_case_files() -> list[str]:
    """Authored case files only — `runs/` and `results/` are generated."""
    found: list[str] = []
    for base, dirs, files in os.walk(EVALS_DIR):
        dirs[:] = [d for d in dirs if d not in EVAL_AUX_DIRS and not d.startswith(SKIP_DIR_PREFIXES)]
        for name in sorted(files):
            if name.endswith(".md") and name != "README.md":
                found.append(os.path.join(base, name))
    return sorted(found)


def load_cases() -> list[dict]:
    """Load every eval case (front-matter + path + body)."""
    cases: list[dict] = []
    if not os.path.isdir(EVALS_DIR):
        return cases
    for path in _eval_case_files():
        text = read_text(path)
        meta = parse_front_matter(text) or {}
        body = text.split("\n---\n", 2)[-1] if text.startswith("---\n") else text
        meta["_path"] = path
        meta["_rel"] = rel(path)
        meta["_body"] = body
        cases.append(meta)
    return sorted(cases, key=lambda c: str(c.get("id", c["_rel"])))
