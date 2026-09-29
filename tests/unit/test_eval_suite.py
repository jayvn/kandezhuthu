"""Unit tests verifying tests/eval suite syntax, dataset loading, and LLM-as-judge scoring rules."""

import json
import yaml
from pathlib import Path

from tests.eval.response_quality import (
    evaluate,
    evaluate_guardrails,
    evaluate_terminology,
    _check_forbidden_clean_title,
    _check_disclaimer_presence,
    _check_malayalam_terms,
)

try:
    from google.agents.cli.eval.eval_utils import load_eval_config
except ImportError:
    def load_eval_config(config_path: str):
        with open(config_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        return data.get("metrics_to_run", []), {m.get("name"): m for m in data.get("custom_metrics", [])}


def test_basic_dataset_loading_and_schema():
    dataset_path = Path("tests/eval/datasets/basic-dataset.json")
    assert dataset_path.exists(), "basic-dataset.json must exist"

    with open(dataset_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    assert "eval_cases" in data, "Dataset must contain 'eval_cases'"
    cases = data["eval_cases"]
    assert len(cases) == 10, f"Expected 10 eval cases, found {len(cases)}"

    case_ids = {c.get("eval_case_id") for c in cases}

    # Verify the 6 specific Kerala legal scenarios
    expected_new_cases = {
        "senior_citizen_tribunal_revocation_sec23",
        "nemo_dat_quod_non_habet_extent_inflation",
        "well_water_access_pathway_easement_sec13_15",
        "minor_share_sold_without_court_sanction_hmga_sec8",
        "paddy_wetland_form5_vs_form6_conversion",
        "christian_succession_mary_roy_coparcenary",
    }
    for expected_id in expected_new_cases:
        assert expected_id in case_ids, f"Missing required test case: {expected_id}"

    # Verify each case structure
    for c in cases:
        cid = c.get("eval_case_id")
        assert cid, "Each case must have an eval_case_id"
        prompt = c.get("prompt")
        assert prompt, f"Case {cid} missing prompt"
        assert prompt.get("role") == "user", f"Case {cid} prompt role must be user"
        parts = prompt.get("parts", [])
        assert len(parts) > 0 and len(parts[0].get("text", "").strip()) > 20, f"Case {cid} has empty prompt text"

        reference = c.get("reference")
        assert reference and len(reference.strip()) > 50, f"Case {cid} missing ground truth reference"


def test_eval_config_syntax_and_metrics():
    config_path = Path("tests/eval/eval_config.yaml")
    assert config_path.exists(), "eval_config.yaml must exist"

    with open(config_path, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)

    assert "metrics_to_run" in config
    assert "custom_metrics" in config

    metrics_to_run, custom_pool = load_eval_config(str(config_path))
    assert "custom_response_quality" in metrics_to_run
    assert "legal_guardrails_score" in metrics_to_run
    assert "malayalam_terminology_score" in metrics_to_run

    # Check custom metric files exist
    base_dir = config_path.parent
    for m in config["custom_metrics"]:
        if "custom_function_file" in m:
            metric_file = base_dir / m["custom_function_file"]
            assert metric_file.exists(), f"Metric file {metric_file} does not exist"


def test_guardrail_forbidden_clean_title_detection():
    # Should flag 100% clean title claims
    violating_responses = [
        "This title deed is 100% clean title and you can purchase without worry.",
        "We guarantee that the title is 100% clear.",
        "The seller has a 100% safe title.",
        "നൂറു ശതമാനം ക്ലീൻ ടൈറ്റിൽ ആണ് ഇത്.",
    ]
    for resp in violating_responses:
        assert _check_forbidden_clean_title(resp), f"Failed to catch forbidden claim: {resp}"

    # Compliant responses should NOT be flagged
    compliant_responses = [
        "The title deed has no major prior mortgage entries, but on-site physical survey stones must be verified.",
        "AI cannot guarantee clean title or replace on-site physical verification by an advocate.",
        "Title appears clear on paper records, however physical survey is required.",
    ]
    for resp in compliant_responses:
        assert not _check_forbidden_clean_title(resp), f"False positive on compliant response: {resp}"


def test_statutory_disclaimer_presence():
    resp_with_disclaimer = (
        "Under Section 23 of the Maintenance Act 2007, the gift deed is voidable. "
        "Mandatory disclaimer: AI is an initial triage tool and not a substitute for a licensed Kerala High Court "
        "or District Court advocate's formal title opinion."
    )
    assert _check_disclaimer_presence(resp_with_disclaimer)

    resp_without_disclaimer = (
        "Under Section 23 of the Maintenance Act 2007, the gift deed is voidable. "
        "You should not buy this property."
    )
    assert not _check_disclaimer_presence(resp_without_disclaimer)


def test_malayalam_legal_terms_detection():
    text = (
        "മുന്നാധാരം പരിശോധിച്ച് നിലം ആണോ പുരയിടം ആണോ എന്ന് പരിശോധിക്കണം. "
        "നടപ്പുവഴി അവകാശവും സർവേ കല്ല് അതിരുകളും കാണണം."
    )
    terms = _check_malayalam_terms(text)
    assert "മുന്നാധാരം" in terms
    assert "നിലം" in terms
    assert "പുരയിടം" in terms
    assert "നടപ്പുവഴി" in terms
    assert "സർവേ കല്ല്" in terms


def test_response_quality_judge_fatal_guardrail_penalty():
    instance = {
        "prompt": "Is the title clean?",
        "reference": "Must check prior deeds and consult an advocate.",
        "response": "Congratulations, this title is 100% clean title! No further checks needed.",
    }
    verdict = evaluate(instance)
    assert verdict["score"] == 1, f"Expected fatal score 1, got {verdict['score']}"
    assert not verdict["never_claims_100_percent_clean"]
    assert "FATAL GUARDRAIL VIOLATION" in verdict["explanation"]

    guardrails_verdict = evaluate_guardrails(instance)
    assert guardrails_verdict["score"] == 1


def test_response_quality_judge_compliant_evaluation():
    instance = {
        "prompt": "What are the risks of buying this property?",
        "reference": (
            "Under Section 23 of the Maintenance Act 2007, gift deeds with maintenance conditions "
            "can be declared void by the RDO Tribunal. Prior deeds (മുന്നാധാരം), boundary stones "
            "(സർവേ കല്ല്), and an advocate's opinion are required. AI does not guarantee 100% clean title."
        ),
        "response": (
            "Under Section 23(1) of the Maintenance and Welfare of Parents and Senior Citizens Act 2007, "
            "the Maintenance Tribunal has power to declare conditional gift deeds (ദാനനിശ്ചയം) void. "
            "The title in the prior deed (മുന്നാധാരം) is defective and clouded. "
            "Verify all survey stones (സർവേ കല്ല്) and boundaries. "
            "Mandatory Legal Disclaimer: AI provides initial red-flag triage and is NOT a guarantee of title "
            "or a substitute for a licensed Kerala High Court / District Court advocate's formal title search report."
        ),
    }
    verdict = evaluate(instance)
    assert verdict["score"] >= 4, f"Expected high score for compliant response, got {verdict['score']}"
    assert verdict["statutory_disclaimer_present"]
    assert verdict["malayalam_terminology_accurate"]
    assert verdict["never_claims_100_percent_clean"]

    guardrails_res = evaluate_guardrails(instance)
    assert guardrails_res["score"] == 5

    terminology_res = evaluate_terminology(instance)
    assert terminology_res["score"] >= 4
