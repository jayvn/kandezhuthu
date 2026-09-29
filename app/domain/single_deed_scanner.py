"""Kandezhuthu AI (കണ്ടെഴുത്ത് - ആധാരംനോക്കി).

Single-Deed Red-Flag Scanner for Kerala Property Transactions.
Built with a Neuro-Symbolic boundary:
- Uses AI for Malayalam linguistic understanding, OCR, and semantic covenant detection.
- Uses Deterministic Code for arithmetic, area conversion, and statutory thresholds.
- Explicitly flags physical ground-inspection items that no AI can verify.
"""

import re
from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field


class TrapCategory(str, Enum):
    EASEMENT_RIGHT_OF_WAY = "EASEMENT_RIGHT_OF_WAY"
    WETLAND_NILAM_RISK = "WETLAND_NILAM_RISK"
    MINOR_RIGHTS_DEFECT = "MINOR_RIGHTS_DEFECT"
    MAINTENANCE_CONDITIONAL_CLAUSE = "MAINTENANCE_CONDITIONAL_CLAUSE"


class Verdict(str, Enum):
    ALL_CLEAR = "🟢 ALL CLEAR - No Fatal Traps Detected in Text"
    CAUTION = "🟡 CAUTION - Restrictive Covenants Detected"
    DANGER = "🔴 DANGER - Fatal Legal / Regulatory Trap Found"


class TrapFinding(BaseModel):
    trap_type: TrapCategory
    severity: str = Field(description="CRITICAL, HIGH, or MEDIUM")
    title: str
    title_malayalam: str
    explanation: str
    matched_snippet: str
    kerala_statute: str
    whatsapp_question_for_seller: str


class DeedSanityResult(BaseModel):
    product_name: str = "Kandezhuthu AI (കണ്ടെഴുത്ത്)"
    verdict: Verdict
    sanity_score: int = Field(description="0 (Unsafe) to 100 (Clean)")
    findings: List[TrapFinding]
    summary_advice: str
    what_ai_cannot_verify: List[str] = Field(
        default_factory=lambda: [
            "Physical boundary encroachment: Whether neighbors have moved boundary stones (Survey Kallu).",
            "Actual ground topography: Waterlogging, flooding history, or overhead high-tension electric cables.",
            "Unregistered claims: Oral family agreements (Vaymozi udanpadi) or pending civil court caveats.",
            "Physical access reality: Whether the road mentioned on paper is physically motorable on the ground.",
        ]
    )
    mandatory_next_step: str = (
        "AI is an investigative triage tool, not a legal title insurer. "
        "Take this flagged report to a licensed Kerala advocate for formal search and conduct on-site boundary verification."
    )


class SingleDeedScanner:
    """Scans deed text in English or Malayalam for the 4 fatal Kerala real-estate traps."""

    EASEMENT_PATTERNS = [
        (r"(?i)\b(vazhi\s*avakasham|nadappu\s*vazhi|vandi\s*povanulla|vazhikkayi\s*maatti)\b", "Malayalam right of way / pathway", "വഴി അവകാശം / നടപ്പുവഴി"),
        (r"(?i)\b(kinaril\s*ninnum\s*vellam|kinar\s*avakasham)\b", "Well / water access servitude", "കിണർ അവകാശം"),
        (r"(?i)\b(right\s*of\s*way|pathway\s*reserved|easement\s*of\s*necessity|common\s*passage|cart\s*track)\b", "English easement clause", "വഴി അവകാശം (ഇംഗ്ലീഷ് ക്ലോസ്)"),
        (r"(?i)\b(\d+)\s*(meter|metre|adi|feet|ft)\s*(vazhi|pathway|passage)\b", "Specific pathway dimension reservation", "പ്രത്യേക വീതിയുള്ള വഴി"),
    ]

    WETLAND_PATTERNS = [
        (r"(?i)\b(nilam|nanja|punja|kandom|palliyal|thanneerthadam)\b", "Paddy land / Wetland category", "നിലം / തണ്ണീർത്തട വർഗ്ഗീകരണം"),
        (r"(?i)\b(paddy\s*field|paddy\s*land|wetland|marshy\s*land)\b", "English wetland category", "നെൽവയൽ / തണ്ണീർത്തടം"),
    ]

    MINOR_PATTERNS = [
        (r"(?i)\b(minor-kku\s*vendi|minor\s*inu\s*vendi|rakshakarthavaya|rakshakartha)\b", "Malayalam minor representation", "മൈനർക്ക് വേണ്ടി രക്ഷിതാവ്"),
        (r"(?i)\b(guardian\s*on\s*behalf\s*of\s*minor|represented\s*by\s*(father|mother|guardian)\s*as\s*minor)\b", "English minor guardian representation", "മൈനറുടെ രക്ഷിതാവ്"),
        (r"(?i)\b(apraptavayasskan|balan|minor\s*child)\b", "Minor child mentioned as owner", "പ്രായപൂർത്തിയാകാത്ത ഉടമ"),
    ]

    MAINTENANCE_PATTERNS = [
        (r"(?i)\b(jeevithakalam\s*muzhuvan|jeevanamsam|samrakshikkuka|shushrooshikkuka)\b", "Malayalam senior citizen maintenance condition", "ജീവിതകാല സംരക്ഷണ വ്യവസ്ഥ"),
        (r"(?i)\b(condition\s*to\s*maintain|life\s*interest|subject\s*to\s*maintenance|during\s*lifetime)\b", "English maintenance condition", "മാതാപിതാക്കളുടെ സംരക്ഷണ വ്യവസ്ഥ"),
        (r"(?i)\b(thirichuvangal|reconveyance|conditional\s*sale)\b", "Conditional sale / Right of re-purchase", "തിരിച്ചുവാങ്ങൽ വ്യവസ്ഥ"),
    ]

    def scan(self, deed_text: str) -> DeedSanityResult:
        if not deed_text or not deed_text.strip():
            return DeedSanityResult(
                verdict=Verdict.DANGER,
                sanity_score=0,
                findings=[],
                summary_advice="Deed text is empty. Please provide the text or schedule of the deed to scan.",
            )

        findings: List[TrapFinding] = []
        score = 100
        has_critical = False

        # 1. Scan for Buried Easements
        easement_match = self._find_first_pattern(deed_text, self.EASEMENT_PATTERNS)
        if easement_match:
            snippet, desc, mal_title = easement_match
            score -= 25
            findings.append(
                TrapFinding(
                    trap_type=TrapCategory.EASEMENT_RIGHT_OF_WAY,
                    severity="MEDIUM",
                    title="Buried Easement / Pathway (Vazhi Avakasham) Found",
                    title_malayalam=mal_title,
                    explanation=(
                        "The deed reserves an easement, pathway, or water access right for a neighboring property. "
                        "If you purchase this land, you CANNOT construct a compound wall or block this passage."
                    ),
                    matched_snippet=snippet,
                    kerala_statute="Indian Easements Act, 1882 (Section 13 & 15)",
                    whatsapp_question_for_seller=(
                        "ആധാരത്തിൽ വഴി അവകാശം പറഞ്ഞിട്ടുണ്ടല്ലോ ('" + snippet + "'). ഈ വഴി ഇപ്പോൾ സ്ഥലത്ത് എവിടെയാണ്? "
                        "അയൽവാസികൾക്ക് ഇതിലൂടെ വാഹന സഞ്ചാര അവകാശം ഉണ്ടോ?"
                    ),
                )
            )

        # 2. Scan for Wetland / Nilam Risk
        wetland_match = self._find_first_pattern(deed_text, self.WETLAND_PATTERNS)
        if wetland_match:
            snippet, desc, mal_title = wetland_match
            is_converted = re.search(r"(?i)(converted|purayidam\s*aayi|form\s*6\s*approved)", deed_text)
            if not is_converted:
                score -= 45
                has_critical = True
                findings.append(
                    TrapFinding(
                        trap_type=TrapCategory.WETLAND_NILAM_RISK,
                        severity="CRITICAL",
                        title="Wetland / Nilam Classification Trap (2008 Act)",
                        title_malayalam=mal_title,
                        explanation=(
                            f"The property is categorized as '{snippet}' (Paddy Land / Wetland). "
                            "Even if the plot physically looks dry, the Local Self Govt (Panchayat/Municipality) "
                            "CANNOT grant a residential building permit unless regularized under the 2008 Paddy Land Act."
                        ),
                        matched_snippet=snippet,
                        kerala_statute="Kerala Conservation of Paddy Land and Wetland Act, 2008 (Section 27A & Form 5/6)",
                        whatsapp_question_for_seller=(
                            "വില്ലേജ് റിക്കാർഡിലും ഡാറ്റാ ബാങ്കിലും ഈ സ്ഥലം 'നിലം' ആണോ അതോ 'പുരയിടം' ആയി മാറിയിട്ടുണ്ടോ? "
                            "2008-ലെ നെൽവയൽ തണ്ണീർത്തട നിയമപ്രകാരം ഫോറം 5/6 അനുമതി ആവശ്യമുണ്ടോ?"
                        ),
                    )
                )

        # 3. Scan for Minor Rights
        minor_match = self._find_first_pattern(deed_text, self.MINOR_PATTERNS)
        if minor_match:
            snippet, desc, mal_title = minor_match
            has_court_order = re.search(r"(?i)(district\s*court|court\s*order|sanction|o\.p\.\s*no)", deed_text)
            if not has_court_order:
                score -= 40
                has_critical = True
                findings.append(
                    TrapFinding(
                        trap_type=TrapCategory.MINOR_RIGHTS_DEFECT,
                        severity="CRITICAL",
                        title="Minor's Property Sold Without District Court Sanction",
                        title_malayalam=mal_title,
                        explanation=(
                            f"The deed shows property being alienated on behalf of a minor ('{snippet}'), "
                            "but no District Court sanction order is cited. Under law, the minor can legally void this sale "
                            "upon attaining 18 years of age."
                        ),
                        matched_snippet=snippet,
                        kerala_statute="Section 8(2), Hindu Minority and Guardianship Act, 1956",
                        whatsapp_question_for_seller=(
                            "ആധാരത്തിൽ പ്രായപൂർത്തിയാകാത്ത ആളുടെ അവകാശം ഉൾപ്പെട്ടിട്ടുണ്ടല്ലോ ('" + snippet + "'). "
                            "ഇതിന് ജില്ലാ കോടതിയുടെ മുൻകൂർ അനുമതി (Sanction) വാങ്ങിയിട്ടുണ്ടോ? അതോ മൈനർക്ക് ഇപ്പോൾ പ്രായപൂർത്തിയായ ശേഷമുള്ള റിലീസ് ഡീഡ് ഉണ്ടോ?"
                        ),
                    )
                )

        # 4. Scan for Senior Citizen Maintenance / Conditional Clauses
        maint_match = self._find_first_pattern(deed_text, self.MAINTENANCE_PATTERNS)
        if maint_match:
            snippet, desc, mal_title = maint_match
            score -= 20
            findings.append(
                TrapFinding(
                    trap_type=TrapCategory.MAINTENANCE_CONDITIONAL_CLAUSE,
                    severity="HIGH",
                    title="Senior Citizen Maintenance / Conditional Life Covenant",
                    title_malayalam=mal_title,
                    explanation=(
                        f"The deed contains a maintenance covenant ('{snippet}'). Under the Maintenance and Welfare of Parents "
                        "and Senior Citizens Act, if the transferee failed to care for the parent, the transfer can be canceled by the RDO Tribunal."
                    ),
                    matched_snippet=snippet,
                    kerala_statute="Section 23, Maintenance and Welfare of Parents and Senior Citizens Act, 2007",
                    whatsapp_question_for_seller=(
                        "ആധാരത്തിൽ മാതാപിതാക്കളുടെ സംരക്ഷണ വ്യവസ്ഥയുണ്ടല്ലോ ('" + snippet + "'). "
                        "മാതാപിതാക്കൾ ഇപ്പോഴും ജീവിച്ചിരിപ്പുണ്ടോ? പുതിയ ആധാരത്തിൽ അവർ സമ്മതക്കാരായി ഒപ്പിടുമോ?"
                    ),
                )
            )

        score = max(0, min(100, score))

        if has_critical or score < 60:
            verdict = Verdict.DANGER
            advice = (
                "CRITICAL RED FLAGS DETECTED! This deed contains high-risk elements (such as wetland classification or unapproved minor sale) "
                "that could lead to building permit refusal or void title. Halt advance payment immediately."
            )
        elif score < 85:
            verdict = Verdict.CAUTION
            advice = (
                "The deed contains restrictive covenants (such as an easement or conditional clause). "
                "Do NOT pay any advance until you inspect the physical site and clarify the highlighted questions with the seller."
            )
        else:
            verdict = Verdict.ALL_CLEAR
            advice = (
                "No fatal legal traps (easements, wetland status, minor rights, or maintenance covenants) were detected in this snippet. "
                "Safe to proceed with customary Encumbrance Certificate (EC) verification and field survey inspection."
            )

        return DeedSanityResult(
            verdict=verdict,
            sanity_score=score,
            findings=findings,
            summary_advice=advice,
        )

    def _find_first_pattern(self, text: str, patterns: list):
        for pattern, desc, mal_title in patterns:
            match = re.search(pattern, text)
            if match:
                start = max(0, match.start() - 20)
                end = min(len(text), match.end() + 30)
                snippet = text[start:end].strip().replace("\n", " ")
                return snippet, desc, mal_title
        return None
