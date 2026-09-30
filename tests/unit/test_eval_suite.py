"""Unit tests for the eval judge's guardrail, disclaimer and terminology scoring rules."""

from tests.eval.response_quality import (
    evaluate,
    evaluate_guardrails,
    evaluate_terminology,
    _check_forbidden_clean_title,
    _check_disclaimer_presence,
    _check_malayalam_terms,
)


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
