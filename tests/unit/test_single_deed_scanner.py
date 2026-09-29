"""Unit tests for Single-Deed Red-Flag Scanner ('DeedSanity Kerala')."""

import unittest
from app.domain.single_deed_scanner import (
    SingleDeedScanner,
    Verdict,
    TrapCategory,
)


class TestSingleDeedScanner(unittest.TestCase):

    def setUp(self):
        self.scanner = SingleDeedScanner()

    def test_clean_purayidam_deed(self):
        """Test a clean residential purayidam deed without any traps."""
        deed_text = """
        Schedule of Property:
        District: Ernakulam, Taluk: Aluva, Village: Aluva West.
        Re-Survey No: 412/3, Extent: 10 Cents of Purayidam (garden land with coconut trees).
        Boundaries:
        East: Property of Ramanathan
        West: PWD Road
        South: Property of Varghese
        North: Property of Soman
        Absolute ownership with clear title, free from all encumbrances.
        """
        result = self.scanner.scan(deed_text)
        self.assertEqual(result.verdict, Verdict.ALL_CLEAR)
        self.assertEqual(result.sanity_score, 100)
        self.assertEqual(len(result.findings), 0)

    def test_buried_easement_vazhi_avakasham(self):
        """Test detection of buried pathway reservation for neighbor."""
        deed_text = """
        Schedule:
        Re-Sy 105/4, Extent 8 Cents Purayidam.
        Special Covenant: The purchaser shall permit the owner of the eastern property
        to use a 3-meter nadappu vazhi (right of way) along the southern boundary for vehicle access.
        """
        result = self.scanner.scan(deed_text)
        self.assertEqual(result.verdict, Verdict.CAUTION)
        self.assertEqual(result.sanity_score, 75)
        self.assertEqual(len(result.findings), 1)
        self.assertEqual(result.findings[0].trap_type, TrapCategory.EASEMENT_RIGHT_OF_WAY)
        self.assertIn("Indian Easements Act", result.findings[0].kerala_statute)

    def test_nilam_wetland_trap(self):
        """Test detection of Nilam (paddy land) classification under 2008 Act."""
        deed_text = """
        Sale Deed No. 1204/2019:
        Conveyance of all that piece of land measuring 12 Cents in Re-Sy 89/2,
        described in revenue records as Nilam (Kandom), presently cultivated with plantains.
        """
        result = self.scanner.scan(deed_text)
        self.assertEqual(result.verdict, Verdict.DANGER)
        self.assertLessEqual(result.sanity_score, 60)
        self.assertEqual(len(result.findings), 1)
        self.assertEqual(result.findings[0].trap_type, TrapCategory.WETLAND_NILAM_RISK)
        self.assertIn("5/6", result.findings[0].whatsapp_question_for_seller)

    def test_minor_rights_without_court_sanction(self):
        """Test detection of minor's interest alienated without District Court order."""
        deed_text = """
        This deed of sale executed by Smt. Kamala, acting as mother and natural guardian
        on behalf of minor child master Adarsh, aged 11 years, conveying their undivided 5 Cents share.
        """
        result = self.scanner.scan(deed_text)
        self.assertEqual(result.verdict, Verdict.DANGER)
        self.assertEqual(result.findings[0].trap_type, TrapCategory.MINOR_RIGHTS_DEFECT)
        self.assertIn("Hindu Minority and Guardianship Act", result.findings[0].kerala_statute)

    def test_senior_citizen_maintenance_condition(self):
        """Test detection of conditional gift subject to lifelong maintenance."""
        deed_text = """
        Dhanam (Gift) Deed:
        Executed by Velayudhan in favour of son Suresh.
        Subject to the explicit condition that the donee shall provide samrakshikkuka
        and food during jeevithakalam muzhuvan of the donor.
        """
        result = self.scanner.scan(deed_text)
        self.assertEqual(result.verdict, Verdict.CAUTION)
        self.assertEqual(result.findings[0].trap_type, TrapCategory.MAINTENANCE_CONDITIONAL_CLAUSE)
        self.assertIn("Senior Citizens Act", result.findings[0].kerala_statute)


if __name__ == "__main__":
    unittest.main()
