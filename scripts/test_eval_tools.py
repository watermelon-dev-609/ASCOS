#!/usr/bin/env python3
"""Tests for the eval harness and its shared primitives.

Stdlib only, the same constraint as the scripts under test: CI has no PyYAML
and must not need it. Run with `python scripts/test_eval_tools.py`.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
import unittest.mock

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import eval_common  # noqa: E402
from eval_common import read_text  # noqa: E402
import cost_runner  # noqa: E402
import eval_harness  # noqa: E402

def trigger_case(cid, expect):
    return [{"id": cid, "group": "trigger", "expect": expect,
             "_rel": "evals/triggers/%s.md" % cid.lower()}]


MUST_NOT_FIRE = trigger_case("T11", "not_fire")
MUST_FIRE = trigger_case("T01", "fire")
T13 = trigger_case("T13", "not_fire")
T05 = trigger_case("T05", "fire")


def check(records, cases):
    """Run records_check over a fabricated record set."""
    report = eval_common.Report()
    original = eval_harness.load_records
    eval_harness.load_records = lambda: records
    try:
        eval_harness.records_check(report, cases)
    finally:
        eval_harness.load_records = original
    return report


class PassAtKTests(unittest.TestCase):
    def test_blank_when_fewer_runs_than_k(self):
        self.assertIsNone(eval_harness.pass_at_k(2, 2, 3))

    def test_all_pass_gives_one(self):
        self.assertAlmostEqual(eval_harness.pass_at_k(3, 3, 1), 1.0)

    def test_none_pass_gives_zero(self):
        self.assertAlmostEqual(eval_harness.pass_at_k(3, 0, 1), 0.0)

    def test_single_draw_is_the_hit_rate(self):
        self.assertAlmostEqual(eval_harness.pass_at_k(3, 1, 1), 1 / 3)

    def test_every_draw_succeeds_when_too_few_failures(self):
        self.assertAlmostEqual(eval_harness.pass_at_k(3, 2, 3), 1.0)

    def test_comb_is_integer_exact(self):
        self.assertEqual(eval_harness._comb(10, 5), 252)
        self.assertEqual(eval_harness._comb(4, 0), 1)
        self.assertEqual(eval_harness._comb(2, 5), 0)


class FrontMatterTests(unittest.TestCase):
    def test_body_keeps_its_horizontal_rules(self):
        text = "---\nid: T99\n---\n\n# T99\n\n## 输入\nA\n\n---\n\n## 判定\nB\n"
        meta, body = eval_common.split_front_matter(text)
        self.assertEqual(meta.get("id"), "T99")
        self.assertIn("## 判定", body)

    def test_missing_front_matter_returns_intact_body(self):
        text = "# no front matter\n\n---\n\nbody\n"
        meta, body = eval_common.split_front_matter(text)
        self.assertIsNone(meta)
        self.assertEqual(body, text)

    def test_nested_list_items_are_parsed(self):
        meta = eval_common.parse_front_matter(
            "---\nid: T01\nevidence:\n  - a\n  - b\n---\n")
        self.assertEqual(meta.get("evidence"), ["a", "b"])


class PromptExportTests(unittest.TestCase):
    def test_grader_notes_are_stripped(self):
        case = {"_body": "# T99\n\n## 输入\nreal input\n> use fixture X\n",
                "_rel": "evals/triggers/99.md", "id": "T99"}
        prompt = eval_harness.case_prompt(case)
        self.assertIn("real input", prompt)
        self.assertNotIn("fixture", prompt)

    def test_missing_input_section_emits_nothing(self):
        case = {"_body": "# T99\n\nno input here\n", "_rel": "x.md", "id": "T99"}
        self.assertEqual(eval_harness.case_prompt(case), "")


class MisfireShapeTests(unittest.TestCase):
    def test_shape_is_required_on_must_not_fire(self):
        report = check([{"case": "T11", "variant": "with_skill", "run": 1,
                         "verdict": "not_fire"}], MUST_NOT_FIRE)
        self.assertTrue(report.errors)

    def test_fire_with_none_shape_is_rejected(self):
        report = check([{"case": "T11", "variant": "with_skill", "run": 1,
                         "verdict": "fire", "misfire_shape": "none"}], MUST_NOT_FIRE)
        self.assertTrue(report.errors)

    def test_not_fire_with_a_real_shape_is_rejected(self):
        report = check([{"case": "T11", "variant": "with_skill", "run": 1,
                         "verdict": "not_fire",
                         "misfire_shape": "risk-tail"}], MUST_NOT_FIRE)
        self.assertTrue(report.errors)

    def test_unknown_shape_is_rejected(self):
        report = check([{"case": "T11", "variant": "with_skill", "run": 1,
                         "verdict": "not_fire", "misfire_shape": "banana"}],
                       MUST_NOT_FIRE)
        self.assertTrue(report.errors)

    def test_must_fire_cases_carry_no_shape(self):
        report = check([{"case": "T01", "variant": "with_skill", "run": 1,
                         "verdict": "fire", "misfire_shape": "risk-tail"}], MUST_FIRE)
        self.assertTrue(report.errors)

    def test_clean_record_passes(self):
        report = check([{"case": "T11", "variant": "with_skill", "run": 1,
                         "verdict": "not_fire", "misfire_shape": "none"}],
                       MUST_NOT_FIRE)
        self.assertFalse(report.errors)


class InvalidRunTests(unittest.TestCase):
    """An invalid run measured the environment, not the skill, so it must not
    reach any denominator — and it must say why, or "invalid" becomes a drawer
    to sweep inconvenient results into."""

    def test_invalid_without_a_reason_is_rejected(self):
        report = check([{"case": "T05", "variant": "with_skill", "run": 1,
                         "verdict": "invalid"}], T05)
        self.assertTrue(report.errors)

    def test_invalid_with_a_reason_is_accepted(self):
        report = check([{"case": "T05", "variant": "with_skill", "run": 1,
                         "verdict": "invalid",
                         "note": "weixinpay connector hijacked the request"}], T05)
        self.assertFalse(report.errors)

    def test_invalid_carries_no_shape(self):
        report = check([{"case": "T11", "variant": "with_skill", "run": 1,
                         "verdict": "invalid", "note": "environment",
                         "misfire_shape": "risk-tail"}], MUST_NOT_FIRE)
        self.assertTrue(report.errors)

    def test_invalid_is_excluded_from_the_hit_rate(self):
        section = eval_harness._misfire_section(
            {}, {"T11": {"with_skill": [
                {"case": "T11", "variant": "with_skill", "run": 1,
                 "verdict": "invalid", "note": "env"}]}})
        self.assertEqual(section, [])


class ObservationTagTests(unittest.TestCase):
    """Saying why you will NOT trigger is the routing decision being legible.
    It is the opposite of a misfire, so it must live outside misfire_shape."""

    def test_negative_routing_is_a_known_tag(self):
        self.assertIn("negative-routing", eval_harness.OBSERVATIONS)

    def test_known_tag_is_accepted(self):
        report = check([{"case": "T13", "variant": "with_skill", "run": 1,
                         "verdict": "not_fire", "misfire_shape": "none",
                         "observation": "negative-routing"}], T13)
        self.assertFalse(report.errors)

    def test_unknown_tag_is_rejected(self):
        report = check([{"case": "T13", "variant": "with_skill", "run": 1,
                         "verdict": "not_fire", "misfire_shape": "none",
                         "observation": "felt-like-it"}], T13)
        self.assertTrue(report.errors)

    def test_observations_are_reported_separately_from_misfires(self):
        by_case = {"T13": {"with_skill": [
            {"case": "T13", "variant": "with_skill", "run": 1,
             "verdict": "not_fire", "misfire_shape": "none",
             "observation": "negative-routing"}]}}
        cases = {"T13": {"expect": "not_fire"}}
        self.assertEqual(eval_harness._misfire_section(cases, by_case)[-2:],
                         ["No misfire recorded in this batch.", ""])
        joined = "\n".join(eval_harness._observation_section(by_case))
        self.assertIn("negative-routing", joined)
        self.assertNotIn("misfire", joined.lower().replace("misfires", ""))


class LoadedFieldTests(unittest.TestCase):
    """`loaded` records whether the run opened SKILL.md.

    Rubric revisions keep moving "does this answer look like activation";
    "did the run open the file" does not, so it is the safety signal that
    stays comparable across rounds.
    """

    def test_yes_and_no_are_the_only_values(self):
        self.assertEqual(sorted(eval_harness.LOADED), ["no", "yes"])

    def test_known_value_is_accepted(self):
        report = check([{"case": "T13", "variant": "with_skill", "run": 1,
                         "verdict": "not_fire", "misfire_shape": "none",
                         "loaded": "no"}], T13)
        self.assertFalse(report.errors)

    def test_unknown_value_is_rejected(self):
        report = check([{"case": "T13", "variant": "with_skill", "run": 1,
                         "verdict": "not_fire", "misfire_shape": "none",
                         "loaded": "maybe"}], T13)
        self.assertTrue(report.errors)

    def test_section_stays_empty_when_nobody_recorded_it(self):
        by_case = {"T13": {"with_skill": [
            {"case": "T13", "variant": "with_skill", "run": 1,
             "verdict": "not_fire", "misfire_shape": "none"}]}}
        self.assertEqual(eval_harness._loaded_section({"T13": {"expect": "not_fire"}},
                                                      by_case), [])

    def test_section_groups_by_expectation_so_the_safety_half_is_visible(self):
        by_case = {"T13": {"with_skill": [
            {"case": "T13", "variant": "with_skill", "run": 1,
             "verdict": "not_fire", "misfire_shape": "none", "loaded": "yes"}]}}
        joined = "\n".join(eval_harness._loaded_section(
            {"T13": {"expect": "not_fire"}}, by_case))
        self.assertIn("not_fire", joined)
        self.assertIn("| 1 |", joined)


class VerdictTypeTests(unittest.TestCase):
    def test_trigger_verdicts_on_trigger_case(self):
        report = check([{"case": "T01", "variant": "with_skill", "run": 1,
                         "verdict": "pass"}], MUST_FIRE)
        self.assertTrue(report.errors)

    def test_behaviour_verdict_rejected_on_trigger_case(self):
        report = check([{"case": "T01", "variant": "with_skill", "run": 1,
                         "verdict": "fire"}], MUST_FIRE)
        self.assertFalse(report.errors)


class CostRecordTests(unittest.TestCase):
    """Stage 2 field contract.

    Written after the cost block was found broken and unrunnable (a stray quote
    in QUALITY_FLAGS), which is the whole reason this suite exists: an
    aggregator that has never executed is not a measurement, it is a guess
    with a command line.
    """

    CASES = [{"id": "E01", "group": "small", "expect": "pass"},
             {"id": "E10", "group": "large", "expect": "pass"}]

    def cost_check(self, records, manifest=None):
        report = eval_common.Report()
        original = eval_harness.load_cost_records
        eval_harness.load_cost_records = lambda: records
        try:
            eval_harness.cost_records_check(report, self.CASES)
        finally:
            eval_harness.load_cost_records = original
        return report

    def rec(self, **kw):
        base = {"case": "E01", "variant": "with_skill", "run": 1, "verdict": "pass"}
        base.update(kw)
        return base

    # --- the contract accepts what it should ---------------------------

    def test_minimal_record_is_well_formed(self):
        self.assertEqual(eval_harness.cost_errors(self.rec()), [])

    def test_full_record_is_well_formed(self):
        self.assertEqual(eval_harness.cost_errors(self.rec(
            input_tokens=9000, output_tokens=1200, total_tokens=10200,
            seconds=41.5, tool_calls=7,
            skills_loaded=["implementation"], references_loaded=["testing.md"],
            defects={"bugs": 1, "security": 0},
            over_engineering=False, verified=True, tests_pass=True,
            stages=[{"stage": "implementation", "tokens": 4000}])), [])

    def test_missing_fields_are_allowed_not_faked(self):
        """Unmeasured stays absent; the report prints — rather than 0."""
        self.assertEqual(eval_harness.cost_errors(self.rec(seconds=None)), [])

    # --- reverse verification: broken data must be rejected ------------

    def test_negative_token_count_is_rejected(self):
        self.assertTrue(eval_harness.cost_errors(self.rec(input_tokens=-1)))

    def test_boolean_is_rejected_as_a_number(self):
        """bool is a subclass of int, so it must be excluded explicitly."""
        self.assertTrue(eval_harness.cost_errors(self.rec(tool_calls=True)))

    def test_string_is_rejected_as_a_number(self):
        self.assertTrue(eval_harness.cost_errors(self.rec(seconds="41")))

    def test_loaded_lists_must_be_lists_of_strings(self):
        self.assertTrue(eval_harness.cost_errors(self.rec(skills_loaded="implementation")))
        self.assertTrue(eval_harness.cost_errors(self.rec(references_loaded=[1, 2])))

    def test_unknown_defect_key_is_rejected(self):
        self.assertTrue(eval_harness.cost_errors(self.rec(defects={"typo": 1})))

    def test_negative_defect_count_is_rejected(self):
        self.assertTrue(eval_harness.cost_errors(self.rec(defects={"bugs": -1})))

    def test_stage_trace_needs_both_fields(self):
        self.assertTrue(eval_harness.cost_errors(
            self.rec(stages=[{"stage": "implementation"}])))
        self.assertTrue(eval_harness.cost_errors(self.rec(stages=[{"tokens": 1}])))

    def test_checker_surfaces_a_malformed_record_as_an_error(self):
        report = self.cost_check([self.rec(input_tokens=-5)])
        self.assertTrue(report.errors)

    def test_checker_rejects_an_unknown_case(self):
        report = self.cost_check([self.rec(case="E99")])
        self.assertTrue(report.errors)

    def test_checker_rejects_a_variant_outside_the_three_arms(self):
        report = self.cost_check([self.rec(variant="with_skill_v3")])
        self.assertTrue(report.errors)

    # --- quality index -------------------------------------------------

    def test_clean_run_scores_full(self):
        self.assertEqual(eval_harness.quality_index(self.rec()), 100)

    def test_defects_subtract_their_registered_weight(self):
        self.assertEqual(eval_harness.quality_index(self.rec(defects={"bugs": 2})), 70)
        self.assertEqual(eval_harness.quality_index(self.rec(defects={"security": 1})), 75)

    def test_flags_subtract_their_registered_weight(self):
        self.assertEqual(eval_harness.quality_index(self.rec(over_engineering=True)), 85)
        self.assertEqual(eval_harness.quality_index(self.rec(verified=False)), 80)
        self.assertEqual(eval_harness.quality_index(self.rec(tests_pass=False)), 80)

    def test_index_is_clamped_at_zero(self):
        self.assertEqual(eval_harness.quality_index(self.rec(defects={"security": 10})), 0)

    def test_verdict_is_not_double_counted(self):
        """A clean but failing run keeps 100: completion is reported beside
        the index, never inside it."""
        self.assertEqual(eval_harness.quality_index(self.rec(verdict="fail")), 100)

    # --- aggregation ---------------------------------------------------

    def test_invalid_runs_never_reach_a_mean(self):
        runs = [self.rec(total_tokens=100, verdict="pass"),
                self.rec(run=2, total_tokens=9999, verdict="invalid", note="env")]
        stats = eval_harness._bucket_stats(runs)
        self.assertEqual(stats["n"], 1)
        self.assertEqual(stats["invalid"], 1)
        self.assertEqual(stats["total"], 100)

    def test_bucket_falls_back_to_group_without_a_manifest(self):
        self.assertEqual(eval_harness.cost_bucket("E10", {"E10": {"group": "large"}}, {}),
                         "large")

    def test_manifest_overrides_the_group(self):
        self.assertEqual(
            eval_harness.cost_bucket("E10", {"E10": {"group": "large"}},
                                     {"E10": {"bucket": "medium"}}), "medium")

    def test_bucket_is_none_outside_the_cost_buckets(self):
        self.assertIsNone(eval_harness.cost_bucket("E22", {"E22": {"group": "bugs"}}, {}))

    def test_unstarted_batch_reports_no_coverage_warnings(self):
        """CI runs `check --strict`, where a warning is a red build.

        Before the first cost record an empty bucket means "not begun", not
        "missing a bucket" — warning on it would fail the build for a
        measurement nobody has taken yet.
        """
        self.assertEqual(self.cost_check([]).warnings, [])

    def test_started_batch_warns_about_buckets_with_no_runs(self):
        report = self.cost_check([self.rec(case="E01")])
        self.assertEqual(len(report.warnings), 2)
        joined = " ".join(report.warnings)
        self.assertIn("medium", joined)
        self.assertIn("large", joined)
        self.assertNotIn("small", joined)


class CostRunnerTests(unittest.TestCase):
    """The runner turns a CLI event stream into a record.

    Sample is a real captured `claude -p --output-format stream-json` run, not
    a hand-written mock: the point of the parser is that it reads what the CLI
    actually emits, and a mock would only prove it reads what I imagined.
    """

    SAMPLE = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                          "testdata", "claude-sample.jsonl")

    def events(self):
        return cost_runner.parse_events(read_text(self.SAMPLE))

    def test_unparseable_lines_are_skipped_not_fatal(self):
        events = cost_runner.parse_events("{not json\n\n")
        self.assertEqual(events, [])

    def test_claude_usage_is_read_from_the_real_stream(self):
        s = cost_runner.summarise_claude(self.events())
        self.assertEqual(s["input_tokens"], 29952)
        self.assertEqual(s["output_tokens"], 95)
        self.assertEqual(s["total_tokens"], 30047)
        self.assertEqual(s["tool_calls"], 1)
        self.assertEqual(len(s["files_read"]), 1)
        self.assertIn("theme.js", s["files_read"][0])

    def test_only_real_reads_count_as_loaded(self):
        """"Loaded" means Read. Write/Edit targets are not loads, and tools like
        Grep carry `path` rather than `file_path`, which used to put None in the
        list and make every downstream classifier defend against it."""
        def event(name, inp):
            return {"type": "assistant",
                    "message": {"content": [{"type": "tool_use", "name": name,
                                             "input": inp}]}}
        done = {"type": "result", "usage": {"input_tokens": 1,
                                            "output_tokens": 1},
                "duration_ms": 1000}
        s = cost_runner.summarise_claude([
            event("Read", {"file_path": "/a/references/testing.md"}),
            event("Write", {"file_path": "/a/references/written.md"}),
            event("Grep", {"path": "/a/src", "pattern": "x"}),
            done,
        ])
        self.assertEqual(s["files_read"], ["/a/references/testing.md"])
        self.assertNotIn(None, s["files_read"])

    def test_a_skill_invoked_by_tool_still_counts_as_loaded(self):
        """The pilot's small case invoked Skill {"skill": "ascos"} and reported
        no loaded skill, because loading that way produces no file read. That
        under-reports activation, the one signal this batch is measuring."""
        events = [
            {"type": "assistant", "message": {"content": [
                {"type": "tool_use", "name": "Skill",
                 "input": {"skill": "ascos", "args": "x"}}]}},
            {"type": "result", "usage": {"input_tokens": 1, "output_tokens": 1},
             "duration_ms": 1000},
        ]
        rec = cost_runner.build_record({"id": "E01"}, "with_skill", 1,
                                       "claude", events)
        self.assertEqual(rec["skills_loaded"], ["ascos"])

    def test_seconds_are_derived_from_wall_clock(self):
        self.assertEqual(cost_runner.summarise_claude(self.events())["seconds"], 2.4)

    def test_an_incomplete_stream_yields_no_numbers(self):
        """A run that never completed was not measured — it is not zero."""
        s = cost_runner.summarise_claude([{"type": "assistant"}])
        self.assertIsNone(s.get("input_tokens"))
        self.assertIsNone(s.get("total_tokens"))
        self.assertIn("did not complete", s["note"])

    def test_codex_parser_fails_loudly_instead_of_returning_zeros(self):
        """No successful Codex run has been observed here, so the parser is
        unverified. Returning 0 tokens would be a fabricated measurement."""
        s = cost_runner.summarise_codex([{"type": "turn.started"}])
        self.assertIsNone(s.get("input_tokens"))
        self.assertIn("no token usage event", s["note"])

    def test_codex_parser_reads_a_usage_event(self):
        s = cost_runner.summarise_codex([
            {"type": "token_count",
             "info": {"total_token_usage": {"input_tokens": 900,
                                            "output_tokens": 100}}}])
        self.assertEqual(s["input_tokens"], 900)
        self.assertEqual(s["total_tokens"], 1000)

    def test_observed_reads_split_into_skills_and_references(self):
        skills, refs = cost_runner.classify_paths([
            "C:/ws/.claude/skills/ascos/skills/implementation/SKILL.md",
            "C:/ws/.claude/skills/ascos/references/testing.md",
            "C:/ws/src/theme.js",
        ])
        self.assertEqual(skills, ["implementation"])
        self.assertEqual(refs, ["testing.md"])

    def test_classify_dedupes_and_ignores_junk(self):
        skills, refs = cost_runner.classify_paths([
            "C:/ws/.claude/skills/ascos/skills/implementation/SKILL.md",
            "C:/ws/.claude/skills/ascos/skills/implementation/SKILL.md",
            None, 42,
        ])
        self.assertEqual(skills, ["implementation"])
        self.assertEqual(refs, [])


class CostRunnerIOTests(unittest.TestCase):
    """Workspace preparation and record construction.

    These exercise the parts that decide whether the two arms can differ at
    all, which is the one thing that makes the comparison meaningful.
    """

    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.tmp, True)
        self.sample = read_text(cost_runner.SAMPLE
                                if hasattr(cost_runner, "SAMPLE") else
                                os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                             "testdata", "claude-sample.jsonl"))

    def workspace(self, name):
        return os.path.join(self.tmp, name)

    def test_with_skill_arm_installs_the_skill(self):
        dest = self.workspace("with")
        cost_runner.prepare_workspace(dest, "cost-app", "with_skill", "claude")
        self.assertTrue(os.path.isfile(
            os.path.join(dest, ".claude", "skills", "ascos", "SKILL.md")))

    def test_without_skill_arm_installs_nothing(self):
        dest = self.workspace("without")
        cost_runner.prepare_workspace(dest, "cost-app", "without_skill", "claude")
        self.assertFalse(os.path.isdir(os.path.join(dest, ".claude")))
        self.assertTrue(os.path.isfile(os.path.join(dest, "package.json")))

    def test_empty_workspace_still_gets_the_skill(self):
        """E13 builds from nothing — but must still differ between arms.

        An early return here once produced two identical arms for E13: a pair
        of runs that cannot differ measures nothing.
        """
        dest = self.workspace("empty")
        cost_runner.prepare_workspace(dest, "empty", "with_skill", "claude")
        self.assertTrue(os.path.isfile(
            os.path.join(dest, ".claude", "skills", "ascos", "SKILL.md")))
        self.assertFalse(os.path.exists(os.path.join(dest, "package.json")))

    def test_workspace_is_rebuilt_so_a_second_run_gets_a_clean_fixture(self):
        dest = self.workspace("twice")
        cost_runner.prepare_workspace(dest, "cost-app", "without_skill", "claude")
        with open(os.path.join(dest, "dirty.txt"), "w") as fh:
            fh.write("left over")
        cost_runner.prepare_workspace(dest, "cost-app", "without_skill", "claude")
        self.assertFalse(os.path.exists(os.path.join(dest, "dirty.txt")))

    def _run(self, stdout="", returncode=0, stderr=""):
        case = {"id": "E01", "prompt": "do the thing"}
        self.kwargs = {}

        def fake(*a, **k):
            self.kwargs = k
            return subprocess.CompletedProcess(a, returncode, stdout, stderr)
        original = cost_runner.subprocess.run
        cost_runner.subprocess.run = fake
        try:
            return cost_runner.run_one(case, "with_skill", 1, "claude", None,
                                       "empty", self.tmp, bin_path="x")
        finally:
            cost_runner.subprocess.run = original

    def test_record_carries_what_the_stream_reported(self):
        rec = self._run(stdout=self.sample)
        self.assertEqual(rec["case"], "E01")
        self.assertEqual(rec["variant"], "with_skill")
        self.assertEqual(rec["run"], 1)
        self.assertEqual(rec["verdict"], "pass")
        self.assertEqual(rec["input_tokens"], 29952)
        self.assertEqual(rec["tool_calls"], 1)

    def test_a_failed_run_is_invalid_and_must_say_why(self):
        """`invalid` without a reason is a drawer to sweep results into."""
        rec = self._run(returncode=1, stderr="boom")
        self.assertEqual(rec["verdict"], "invalid")
        self.assertIn("boom", rec["note"])

    def test_the_child_never_inherits_our_stdin(self):
        """`codex exec` reads stdin when it thinks the prompt is missing. One
        run blocking on a terminal would stall a 72-run batch indefinitely."""
        self._run(stdout=self.sample)
        self.assertEqual(self.kwargs.get("stdin"), subprocess.DEVNULL)

    def test_a_timeout_is_invalid_without_taking_the_batch_down(self):
        """72 runs is long enough that one hang must not cost the other 71."""
        def hang(*a, **k):
            raise subprocess.TimeoutExpired(cmd="x", timeout=900,
                                            output="half a turn")
        case = {"id": "E01", "prompt": "p"}
        with unittest.mock.patch.object(cost_runner.subprocess, "run", hang):
            rec = cost_runner.run_one(case, "with_skill", 1, "claude", None,
                                      "empty", self.tmp, bin_path="x")
        self.assertEqual(rec["verdict"], "invalid")
        self.assertIn("timeout", rec["note"])
        self.assertIn("half a turn", rec["note"])
        self.assertIsNone(rec["total_tokens"])

    def test_an_unmeasurable_run_stays_empty_rather_than_zero(self):
        rec = self._run(stdout='{"type":"turn.started"}')
        self.assertIsNone(rec["input_tokens"])
        self.assertIsNone(rec["total_tokens"])

    def test_raw_events_are_kept_so_a_verdict_can_be_reaudited(self):
        self._run(stdout=self.sample)
        self.assertTrue(os.path.isfile(
            os.path.join(self.tmp, "events", "E01-with_skill-1.jsonl")))

    def test_bin_override_is_used_verbatim(self):
        self.assertEqual(cost_runner.resolve_bin("claude", "C:/x/claude.cmd"),
                         "C:/x/claude.cmd")

    def test_manifest_joins_the_corpus_into_a_runnable_batch(self):
        manifest = os.path.join(eval_common.ROOT, "evals", "cost", "manifest.json")
        batch = cost_runner.load_batch(manifest, eval_harness.load_cases())
        self.assertEqual(len(batch), 12)
        by_id = {c["id"]: c for c in batch}
        self.assertEqual(by_id["E01"]["bucket"], "small")
        self.assertEqual(by_id["E13"]["bucket"], "large")
        self.assertEqual(by_id["E13"]["workspace"], "empty")
        self.assertTrue(all(c["prompt"] for c in batch))


class CostRunnerBatchTests(unittest.TestCase):
    """`cmd_run` is the entry point for a 72-run spend.

    It has to be exercised before that spend, not during: a crash at record 40
    would cost the whole batch. The CLI is stubbed so the orchestration is
    tested without paying for 72 real runs.
    """

    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.tmp, True)
        self.sample = read_text(cost_runner.SAMPLE) if hasattr(
            cost_runner, "SAMPLE") else read_text(os.path.join(
                os.path.dirname(os.path.abspath(__file__)), "testdata",
                "claude-sample.jsonl"))
        self.seen = []

        def fake(cmd, *a, **k):
            self.seen.append(list(cmd))
            return subprocess.CompletedProcess(cmd, 0, self.sample, "")
        self.patcher = unittest.mock.patch.object(cost_runner.subprocess,
                                                  "run", fake)
        self.patcher.start()
        self.addCleanup(self.patcher.stop)

    def _args(self, **kw):
        import argparse
        base = dict(manifest=os.path.join(eval_common.ROOT, "evals", "cost",
                                          "manifest.json"),
                    case=None, bucket=None, arm=["with_skill", "without_skill"],
                    runs=1, cli="claude", model=None, out_dir=self.tmp,
                    timeout=900, bin="x")
        base.update(kw)
        return argparse.Namespace(**base)

    def _run_batch(self, args):
        """cmd_run narrates to stdout; that is useful in a terminal and noise
        in a test run."""
        import argparse
        import contextlib
        import io
        assert isinstance(args, argparse.Namespace)
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            rc = cost_runner.cmd_run(args)
        return rc, out.getvalue()

    def _records(self):
        path = os.path.join(self.tmp, "cost-runs.jsonl")
        with open(path, encoding="utf-8") as fh:
            return [json.loads(line) for line in fh if line.strip()]

    def test_one_record_per_case_arm_and_run(self):
        self.assertEqual(self._run_batch(self._args(case="E01", runs=3))[0], 0)
        recs = self._records()
        self.assertEqual(len(recs), 6)
        self.assertEqual({r["case"] for r in recs}, {"E01"})
        self.assertEqual(sorted(r["run"] for r in recs), [1, 1, 2, 2, 3, 3])

    def test_bucket_selection_runs_the_whole_bucket(self):
        self.assertEqual(self._run_batch(self._args(bucket="small"))[0], 0)
        recs = self._records()
        self.assertEqual(len(recs), 8)
        self.assertEqual({r["case"] for r in recs},
                         {"E01", "E02", "E03", "E04"})

    def test_a_pinned_model_reaches_the_cli_invocation(self):
        """Comparability depends on the model actually being passed through."""
        self._run_batch(self._args(case="E01", arm=["without_skill"],
                           model="haiku"))
        self.assertTrue(all("--model" in c for c in self.seen))
        self.assertTrue(all("haiku" in c for c in self.seen))

    def test_no_match_is_an_error_and_writes_nothing(self):
        import io
        import contextlib
        err = io.StringIO()
        with contextlib.redirect_stderr(err):
            rc = cost_runner.cmd_run(self._args(case="E99"))
        self.assertEqual(rc, 1)
        self.assertFalse(os.path.exists(
            os.path.join(self.tmp, "cost-runs.jsonl")))

    def test_running_a_second_case_does_not_discard_the_first(self):
        """Driving a batch one case at a time is the natural way to use this.
        Overwriting the file once silently cost the pilot two of its records."""
        self._run_batch(self._args(case="E01", arm=["with_skill"]))
        self._run_batch(self._args(case="E10", arm=["with_skill"]))
        recs = self._records()
        self.assertEqual({r["case"] for r in recs}, {"E01", "E10"})

    def test_re_running_a_case_replaces_it_rather_than_duplicating(self):
        self._run_batch(self._args(case="E01", arm=["with_skill"]))
        self._run_batch(self._args(case="E01", arm=["with_skill"]))
        recs = self._records()
        self.assertEqual(len(recs), 1)

    def test_records_survive_a_round_trip_through_the_harness(self):
        """A batch that the harness rejects is a batch that measured nothing."""
        self._run_batch(self._args(case="E01", arm=["with_skill"],
                           model="haiku"))
        recs = self._records()
        self.assertTrue(recs)
        self.assertEqual(eval_harness.cost_errors(recs[0]), [])


if __name__ == "__main__":
    unittest.main(verbosity=2)
