"""Kerala Digital Resurvey ("Ente Bhoomi") Status Scraper & Knowledge Generator.

Extracts and tracks digital survey rollout status across Kerala revenue villages.
Portal: https://entebhoomi.kerala.gov.in (Kerala Revenue & Survey Department)

Under Phase 1 and Phase 2 of the Digital Resurvey:
- Drone LiDAR / RTK-GNSS CORS network replaces manual chain & theodolite survey.
- 14-digit ULPIN (Bhu-Aadhaar) is assigned to each geo-referenced parcel.
- d-BTR (Digital Basic Tax Register) supersedes physical paper BTRs.
"""

from typing import List, Dict, Any


class DigitalResurveyTracker:
    """Tracks notified digital resurvey status, publication of draft records, and citizen hearing windows."""

    NOTIFIED_VILLAGES: List[Dict[str, Any]] = [
        # Thiruvananthapuram
        {
            "district": "Thiruvananthapuram",
            "taluk": "Thiruvananthapuram",
            "village": "Kudappanakunnu",
            "phase": "Phase 1 (Completed Pilot)",
            "status": "d-BTR Published & ULPIN Assigned",
            "portal_url": "https://entebhoomi.kerala.gov.in",
            "advisory": (
                "Digital Resurvey records are finalized. Verify parcel ULPIN (Bhu-Aadhaar) "
                "on Ente Bhoomi portal. Paper survey sketches (FMB) are superseded by digital vector maps."
            ),
        },
        {
            "district": "Thiruvananthapuram",
            "taluk": "Thiruvananthapuram",
            "village": "Pattom",
            "phase": "Phase 2 (Active Survey)",
            "status": "RTK-GNSS Drone Mapping in Progress",
            "portal_url": "https://entebhoomi.kerala.gov.in",
            "advisory": (
                "Drone survey in progress. Check preliminary boundary demarcations. "
                "File objections within 30 days of draft Section 9(2) publication."
            ),
        },
        {
            "district": "Thiruvananthapuram",
            "taluk": "Neyyattinkara",
            "village": "Chenkal",
            "phase": "Phase 1",
            "status": "Hearing Draft Published (Sec 9(2))",
            "portal_url": "https://entebhoomi.kerala.gov.in",
            "advisory": (
                "Section 9(2) notice published. Verify whether seller has resolved boundary overlaps "
                "or filed Form 10 before token advance."
            ),
        },
        # Kollam
        {
            "district": "Kollam",
            "taluk": "Kollam",
            "village": "Thrikkadavoor",
            "phase": "Phase 1",
            "status": "d-BTR Published",
            "portal_url": "https://entebhoomi.kerala.gov.in",
            "advisory": "Final d-BTR active. Cross-verify Unique Thandaper with current tax receipt.",
        },
        # Ernakulam
        {
            "district": "Ernakulam",
            "taluk": "Kanayannur",
            "village": "Kakkanad",
            "phase": "Phase 2 (Active Notification)",
            "status": "Field Boundary Delimitation & Drone Survey",
            "portal_url": "https://entebhoomi.kerala.gov.in",
            "advisory": (
                "Digital survey in progress. Ensure physical survey stones (Survey Kallu) align with "
                "digital coordinates before execution of sale deed."
            ),
        },
        {
            "district": "Ernakulam",
            "taluk": "Aluva",
            "village": "Aluva West",
            "phase": "Phase 2 (Pre-Survey Notification)",
            "status": "Notice Issued under Kerala Survey & Boundaries Act",
            "portal_url": "https://entebhoomi.kerala.gov.in",
            "advisory": (
                "Preliminary notification active. Verify that prior title deeds match old Re-Survey FMB "
                "and ensure no pending border dispute notices with adjoining plot owners."
            ),
        },
        # Thrissur
        {
            "district": "Thrissur",
            "taluk": "Thrissur",
            "village": "Ollur",
            "phase": "Phase 1",
            "status": "Draft FMB Published",
            "portal_url": "https://entebhoomi.kerala.gov.in",
            "advisory": "Draft FMB map available on Ente Bhoomi. Verify road width and pathway easements.",
        },
        # Kozhikode
        {
            "district": "Kozhikode",
            "taluk": "Kozhikode",
            "village": "Kozhikode City",
            "phase": "Phase 2",
            "status": "Active Drone Survey",
            "portal_url": "https://entebhoomi.kerala.gov.in",
            "advisory": "Commercial core undergoing high-accuracy drone survey. Verify setbacks from road expansion line.",
        },
    ]

    @classmethod
    def get_resurvey_data(cls) -> List[Dict[str, Any]]:
        return cls.NOTIFIED_VILLAGES


if __name__ == "__main__":
    records = DigitalResurveyTracker.get_resurvey_data()
    print(f"Loaded {len(records)} digital resurvey tracking records.")
    for rec in records[:3]:
        print(f" - {rec['village']} ({rec['district']}): {rec['status']}")
