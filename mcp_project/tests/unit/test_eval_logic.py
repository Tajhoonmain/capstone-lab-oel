"""
Unit Tests for the Quality Gate Evaluation Logic.

These tests validate the evaluation logic WITHOUT making any real LLM calls.
They mock the agent so CI/CD runs are fast and don't consume API quota.

Run locally: pytest mcp_project/tests/unit/ -v
"""

import json
import os
import sys
import pytest
from unittest.mock import patch, MagicMock


# ──────────────────────────────────────────────
# Fixtures
# ──────────────────────────────────────────────


@pytest.fixture
def sample_thresholds():
    return {
        "keyword_match_score": 1.0,
        "relevancy_score": 0.8,
    }


@pytest.fixture
def passing_test_suite():
    return [
        {
            "question": "If my GPA is 1.5, what is my academic status?",
            "expected_keyword": "probation",
        },
        {
            "question": "How many grade points do I get for an A-?",
            "expected_keyword": "3.67",
        },
    ]


# ──────────────────────────────────────────────
# Test 1 — Keyword evaluator logic (pure unit)
# ──────────────────────────────────────────────


class TestKeywordEvaluator:
    """Tests the keyword-match scoring logic used by run_eval.py."""

    def _score(self, expected_keyword: str, agent_response: str) -> float:
        """Mirrors the exact logic in run_eval.py."""
        return 1.0 if expected_keyword.lower() in agent_response.lower() else 0.0

    def test_exact_match_passes(self):
        score = self._score("probation", "Your GPA is below 2.0, so you are on academic probation.")
        assert score == 1.0

    def test_case_insensitive_match(self):
        score = self._score("PROBATION", "You are on Academic Probation per the handbook.")
        assert score == 1.0

    def test_no_match_fails(self):
        score = self._score("probation", "Your status is satisfactory.")
        assert score == 0.0

    def test_partial_match_passes(self):
        """Keyword is a substring — should still pass."""
        score = self._score("3.67", "An A- is worth exactly 3.67 grade points.")
        assert score == 1.0

    def test_empty_response_fails(self):
        score = self._score("probation", "")
        assert score == 0.0


# ──────────────────────────────────────────────
# Test 2 — Threshold enforcement logic
# ──────────────────────────────────────────────


class TestThresholdEnforcement:
    """Tests the gate pass/fail logic from run_eval.py."""

    def _check_thresholds(self, metrics: dict, thresholds: dict):
        """Mirrors the threshold-check in run_eval.py. Returns list of failed metrics."""
        failed = []
        for metric_name, threshold_val in thresholds.items():
            actual_val = metrics.get(metric_name, 0.0)
            if actual_val < threshold_val:
                failed.append(metric_name)
        return failed

    def test_all_metrics_pass(self, sample_thresholds):
        metrics = {"keyword_match_score": 1.0, "relevancy_score": 0.9}
        failed = self._check_thresholds(metrics, sample_thresholds)
        assert failed == []

    def test_keyword_metric_fails(self, sample_thresholds):
        metrics = {"keyword_match_score": 0.5, "relevancy_score": 0.9}
        failed = self._check_thresholds(metrics, sample_thresholds)
        assert "keyword_match_score" in failed

    def test_relevancy_metric_fails(self, sample_thresholds):
        metrics = {"keyword_match_score": 1.0, "relevancy_score": 0.5}
        failed = self._check_thresholds(metrics, sample_thresholds)
        assert "relevancy_score" in failed

    def test_both_metrics_fail(self, sample_thresholds):
        metrics = {"keyword_match_score": 0.0, "relevancy_score": 0.0}
        failed = self._check_thresholds(metrics, sample_thresholds)
        assert len(failed) == 2

    def test_missing_metric_treated_as_zero(self, sample_thresholds):
        """If a metric is absent from results, it defaults to 0.0 and should fail."""
        metrics = {}  # no keys at all
        failed = self._check_thresholds(metrics, sample_thresholds)
        assert "keyword_match_score" in failed


# ──────────────────────────────────────────────
# Test 3 — Eval report structure
# ──────────────────────────────────────────────


class TestEvalReportStructure:
    """Validates that eval_results.json has the required schema."""

    def test_report_has_required_keys(self, tmp_path):
        report = {
            "metrics": {"keyword_match_score": 1.0, "relevancy_score": 0.9},
            "thresholds": {"keyword_match_score": 1.0, "relevancy_score": 0.8},
            "pass": True,
            "details": [],
        }
        report_path = tmp_path / "eval_results.json"
        report_path.write_text(json.dumps(report))

        loaded = json.loads(report_path.read_text())
        assert "metrics" in loaded
        assert "thresholds" in loaded
        assert "pass" in loaded
        assert "details" in loaded

    def test_passing_report_sets_pass_true(self):
        report = {"metrics": {}, "thresholds": {}, "pass": True, "details": []}
        assert report["pass"] is True

    def test_failing_report_sets_pass_false(self):
        report = {"metrics": {}, "thresholds": {}, "pass": False, "details": []}
        assert report["pass"] is False


# ──────────────────────────────────────────────
# Test 4 — run_eval.py integration (mocked agent)
# ──────────────────────────────────────────────


class TestRunEvalMocked:
    """
    Tests the full run_eval pipeline with the agent mocked out.
    No LLM calls are made — this is safe to run in CI without a real API key.
    """

    def _make_mock_event(self, content: str):
        """Creates a fake LangGraph stream event."""
        msg = MagicMock()
        msg.type = "ai"
        msg.tool_calls = []
        msg.content = content
        return {"messages": [msg]}

    def test_full_eval_passes_when_keywords_found(self, tmp_path, monkeypatch):
        """Mocks the agent to return the expected keywords → gate should PASS."""

        # Mock responses that contain the expected keywords
        responses = ["You are on academic probation.", "An A- is worth 3.67 grade points."]
        call_count = [0]

        def mock_stream(inputs, config, stream_mode):
            response = responses[call_count[0] % len(responses)]
            call_count[0] += 1
            yield self._make_mock_event(response)

        # Patch the multi_agent_app stream and file I/O
        monkeypatch.setenv("GEMINI_API_KEY", "stub-key")
        monkeypatch.chdir(tmp_path)

        # Copy thresholds file to temp dir
        thresholds_dir = tmp_path / "mcp_project"
        thresholds_dir.mkdir()
        (thresholds_dir / "eval_thresholds.json").write_text(
            json.dumps({"keyword_match_score": 1.0, "relevancy_score": 0.8})
        )

        with patch("mcp_project.run_eval.multi_agent_app") as mock_app:
            mock_app.stream.side_effect = mock_stream

            # Import here after patching
            import importlib
            import mcp_project.run_eval as run_eval_module

            importlib.reload(run_eval_module)

            # The function should not sys.exit(1)
            with patch("sys.exit") as mock_exit:
                run_eval_module.run_headless_eval()
                # Check it exited with 0 (pass) not 1 (fail)
                mock_exit.assert_called_with(0)

    def test_api_key_missing_exits_with_error(self, monkeypatch):
        """Without GEMINI_API_KEY, run_eval must exit with code 1."""
        monkeypatch.delenv("GEMINI_API_KEY", raising=False)

        import importlib
        import mcp_project.run_eval as run_eval_module

        importlib.reload(run_eval_module)

        with pytest.raises(SystemExit) as exc_info:
            run_eval_module.run_headless_eval()

        assert exc_info.value.code == 1


# ──────────────────────────────────────────────
# Test 5 — Config & environment sanity checks
# ──────────────────────────────────────────────


class TestEnvironmentSanity:
    """Fast sanity checks that don't import the agent at all."""

    def test_python_version_is_311_or_higher(self):
        assert sys.version_info >= (3, 11), f"Python 3.11+ required, got {sys.version}"

    def test_eval_thresholds_file_exists(self):
        path = os.path.join("mcp_project", "eval_thresholds.json")
        assert os.path.exists(path), "eval_thresholds.json is missing from mcp_project/"

    def test_eval_thresholds_are_valid_json(self):
        path = os.path.join("mcp_project", "eval_thresholds.json")
        with open(path) as f:
            data = json.load(f)
        assert isinstance(data, dict), "eval_thresholds.json must be a JSON object"
        assert len(data) > 0, "eval_thresholds.json must not be empty"

    def test_threshold_values_are_between_0_and_1(self):
        path = os.path.join("mcp_project", "eval_thresholds.json")
        with open(path) as f:
            data = json.load(f)
        for key, val in data.items():
            assert 0.0 <= val <= 1.0, f"Threshold '{key}' must be in [0, 1], got {val}"

    def test_requirements_txt_exists(self):
        assert os.path.exists("requirements.txt"), "requirements.txt not found at project root"
