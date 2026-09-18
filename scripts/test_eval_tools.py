#!/usr/bin/env python3
"""Tests for the eval harness and its shared primitives.

Stdlib only, the same constraint as the scripts under test: CI has no PyYAML
and must not need it. Run with `python scripts/test_eval_tools.py`.
"""

from __future__ import annotations

import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import eval_common  # noqa: E402
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


if __name__ == "__main__":
    unittest.main(verbosity=2)
