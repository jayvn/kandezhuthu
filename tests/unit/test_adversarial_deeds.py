"""Adversarial stress testing for Kerala property deeds, statutory traps, and extent arithmetic.

Validates:
1. Deeds containing ALL 4 fatal traps simultaneously (burial covenant, wetland, minor rights, maintenance revocation).
2. Bilingual Malayalam OCR noise, typos, dropped ligatures, and deceptive recitals.
3. Extent arithmetic and unit conversions (Hectares, Ares, Cents, Sq.M, Sq.Ft).
4. Multi-deed lineage extent inflation (Nemo dat quod non habet).
"""

import unittest
from app.domain.single_deed_scanner import (
    SingleDeedScanner,
    Verdict,
    TrapCategory,
)
from app.domain.extent_converter import (
    cents_to_ares,
    ares_to_cents,
    hectares_to_ares,
    ares_to_hectares,
    hectares_to_cents,
    cents_to_hectares,
    cents_to_sqm,
    sqm_to_cents,
    cents_to_sqft,
    sqft_to_cents,
    sqm_to_sqft,
    sqft_to_sqm,
    parse_extents_from_text,
    verify_extent_inflation,
    verify_internal_extent_consistency,
)
from app.domain.models import DeedNode, DeedType
from app.domain.auditor import MunnadharamAuditor


class TestAllFourFatalTrapsSimultaneous(unittest.TestCase):
    """Stress tests deeds that bury all 4 fatal Kerala statutory traps in a single instrument."""

    def setUp(self):
        self.scanner = SingleDeedScanner()

    def test_english_deed_with_all_4_fatal_traps(self):
        """Validates that a deed containing all 4 fatal traps simultaneously is flagged with:
        - All 4 distinct TrapCategory findings
        - Statutory severities (RED for CRITICAL, AMBER for HIGH/MEDIUM)
        - Sanity score <= 25/100 (in fact 0)
        - Verdict DANGER
        - Statutory legal citations (Easements Act, Paddy Land Act 2008, HMGA 1956, Senior Citizens Act 2007)
        """
        deed_text = """
        SALE DEED No. 1402/2022 of Sub-Registrar Office Aluva.
        Preamble: Executed by Smt. Kamala, acting as mother and natural guardian on behalf of
        her minor daughter Kumari Ananya, aged 8 years, selling the minor's undivided share for family maintenance.
        
        Schedule of Property:
        Re-Survey No. 412/4, Village: Aluva West, Taluk: Aluva, District: Ernakulam.
        Revenue Classification: Land categorized in revenue records as Nanja / Nilam (Paddy land), measuring 12 Cents.
        
        Parental Maintenance Condition:
        This conveyance is subject to the explicit condition of looking after elderly parents during their lifetime,
        with a specific clause allowing deed cancellation and revocation if maintenance is neglected.
        
        Schedule Footer Covenants:
        Reserving a 3-meter nadappu vazhi pathway covenant along the southern boundary for neighbor access.
        """
        result = self.scanner.scan(deed_text)

        # 1. Overall verdict and score
        self.assertEqual(result.verdict, Verdict.DANGER)
        self.assertLessEqual(result.sanity_score, 25)
        self.assertEqual(result.sanity_score, 0)  # 100 - 25 - 45 - 40 - 20 = 0

        # 2. All 4 traps must be detected
        detected_traps = {f.trap_type for f in result.findings}
        self.assertEqual(
            detected_traps,
            {
                TrapCategory.EASEMENT_RIGHT_OF_WAY,
                TrapCategory.WETLAND_NILAM_RISK,
                TrapCategory.MINOR_RIGHTS_DEFECT,
                TrapCategory.MAINTENANCE_CONDITIONAL_CLAUSE,
            },
        )

        # 3. Verify statutory severities
        finding_map = {f.trap_type: f for f in result.findings}
        self.assertEqual(finding_map[TrapCategory.WETLAND_NILAM_RISK].severity, "CRITICAL")
        self.assertEqual(finding_map[TrapCategory.MINOR_RIGHTS_DEFECT].severity, "CRITICAL")
        self.assertEqual(finding_map[TrapCategory.MAINTENANCE_CONDITIONAL_CLAUSE].severity, "HIGH")
        self.assertEqual(finding_map[TrapCategory.EASEMENT_RIGHT_OF_WAY].severity, "MEDIUM")

        # 4. Verify statutory citations
        self.assertIn("Easements Act", finding_map[TrapCategory.EASEMENT_RIGHT_OF_WAY].kerala_statute)
        self.assertIn("Paddy Land", finding_map[TrapCategory.WETLAND_NILAM_RISK].kerala_statute)
        self.assertIn("Hindu Minority and Guardianship Act", finding_map[TrapCategory.MINOR_RIGHTS_DEFECT].kerala_statute)
        self.assertIn("Senior Citizens Act", finding_map[TrapCategory.MAINTENANCE_CONDITIONAL_CLAUSE].kerala_statute)

        # 5. Verify bilingual seller question drafting
        for finding in result.findings:
            self.assertTrue(len(finding.whatsapp_question_for_seller) > 10, "Malayalam inquiry missing")
            self.assertTrue(len(finding.whatsapp_question_for_seller_en) > 10, "English inquiry missing")

    def test_malayalam_script_deed_with_all_4_fatal_traps(self):
        """Validates that authentic Malayalam deed text with all 4 traps is detected without dropping Unicode tokens."""
        deed_text = """
        തീറാധാരം നമ്പർ 820/2021 (ആലുവ സബ് രജിസ്ട്രാർ ഓഫീസ്):
        
        വിൽപ്പനക്കാരി: കമല, പ്രായപൂർത്തിയാകാത്ത മൈനർ മകൾ ആര്യക്ക് വേണ്ടി മാതാവും സ്വാഭാവിക രക്ഷാകർത്താവും ആയി 
        കുടുംബച്ചിലവിനായി മൈനറുടെ സ്വത്ത് തീറു നൽകുന്നു.
        
        വസ്തു വിവരണം (ഷെഡ്യൂൾ):
        ആലുവ വെസ്റ്റ് വില്ലേജിൽ റീ-സർവേ 108/3-ൽപ്പെട്ട 10 സെന്റ് സ്ഥലം.
        ഭൂമി തരംതിരിവ്: വില്ലേജ് രേഖയിൽ നഞ്ച നിലം ആകുന്നു.
        
        വ്യവസ്ഥ:
        വൃദ്ധരായ മാതാപിതാക്കളെ ജീവിതകാലം മുഴുവൻ സംരക്ഷിക്കേണ്ടതാണ്. സംരക്ഷണം മുടങ്ങിയാൽ ആധാരം റദ്ദാക്കാൻ അധികാരമുള്ളതാണ്.
        
        ഷെഡ്യൂൾ അടിക്കുറിപ്പ്:
        കിഴക്കേ അതിരിലൂടെ അയൽവാസികൾക്ക് 3 മീറ്റർ വീതിയിൽ നടപ്പുവഴി അനുവദിച്ചിട്ടുള്ളതാകുന്നു.
        """
        result = self.scanner.scan(deed_text)

        self.assertEqual(result.verdict, Verdict.DANGER)
        self.assertLessEqual(result.sanity_score, 25)

        detected_traps = {f.trap_type for f in result.findings}
        self.assertIn(TrapCategory.EASEMENT_RIGHT_OF_WAY, detected_traps)
        self.assertIn(TrapCategory.WETLAND_NILAM_RISK, detected_traps)
        self.assertIn(TrapCategory.MINOR_RIGHTS_DEFECT, detected_traps)
        self.assertIn(TrapCategory.MAINTENANCE_CONDITIONAL_CLAUSE, detected_traps)

    def test_court_order_mitigates_minor_trap_only(self):
        """Citing a valid District Court sanction order must clear the minor trap while retaining other traps."""
        deed_text = """
        Sale deed executed by Smt. Radha as natural guardian on behalf of minor son Master Ashwin,
        duly authorized by District Court Sanction Order in O.P. No. 45/2020.
        Classification: Nanja (Nilam) measuring 8 Cents.
        Reserving nadappu vazhi along eastern boundary.
        Subject to condition to maintain elderly parents.
        """
        result = self.scanner.scan(deed_text)
        detected_traps = {f.trap_type for f in result.findings}

        self.assertNotIn(TrapCategory.MINOR_RIGHTS_DEFECT, detected_traps)
        self.assertIn(TrapCategory.WETLAND_NILAM_RISK, detected_traps)
        self.assertIn(TrapCategory.EASEMENT_RIGHT_OF_WAY, detected_traps)
        self.assertIn(TrapCategory.MAINTENANCE_CONDITIONAL_CLAUSE, detected_traps)

    def test_form_6_approval_mitigates_wetland_trap_only(self):
        """Citing statutory Form 6 conversion order must clear the wetland trap while retaining other traps."""
        deed_text = """
        Sale deed for 10 Cents in Re-Sy 55/2.
        Classification: Formerly Nilam, regularized under Section 27A with Form 6 approved vide RDO Order 401/2021.
        Executed by mother on behalf of minor daughter without court sanction.
        Reserving nadappu vazhi pathway.
        """
        result = self.scanner.scan(deed_text)
        detected_traps = {f.trap_type for f in result.findings}

        self.assertNotIn(TrapCategory.WETLAND_NILAM_RISK, detected_traps)
        self.assertIn(TrapCategory.MINOR_RIGHTS_DEFECT, detected_traps)
        self.assertIn(TrapCategory.EASEMENT_RIGHT_OF_WAY, detected_traps)


class TestBilingualAndNoisyOCR(unittest.TestCase):
    """Validates resilience against noisy OCR text, font dropouts, and deceptive drafting."""

    def setUp(self):
        self.scanner = SingleDeedScanner()

    def test_ocr_typo_nilam_missing_anusvara(self):
        """When Malayalam OCR drops the trailing anusvara 'ം', 'നഞ്ച നില' must still be caught."""
        noisy_text = """
        വസ്തുവിവരം: റീ-സർവേ 204/1, വിസ്തീർണ്ണം 15 സെന്റ്.
        ഭൂമിയുടെ തരം: നഞ്ച നില ആകുന്നു.
        """
        result = self.scanner.scan(noisy_text)
        self.assertEqual(result.verdict, Verdict.DANGER)
        self.assertTrue(any(f.trap_type == TrapCategory.WETLAND_NILAM_RISK for f in result.findings))

    def test_deceptive_purayidam_claim_with_nilam_revenue_status(self):
        """When seller claims land is 'purayidam' in description, but BTR is Nilam without Form 6, trap must trigger."""
        deceptive_text = """
        Schedule of Property:
        Re-Survey 89/1, measuring 10 Cents.
        Property is currently occupied and used as purayidam with garden crops,
        however in the Village Revenue Basic Tax Register (BTR), the classification is listed as Nilam.
        """
        result = self.scanner.scan(deceptive_text)
        self.assertEqual(result.verdict, Verdict.DANGER)
        self.assertTrue(any(f.trap_type == TrapCategory.WETLAND_NILAM_RISK for f in result.findings))

    def test_ocr_typo_in_pathway_transliteration(self):
        """Catches noisy transliterated OCR terms like 'nadapu vazhi' or 'nadappuvazhy'."""
        noisy_text = """
        Schedule: Re-Sy 112/3, 8 Cents purayidam.
        Special condition: The purchaser agrees to provide 3 meter nadapu vazhi along south boundary.
        """
        result = self.scanner.scan(noisy_text)
        self.assertEqual(result.verdict, Verdict.CAUTION)
        self.assertTrue(any(f.trap_type == TrapCategory.EASEMENT_RIGHT_OF_WAY for f in result.findings))

    def test_malayalam_script_water_well_servitude(self):
        """Catches Malayalam well water servitude covenant."""
        text = """
        ഷെഡ്യൂൾ: 5 സെന്റ് പുരയിടം. തെക്കേ അതിരിലുള്ള കിണറ്റിൽ നിന്ന് വെള്ളമെടുക്കാനുള്ള അവകാശം അയൽവാസിക്ക് ഉണ്ടായിരിക്കുന്നതാണ്.
        """
        result = self.scanner.scan(text)
        self.assertEqual(result.verdict, Verdict.CAUTION)
        self.assertTrue(any(f.trap_type == TrapCategory.EASEMENT_RIGHT_OF_WAY for f in result.findings))

    def test_malayalam_elderly_parent_revocation_clause(self):
        """Catches deed cancellation threat for parent maintenance."""
        text = """
        ദാനാധാരം: മകൻ അച്ഛനമ്മമാരെ ശുശ്രൂഷിക്കേണ്ടതാണ്. വ്യവസ്ഥ ലംഘിച്ചാൽ ആധാരം റദ്ദാക്കാൻ പൂർണ്ണ അധികാരമുണ്ടായിരിക്കും.
        """
        result = self.scanner.scan(text)
        self.assertEqual(result.verdict, Verdict.CAUTION)
        self.assertTrue(any(f.trap_type == TrapCategory.MAINTENANCE_CONDITIONAL_CLAUSE for f in result.findings))


class TestExtentArithmeticAndConversions(unittest.TestCase):
    """Validates exact conversions between Hectares, Ares, Cents, Sq.M, and Sq.Ft."""

    def test_hectares_to_ares_and_cents(self):
        # 1 Hectare = 100 Ares = 247.1054 Cents
        self.assertEqual(hectares_to_ares(1.0), 100.0)
        self.assertAlmostEqual(hectares_to_cents(1.0), 247.1054, places=2)
        self.assertEqual(ares_to_hectares(100.0), 1.0)
        self.assertAlmostEqual(cents_to_hectares(247.1054), 1.0, places=3)

        # 0.0405 Hectares = 4.05 Ares ≈ 10.01 Cents
        self.assertEqual(hectares_to_ares(0.0405), 4.05)
        self.assertAlmostEqual(hectares_to_cents(0.0405), 10.01, places=1)

    def test_ares_and_cents_conversions(self):
        # 10 Cents to Ares: 10 * 0.40468564 = 4.0469 Ares
        ares = cents_to_ares(10.0)
        self.assertAlmostEqual(ares, 4.0469, places=3)

        # 4.0469 Ares to Cents: round trip to 10.0 Cents
        cents = ares_to_cents(ares)
        self.assertAlmostEqual(cents, 10.0, places=1)

        # 25 Cents (free Form 6 threshold in Kerala): 25 * 0.404686 = 10.117 Ares
        ares_25 = cents_to_ares(25.0)
        self.assertAlmostEqual(ares_25, 10.117, places=2)

    def test_cents_to_sqm_and_sqft(self):
        # 1 Cent = 40.4686 Sq.M = 435.6 Sq.Ft
        self.assertAlmostEqual(cents_to_sqm(1.0), 40.4686, places=2)
        self.assertEqual(cents_to_sqft(1.0), 435.6)
        self.assertAlmostEqual(sqm_to_cents(40.4686), 1.0, places=2)
        self.assertAlmostEqual(sqft_to_cents(435.6), 1.0, places=2)

        # 10 Cents = 404.69 Sq.M = 4356.0 Sq.Ft
        self.assertAlmostEqual(cents_to_sqm(10.0), 404.6856, places=2)
        self.assertEqual(cents_to_sqft(10.0), 4356.0)

        # Sq.M to Sq.Ft conversion: 40.468564 Sq.M -> 435.6 Sq.Ft
        self.assertAlmostEqual(sqm_to_sqft(40.468564), 435.6, places=1)
        self.assertAlmostEqual(sqft_to_sqm(435.6), 40.4686, places=2)

    def test_parse_extents_from_bilingual_strings(self):
        # English string
        parsed_en = parse_extents_from_text("Extent: 10 Cents (4.05 Ares / 404.68 Sq.M / 4356 Sq.Ft)")
        self.assertEqual(parsed_en.cents, 10.0)
        self.assertEqual(parsed_en.ares, 4.05)
        self.assertEqual(parsed_en.sq_meters, 404.68)
        self.assertEqual(parsed_en.sq_feet, 4356.0)

        # Malayalam string
        parsed_ml = parse_extents_from_text("വിസ്തീർണ്ണം 12 സെന്റ് (4.86 ആർ, 485.6 ചതുരശ്ര മീറ്റർ)")
        self.assertEqual(parsed_ml.cents, 12.0)
        self.assertEqual(parsed_ml.ares, 4.86)
        self.assertEqual(parsed_ml.sq_meters, 485.6)

        # Hectare in revenue record
        parsed_ha = parse_extents_from_text("Re-survey extent: 0.0810 Hectares (8.1 Ares)")
        self.assertEqual(parsed_ha.hectares, 0.0810)
        self.assertEqual(parsed_ha.ares, 8.1)

    def test_internal_extent_discrepancy_detection(self):
        """Detects contradictory units within a single deed (e.g. 4.0 Ares stated as 15 Cents)."""
        # 4.0 Ares is only ~9.88 Cents, not 15.0 Cents!
        is_inconsistent, diff, msg = verify_internal_extent_consistency(cents=15.0, ares=4.0)
        self.assertTrue(is_inconsistent)
        self.assertGreater(diff, 5.0)
        self.assertIn("conflicts with stated 4.00 Ares", msg)

        # Consistent extent should pass
        is_clean, _, _ = verify_internal_extent_consistency(cents=10.0, ares=4.05)
        self.assertFalse(is_clean)

    def test_single_deed_scanner_flags_internal_extent_inflation(self):
        """SingleDeedScanner flags deeds where schedule claims inflated cents over stated Ares."""
        deed_text = """
        Schedule of Property:
        Re-Survey No: 301/2, Village: Aluva.
        Classification: Purayidam.
        Extent: 4.00 Ares (16 Cents).
        Boundaries: All four sides residential plots.
        """
        scanner = SingleDeedScanner()
        result = scanner.scan(deed_text)

        self.assertEqual(result.verdict, Verdict.CAUTION)
        self.assertTrue(any(f.trap_type == TrapCategory.EXTENT_INFLATION_DISCREPANCY for f in result.findings))

    def test_lineage_extent_inflation_nemo_dat(self):
        """MunnadharamAuditor flags multi-deed chain when subsequent deed claims more land than prior deed."""
        deeds = [
            DeedNode(
                doc_number="100/2000",
                year=2000,
                sro_name="Aluva",
                deed_type=DeedType.THEERADHARAM,
                grantors=["Raman Nair"],
                grantees=["Suresh"],
                extent_cents=8.0,
                survey_no="105/1",
            ),
            DeedNode(
                doc_number="250/2015",
                year=2015,
                sro_name="Aluva",
                deed_type=DeedType.THEERADHARAM,
                grantors=["Suresh"],
                grantees=["Antony"],
                extent_cents=10.0,  # +2.0 Cents unbacked extent!
                survey_no="105/1",
            ),
        ]
        auditor = MunnadharamAuditor(property_identifier="Re-Sy 105/1 Aluva")
        scorecard = auditor.audit(deeds)

        inflation_flags = [f for f in scorecard.risk_flags if f.category == "EXTENT_INFLATION"]
        self.assertEqual(len(inflation_flags), 1)
        self.assertIn("Nemo dat quod non habet", inflation_flags[0].legal_citation)
        self.assertIn("+2.00 Cents", inflation_flags[0].description)
        self.assertIn("Ares", inflation_flags[0].description)


if __name__ == "__main__":
    unittest.main()
