#!/usr/bin/env python3
"""Focused tests for contradictory routing fixture references."""

from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path


def load_checker_module():
    path = Path(__file__).with_name("check-skill-routing-fixture.py")
    spec = importlib.util.spec_from_file_location("check_skill_routing_fixture", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"could not load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


checker = load_checker_module()


def fixture_case(**overrides):
    case = {
        "case_id": "fixture-contradiction",
        "prompt": "Route this request to the debugging skill.",
        "expected_skill": "v1-debug",
        "acceptable_skills": [],
        "near_miss_skills": ["v1-fix-tests"],
        "must_not_trigger": ["v1-land-pr"],
        "side_effect_allowed": False,
        "prompt_source": "contributor_seed",
        "budget_stress": False,
        "category": "positive",
        "rationale": "The request directly asks for debugging help.",
    }
    case.update(overrides)
    return case


class RoutingFixtureTests(unittest.TestCase):
    skill_names = {"v1-debug", "v1-fix-tests", "v1-land-pr"}

    def validate(self, **overrides):
        errors = []
        checker.validate_case(
            fixture_case(**overrides), 1, self.skill_names, errors
        )
        return errors

    def test_expected_skill_cannot_be_near_miss(self):
        errors = self.validate(near_miss_skills=["v1-debug"])
        self.assertTrue(any("cannot overlap" in error for error in errors))

    def test_acceptable_skill_cannot_be_must_not_trigger(self):
        errors = self.validate(acceptable_skills=["v1-fix-tests"], must_not_trigger=["v1-fix-tests"])
        self.assertTrue(any("cannot overlap" in error for error in errors))

    def test_near_miss_and_must_not_trigger_may_overlap(self):
        errors = self.validate(
            near_miss_skills=["v1-fix-tests"],
            must_not_trigger=["v1-fix-tests"],
        )
        self.assertFalse(any("cannot overlap" in error for error in errors))


if __name__ == "__main__":
    unittest.main()
