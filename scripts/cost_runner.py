#!/usr/bin/env python3
"""Stage 2 cost runner: one (case, arm, run) -> one measured record.

What this is for
    The harness ingests and aggregates cost records; it never produces them.
    This produces them by actually running a task through a CLI and reading
    the usage the CLI reports.

What it deliberately does not do
    - It does not grade quality. `defects`, `over_engineering`, `verified` and
      `tests_pass` are human judgements, defined before the run in
      evals/runs/. A machine filling them in would be guessing at the exact
      thing the batch exists to measure.
    - It does not invent numbers. Anything the CLI did not report stays
      absent, and absent is printed as `—` rather than 0 downstream. A zero
      would claim "measured, and it was nothing"; absence says "not measured".

Usage
    python scripts/cost_runner.py run --case E01 --arm with_skill --run 1 \
        --cli claude --model claude-haiku-4-5 --out runs.jsonl
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys

from eval_common import ROOT, read_text, rel  # noqa: E402

FIXTURES = os.path.join(ROOT, "eval-fixtures")
SKILLS_DIR = os.path.join(ROOT, "skills")
REFERENCES_DIR = os.path.join(ROOT, "references")

# Where each CLI looks for project-scoped skills. Arm isolation works by
# copying ASCOS here for the `with_skill` arm and leaving it absent for
# `without_skill` — the only difference between arms must be discoverability.
CLI_SKILL_SUBDIR = {"claude": os.path.join(".claude", "skills"),
                    "codex": os.path.join(".codex", "skills")}

# The shell tool is named differently per platform, and a spec against the
# wrong name is silently ignored rather than rejected.
SHELL_TOOL = "PowerShell" if os.name == "nt" else "Bash"
# The whole shell, and why it has to be: a narrow allowlist (node/npm only)
# denied 48 commands on the with_skill arm against 2 on the control — 24x
# asymmetric, every one of them landing on the arm under test. ASCOS's
# verification discipline is exactly what reaches for git, directory listings
# and throw-away check scripts, so a narrow allowlist taxes the behaviour this
# stage is trying to measure. The cost is not symmetric, so it is not noise.
# The workspace is a disposable copy of a fixture, which is what makes this
# acceptable at all.
SHELL_PREFIXES = ("*",)


def parse_events(text: str) -> list[dict]:
    """Events from a JSONL stream; unparseable lines are skipped, not fatal."""
    events = []
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            events.append(json.loads(line))
        except ValueError:
            continue
    return events


def _tool_uses(events: list[dict]) -> list[dict]:
    """Every tool_use block, in order, across all assistant messages."""
    blocks = []
    for event in events:
        message = event.get("message")
        if not isinstance(message, dict):
            continue
        content = message.get("content")
        # Some events carry content as a plain string rather than a block
        # list; only the list form can hold tool_use.
        if not isinstance(content, list):
            continue
        for block in content:
            if isinstance(block, dict) and block.get("type") == "tool_use":
                blocks.append(block)
    return blocks


def _observed_models(events: list[dict]) -> str | None:
    """The model theCLI actually served, not the one we asked for.

    Recorded because asking is not the same as getting: `--model haiku` was
    remapped to `deepseek-v4-flash` by a local relay, and a batch that does not
    write down which model answered cannot be reproduced. If a run somehow
    served more than one, all of them are joined so the inconsistency is
    visible rather than silently averaged away.
    """
    seen = sorted({e["message"].get("model")
                   for e in events
                   if isinstance(e.get("message"), dict)
                   and e["message"].get("model")})
    return ",".join(seen) if seen else None


def _skill_invocations(tools: list[dict]) -> list[str]:
    """Skills the run invoked through the Skill tool.

    Needed because a skill loaded this way never shows up as a file read: the
    pilot's small case invoked `Skill {"skill": "ascos"}` and still reported an
    empty `skills_loaded`. Counting only reads makes activation systematically
    under-reported, which is the one signal this whole batch exists to measure.
    """
    return sorted({name for name in ((b.get("input") or {}).get("skill")
                                     for b in tools
                                     if b.get("name") == "Skill") if name})


ERROR_MARKS = ("api error", "insufficient", "rate limit", "overloaded",
               "quota", "unauthorized", " 401", " 402", " 403", " 429", " 500")


def _stream_error(events: list[dict]) -> str | None:
    """The real reason a run produced nothing, read out of the stream itself.

    An exhausted balance came back as exit 1 with empty stderr while the actual
    message sat in the assistant turn. Without this the note reads "exit 1",
    which explains nothing and invites re-running a batch that cannot succeed
    for a reason no amount of retrying will fix.
    """
    for e in events:
        m = e.get("message")
        if not isinstance(m, dict):
            continue
        c = m.get("content")
        if isinstance(c, list):
            for b in c:
                if isinstance(b, dict) and isinstance(b.get("text"), str):
                    text = b["text"].strip()
                    if any(mark in text.lower() for mark in ERROR_MARKS):
                        return text[:160]
    return None


def summarise_claude(events: list[dict]) -> dict:
    """Usage from a `claude -p --output-format stream-json` stream."""
    result = next((e for e in events if e.get("type") == "result"), None)
    if result is None:
        err = _stream_error(events)
        return {"note": "no result event — the run did not complete"
                        + (": " + err if err else "")}
    usage = result.get("usage") or {}
    inc = usage.get("input_tokens")
    out = usage.get("output_tokens")
    total = usage.get("total_tokens") or (
        (inc + out) if isinstance(inc, int) and isinstance(out, int) else None)
    duration = result.get("duration_ms")
    tools = _tool_uses(events)
    if not total:
        # A run can exit 0-shaped and still have measured nothing; the reason
        # is in the stream, not in the exit code.
        err = _stream_error(events)
        return {"note": "no token usage in the result event"
                        + (": " + err if err else "")}
    return {
        "input_tokens": inc,
        "output_tokens": out,
        "total_tokens": total,
        "seconds": None if duration is None else round(duration / 1000.0, 2),
        "tool_calls": len(tools),
        # Only real Read calls count as "loaded". Taking every tool input with
        # a `file_path` also swept in Write/Edit targets, and tools like Grep
        # use `path` instead, which yielded None entries.
        "files_read": [path for path in
                       ((b.get("input") or {}).get("file_path")
                        for b in tools if b.get("name") == "Read"
                        and isinstance(b.get("input"), dict)) if path],
    }


def summarise_codex(events: list[dict]) -> dict:
    """Usage from a `codex exec --json` stream.

    Written against the event names Codex documents, but NOTE: no successful
    Codex run has been observed on this machine yet (the local relay reports
    an empty model list), so this parser is unverified. It fails loudly
    instead of returning zeros, which is the only honest thing an unverified
    parser can do.
    """
    for event in events:
        info = event.get("info") or {}
        usage = info.get("total_token_usage") or info.get("last_token_usage")
        if not usage:
            continue
        inc = usage.get("input_tokens")
        out = usage.get("output_tokens")
        total = usage.get("total_tokens") or (
            (inc + out) if isinstance(inc, int) and isinstance(out, int) else None)
        return {
            "input_tokens": inc,
            "output_tokens": out,
            "total_tokens": total,
            "seconds": None,
            "tool_calls": None,
            "files_read": [],
            "note": "parsed from token_count; seconds and tool_calls are not "
                    "reported by this event and stay unmeasured",
        }
    return {"note": "no token usage event found — cannot measure this run"}


SUMMARISERS = {"claude": summarise_claude, "codex": summarise_codex}


def classify_paths(paths: list[str]) -> tuple[list[str], list[str]]:
    """Split observed file reads into skills and references.

    Observing beats self-reporting: a model asked which files it loaded will
    answer from its own narrative, and in stage 1 nine batched runs all
    reported having loaded the skill because the first one in the session had.
    """
    skills: list[str] = []
    references: list[str] = []
    for path in paths:
        if not isinstance(path, str):
            continue
        norm = path.replace("\\", "/")
        # Whichever marker sits further right wins. A path like
        # `<ws>/.claude/skills/ascos/references/testing.md` contains both, and
        # taking /skills/ first would file the reference under the skill name.
        skill_at = norm.rfind("/skills/")
        ref_at = norm.rfind("/references/")
        if ref_at > skill_at:
            name = norm[ref_at + len("/references/"):].split("/")[0]
            if name and name not in references:
                references.append(name)
        elif skill_at != -1:
            name = norm[skill_at + len("/skills/"):].split("/")[0]
            if name and name not in skills:
                skills.append(name)
    return skills, references


def prepare_workspace(dest: str, workspace: str, arm: str, cli: str) -> None:
    """A fresh copy per run: a fixture already edited is not the same task."""
    if os.path.isdir(dest):
        shutil.rmtree(dest)
    os.makedirs(dest)
    # E13 builds from nothing, so it gets no fixture — but it must still get
    # the skill on the `with_skill` arm. Returning early here once made both
    # arms identical for that case, which is a pair of runs that cannot
    # differ and therefore cannot measure anything.
    if workspace != "empty":
        # Fixture is chosen by name: E10 needs documents to answer questions
        # over, and cost-app has none, so it gets its own.
        source = os.path.join(FIXTURES, workspace)
        if not os.path.isdir(source):
            raise SystemExit("unknown fixture %r (looked in %s)"
                             % (workspace, FIXTURES))
        shutil.copytree(source, dest, dirs_exist_ok=True)
    if arm == "with_skill":
        # Copy the skill package, not the repository. The default output
        # directory lives inside ROOT, so copying ROOT there would copy the
        # repo into a subdirectory of itself.
        target = os.path.join(dest, CLI_SKILL_SUBDIR[cli], "ascos")
        os.makedirs(target, exist_ok=True)
        for item in ("SKILL.md", "skills", "references", "templates"):
            source = os.path.join(ROOT, item)
            if os.path.isfile(source):
                shutil.copy2(source, os.path.join(target, item))
            elif os.path.isdir(source):
                shutil.copytree(source, os.path.join(target, item),
                                ignore=shutil.ignore_patterns("__pycache__"))


def resolve_bin(cli: str, override: str | None) -> str:
    """Locate the CLI executable.

    npm installs a `.cmd` shim on Windows and Python's subprocess does not
    resolve that on its own, which is why `which` succeeds from a shell while
    `subprocess.run(["claude", ...])` raises FileNotFoundError.
    """
    if override:
        return override
    for name in ((cli, cli + ".cmd") if os.name == "nt" else (cli,)):
        found = shutil.which(name)
        if found:
            return found
    raise SystemExit("cannot find %r on PATH; pass --bin <path>" % cli)


def build_command(cli: str, prompt: str, model: str | None, bin_path: str) -> list[str]:
    if cli == "claude":
        # WebSearch is banned: its results change with the calendar, which
        # makes a run unrepeatable, and it adds tokens that have nothing to do
        # with what is being measured. The pilot hit it on a large case.
        # acceptEdits is the least that lets a run deliver anything: without it
        # every Edit/Write waits for an approval nobody can give, and the batch
        # measures planning instead of work.
        cmd = [bin_path, "-p", prompt, "--output-format", "stream-json",
               "--verbose", "--disallowedTools", "WebSearch",
               "--permission-mode", "acceptEdits"]
        # On top of that, the shell is opened: ASCOS's verification step runs
        # commands and writes scripts, and with the shell closed that cost is
        # paid while the benefit never arrives.
        #
        # The tool is PowerShell on Windows and Bash elsewhere — verified, not
        # assumed: every Bash(...) spec was silently a no-op here, which is why
        # command execution looked completely blocked.
        for prefix in SHELL_PREFIXES:
            # "*" means the whole tool, and the pattern for that is `Tool(*)`,
            # not `Tool(*:*)` — the `:*` form is a command prefix.
            spec = "%s(*)" % SHELL_TOOL if prefix == "*" else "%s(%s:*)" % (SHELL_TOOL, prefix)
            cmd += ["--allowedTools", spec]
        if model:
            cmd += ["--model", model]
        return cmd
    cmd = [bin_path, "exec", "--json", "--ephemeral", "--skip-git-repo-check",
           "-s", "workspace-write", prompt]
    if model:
        cmd += ["-m", model]
    return cmd


def _tail(text: str | None, limit: int = 200) -> str:
    """Last `limit` chars of captured output — a note must stay short but still
    show what the run was doing when it died."""
    if not text:
        return ""
    return text.strip()[-limit:]


def run_one(case: dict, arm: str, run: int, cli: str, model: str | None,
            workspace: str, out_dir: str, timeout: int = 900,
            bin_path: str | None = None) -> dict:
    """Run a single (case, arm, run) and return its record."""
    label = "%s-%s-%d" % (case["id"], arm, run)
    dest = os.path.join(out_dir, "ws", label)
    prepare_workspace(dest, workspace, arm, cli)

    cmd = build_command(cli, case["prompt"], model, resolve_bin(cli, bin_path))
    try:
        # stdin=DEVNULL matters: `codex exec` reads stdin when it thinks the
        # prompt is missing, and subprocess inherits ours by default. One run
        # that blocks on a terminal would stall the whole batch.
        proc = subprocess.run(cmd, cwd=dest, capture_output=True, text=True,
                              encoding="utf-8", errors="replace",
                              timeout=timeout, stdin=subprocess.DEVNULL)
    except subprocess.TimeoutExpired as exc:
        # One hung run must not take the batch down with it: 72 runs is long
        # enough that a single timeout would otherwise cost everything before
        # it. It is an unmeasured run, not a failed one, so it stays empty.
        return {"case": case["id"], "variant": arm, "run": run,
                "verdict": "invalid", "input_tokens": None,
                "output_tokens": None, "total_tokens": None, "seconds": None,
                "tool_calls": None, "skills_loaded": [],
                "references_loaded": [],
                "note": "timeout after %ds: %s" % (timeout, _tail(exc.stdout))}
    events = parse_events(proc.stdout)

    raw_dir = os.path.join(out_dir, "events")
    os.makedirs(raw_dir, exist_ok=True)
    with open(os.path.join(raw_dir, label + ".jsonl"), "w",
              encoding="utf-8", newline="\n") as fh:
        fh.write(proc.stdout)

    return build_record(case, arm, run, cli, events, proc.returncode,
                        proc.stderr)


def build_record(case: dict, arm: str, run: int, cli: str, events: list[dict],
                 returncode: int = 0, stderr: str = "") -> dict:
    """Turn a captured event stream into a cost record.

    Split out of `run_one` so a stream can be re-summarised without paying for
    the run again: the raw events are the evidence and the record is only a
    view over them. Used to recover records after `cmd_run` was fixed to stop
    overwriting the batch file.
    """
    summary = SUMMARISERS[cli](events)
    skills, references = classify_paths(summary.get("files_read") or [])
    skills = sorted(set(skills) | set(_skill_invocations(_tool_uses(events))))

    record = {
        "case": case["id"],
        "variant": arm,
        "run": run,
        "model": _observed_models(events),
        "verdict": "pass" if returncode == 0 else "invalid",
        "input_tokens": summary.get("input_tokens"),
        "output_tokens": summary.get("output_tokens"),
        "total_tokens": summary.get("total_tokens"),
        "seconds": summary.get("seconds"),
        "tool_calls": summary.get("tool_calls"),
        "skills_loaded": skills,
        "references_loaded": references,
        # Basenames only. The absolute paths are machine-specific and long,
        # and what this is for is attribution — which files a run actually
        # opened, as opposed to which skills it merely declared.
        "files_read": sorted({os.path.basename(p)
                              for p in summary.get("files_read") or []}),
    }
    if returncode != 0:
        # An invalid run has to say why, or "invalid" becomes a drawer to
        # sweep inconvenient results into. Lead with the CLI's own failure:
        # "no result event" is only a consequence, the cause is in stderr, and
        # an audit months later needs to tell auth from rate limit from crash.
        detail = (stderr or "").strip()[:200]
        record["note"] = "exit %d" % returncode
        if detail:
            record["note"] += ": " + detail
        if summary.get("note"):
            record["note"] += " | " + summary["note"]
    elif summary.get("note"):
        record["note"] = summary["note"]
    return record


def load_batch(manifest_path: str, cases: list[dict]) -> list[dict]:
    """Join the cost manifest with the corpus so each entry has a prompt."""
    with open(manifest_path, encoding="utf-8") as fh:
        manifest = json.load(fh)
    by_id = {c["id"]: c for c in cases if c.get("id")}
    out = []
    for entry in manifest.get("cases", []):
        case = by_id.get(entry["id"])
        if not case:
            raise SystemExit("manifest references unknown case %r" % entry["id"])
        out.append({"id": entry["id"], "bucket": entry["bucket"],
                    "workspace": entry.get("workspace", "cost-app"),
                    "prompt": case_prompt(case)})
    return out


def case_prompt(case: dict) -> str:
    from eval_harness import case_prompt as _prompt  # local: avoids a cycle
    return _prompt(case)


def _read_records(path: str) -> dict:
    """Existing records keyed on (case, variant, run).

    Keyed rather than appended so re-running one case replaces its record
    instead of duplicating it, and so driving a batch one case at a time — the
    natural way to use this — accumulates instead of discarding. Writing the
    file outright is how the first pilot lost two of its four records.
    """
    merged = {}
    if os.path.exists(path):
        with open(path, encoding="utf-8") as fh:
            for line in fh:
                if line.strip():
                    old = json.loads(line)
                    merged[(old["case"], old["variant"], old["run"])] = old
    return merged


def _write_records(path: str, merged: dict) -> None:
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        for key in sorted(merged):
            fh.write(json.dumps(merged[key], ensure_ascii=False,
                                sort_keys=True) + "\n")


def cmd_run(args) -> int:
    from eval_harness import load_cases
    batch = load_batch(args.manifest, load_cases())
    selected = [c for c in batch
                if (not args.case or c["id"] == args.case)
                and (not args.bucket or c["bucket"] == args.bucket)]
    if not selected:
        print("no case matched", file=sys.stderr)
        return 1

    path = os.path.join(args.out_dir, "cost-runs.jsonl")
    os.makedirs(args.out_dir, exist_ok=True)

    def persist(rec):
        """Write through after every run.

        A full batch takes hours. Buffering until the end means one
        interruption discards everything, and the expensive part is the runs,
        not the writing.
        """
        merged = _read_records(path)
        merged[(rec["case"], rec["variant"], rec["run"])] = rec
        _write_records(path, merged)

    total = 0
    for case in selected:
        for arm in args.arm:
            for run in range(1, args.runs + 1):
                rec = run_one(case, arm, run, args.cli, args.model,
                              case["workspace"], args.out_dir, args.timeout,
                              args.bin)
                total += 1
                persist(rec)
                print("%s %s run%d -> %s | in=%s out=%s tools=%s skills=%s"
                      % (case["id"], arm, run, rec["verdict"],
                         rec["input_tokens"], rec["output_tokens"],
                         rec["tool_calls"], rec["skills_loaded"]))

    print("\n%d record(s) in %s (%d from this invocation)"
          % (len(_read_records(path)), rel(path), total))
    print("next: python scripts/eval_harness.py ingest --cost --file %s" % rel(path))
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = ap.add_subparsers(dest="command", required=True)

    p = sub.add_parser("run", help="run cases and emit cost records")
    p.add_argument("--manifest", default=os.path.join(ROOT, "evals", "cost",
                                                      "manifest.json"))
    p.add_argument("--case", help="a single case id, e.g. E01")
    p.add_argument("--bucket", choices=("small", "medium", "large"))
    p.add_argument("--arm", nargs="+", choices=("with_skill", "without_skill"),
                   default=["with_skill", "without_skill"])
    p.add_argument("--runs", type=int, default=1)
    p.add_argument("--cli", choices=sorted(SUMMARISERS), default="claude")
    p.add_argument("--model", help="pin the model; required for comparability")
    p.add_argument("--out-dir", default=os.path.join(ROOT, "evals", "cost",
                                                     "results", "raw"))
    p.add_argument("--timeout", type=int, default=900)
    p.add_argument("--bin", help="path to the CLI executable (auto-detected, "
                                 "including the npm .cmd shim on Windows)")
    p.set_defaults(func=cmd_run)

    args = ap.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
