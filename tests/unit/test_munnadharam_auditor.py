"""Unit tests for Munnadharam Auditor: Kerala Prior Deeds Title Lineage Legal Heuristics."""

import unittest
from app.domain.models import DeedNode, DeedType, ECRecord, RiskSeverity
from app.domain.auditor import MunnadharamAuditor


class TestMunnadharamAuditor(unittest.TestCase):

    def setUp(self):
        self.auditor = MunnadharamAuditor(property_identifier="Sy. No. 412/3, Aluva West Village")

    def test_clean_chain_of_title(self):
        """Test a clean 3-deed chain over 30 years without any legal defects."""
        deeds = [
            DeedNode(
                doc_number="412/1985",
                year=1985,
                sro_name="Aluva",
                deed_type=DeedType.PATTAYAM,
                grantors=["Special Tahsildar (Land Assignment)"],
                grantees=["Kunjuraman Nair"],
                extent_cents=10.0,
                survey_no="412/3",
            ),
            DeedNode(
                doc_number="1890/2004",
                year=2004,
                sro_name="Aluva",
                deed_type=DeedType.THEERADHARAM,
                grantors=["Kunjuraman Nair"],
                grantees=["Thomas Varghese"],
                extent_cents=10.0,
                survey_no="412/3",
                consideration_inr=250000.0,
            ),
            DeedNode(
                doc_number="945/2018",
                year=2018,
                sro_name="Aluva",
                deed_type=DeedType.THEERADHARAM,
                grantors=["Thomas Varghese"],
                grantees=["Rajesh Kumar"],
                extent_cents=10.0,
                survey_no="412/3",
                consideration_inr=1500000.0,
            ),
        ]
        ec_records = [
            ECRecord(doc_number="412/1985", year=1985, sro_name="Aluva", nature="Pattayam"),
            ECRecord(doc_number="1890/2004", year=2004, sro_name="Aluva", nature="Sale"),
            ECRecord(doc_number="945/2018", year=2018, sro_name="Aluva", nature="Sale"),
        ]

        scorecard = self.auditor.audit(deeds, ec_records)
        self.assertEqual(scorecard.overall_score, 100)
        self.assertEqual(scorecard.risk_level, "CLEAN / LOW RISK")
        self.assertTrue(scorecard.chain_of_custody_intact)
        self.assertEqual(len(scorecard.risk_flags), 0)

    def test_succession_defect_omitted_daughter(self):
        """Test exclusion of daughter from Christian family partition (Mary Roy precedent)."""
        deeds = [
            DeedNode(
                doc_number="120/1992",
                year=1992,
                sro_name="Pala",
                deed_type=DeedType.BHAGAPATHRAM,
                grantors=["Kuruvilla (Deceased Estate)"],
                grantees=["Mathew Kuruvilla", "George Kuruvilla"],
                unrepresented_heirs=["Mary Kuruvilla (Sister / Daughter)"],
                family_religion="christian",
                extent_cents=15.0,
                survey_no="105/2",
            ),
            DeedNode(
                doc_number="650/2015",
                year=2015,
                sro_name="Pala",
                deed_type=DeedType.THEERADHARAM,
                grantors=["Mathew Kuruvilla"],
                grantees=["Current Buyer"],
                extent_cents=15.0,
                survey_no="105/2",
            ),
        ]

        scorecard = self.auditor.audit(deeds)
        self.assertLess(scorecard.overall_score, 70)
        flag_categories = [f.category for f in scorecard.risk_flags]
        self.assertIn("SUCCESSION_HEIR_EXCLUSION", flag_categories)
        succession_flag = next(f for f in scorecard.risk_flags if f.category == "SUCCESSION_HEIR_EXCLUSION")
        self.assertEqual(succession_flag.severity, RiskSeverity.CRITICAL)
        self.assertIn("Mary Roy", succession_flag.legal_citation)

    def test_extent_inflation_deficit(self):
        """Test extent inflation where seller conveys 12 cents from an 8-cent parent deed."""
        deeds = [
            DeedNode(
                doc_number="500/1990",
                year=1990,
                sro_name="Thrissur",
                deed_type=DeedType.DHANAM,
                grantors=["Velayudhan"],
                grantees=["Suresh"],
                extent_cents=8.0,
                survey_no="89/1",
            ),
            DeedNode(
                doc_number="1120/2021",
                year=2021,
                sro_name="Thrissur",
                deed_type=DeedType.THEERADHARAM,
                grantors=["Suresh"],
                grantees=["Buyer"],
                extent_cents=10.5,  # Inflated by 2.5 Cents
                survey_no="89/1",
            ),
        ]

        scorecard = self.auditor.audit(deeds)
        flag_categories = [f.category for f in scorecard.risk_flags]
        self.assertIn("EXTENT_INFLATION", flag_categories)
        inflation_flag = next(f for f in scorecard.risk_flags if f.category == "EXTENT_INFLATION")
        self.assertEqual(inflation_flag.severity, RiskSeverity.HIGH)
        self.assertIn("conveys more land", inflation_flag.title)

    def test_minor_rights_without_court_sanction(self):
        """Test transfer of minor's property without District Court sanction."""
        deeds = [
            DeedNode(
                doc_number="330/2010",
                year=2010,
                sro_name="Kochi",
                deed_type=DeedType.THEERADHARAM,
                grantors=["Lakshmi (Guardian on behalf of minor Rahul)"],
                grantees=["Investor"],
                extent_cents=5.0,
                survey_no="23/4",
                is_minor_involved=True,
                minor_court_sanction_present=False,
            )
        ]

        scorecard = self.auditor.audit(deeds)
        flag_categories = [f.category for f in scorecard.risk_flags]
        self.assertIn("MINOR_RIGHTS_VOIDABLE", flag_categories)
        minor_flag = next(f for f in scorecard.risk_flags if f.category == "MINOR_RIGHTS_VOIDABLE")
        self.assertEqual(minor_flag.severity, RiskSeverity.HIGH)
        self.assertIn("Hindu Minority and Guardianship Act", minor_flag.legal_citation)

    def test_buried_easement_and_ghost_ec_document(self):
        """Test detection of buried pathway easement and an undisclosed mortgage in EC."""
        deeds = [
            DeedNode(
                doc_number="810/1988",
                year=1988,
                sro_name="Kollam",
                deed_type=DeedType.THEERADHARAM,
                grantors=["Damodaran"],
                grantees=["Sreedharan"],
                extent_cents=12.0,
                survey_no="56/7",
                easements_reserved=["3-meter motorable pathway reserved for northern property"],
            )
        ]
        ec_records = [
            ECRecord(doc_number="810/1988", year=1988, sro_name="Kollam", nature="Sale"),
            ECRecord(doc_number="2140/2016", year=2016, sro_name="Kollam", nature="Equitable Mortgage - Canara Bank"),
        ]

        scorecard = self.auditor.audit(deeds, ec_records)
        flag_categories = [f.category for f in scorecard.risk_flags]
        self.assertIn("BURDEN_OR_EASEMENT", flag_categories)
        self.assertIn("GHOST_ENCUMBRANCE_IN_EC", flag_categories)
        ghost_flag = next(f for f in scorecard.risk_flags if f.category == "GHOST_ENCUMBRANCE_IN_EC")
        self.assertEqual(ghost_flag.severity, RiskSeverity.CRITICAL)


if __name__ == "__main__":
    unittest.main()
