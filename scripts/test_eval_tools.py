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

MUST_NOT_FIRE = [{"id": "T11", "group": "trigger", "expect": "not_fire",
                  "_rel": "evals/triggers/11.md"}]
MUST_FIRE = [{"id": "T01", "group": "trigger", "expect": "fire",
              "_rel": "evals/triggers/01.md"}]


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


class VerdictTypeTests(unittest.TestCase):
    def test_trigger_verdicts_on_trigger_case(self):
        report = check([{"case": "T01", "variant": "with_skill", "run": 1,
                         "verdict": "pass"}], MUST_FIRE)
        self.assertTrue(report.errors)

    def test_behaviour_verdict_rejected_on_trigger_case(self):
        report = check([{"case": "T01", "variant": "with_skill", "run": 1,
                         "verdict": "fire"}], MUST_FIRE)
        self.assertFalse(report.errors)


if __name__ == "__main__":
    unittest.main(verbosity=2)
