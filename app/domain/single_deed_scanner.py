"""Kandezhuthu AI (കണ്ടെഴുത്ത് - ആധാരംനോക്കി).

Single-Deed Red-Flag Scanner for Kerala Property Transactions.
Built with a Neuro-Symbolic boundary:
- Uses AI for Malayalam linguistic understanding, OCR, and semantic covenant detection.
- Uses Deterministic Code for arithmetic, area conversion, and statutory thresholds.
- Explicitly flags physical ground-inspection items that no AI can verify.
"""

from __future__ import annotations

import re
import unicodedata
from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field

from app.domain.extent_converter import (
    parse_extents_from_text,
    verify_internal_extent_consistency,
)


class TrapCategory(str, Enum):
    EASEMENT_RIGHT_OF_WAY = "EASEMENT_RIGHT_OF_WAY"
    WETLAND_NILAM_RISK = "WETLAND_NILAM_RISK"
    MINOR_RIGHTS_DEFECT = "MINOR_RIGHTS_DEFECT"
    MAINTENANCE_CONDITIONAL_CLAUSE = "MAINTENANCE_CONDITIONAL_CLAUSE"
    EXTENT_INFLATION_DISCREPANCY = "EXTENT_INFLATION_DISCREPANCY"
    CRZ_COASTAL_REGULATION_RISK = "CRZ_COASTAL_REGULATION_RISK"
    TRUST_DEVASWOM_WAQF_ALIENATION = "TRUST_DEVASWOM_WAQF_ALIENATION"


class Verdict(str, Enum):
    ALL_CLEAR = "● NO KNOWN RED FLAGS - Lawyer Review Still Required"
    CAUTION = "▲ CAUTION - Restrictive Covenants Detected"
    DANGER = "■ DANGER - Fatal Legal / Regulatory Trap Found"


class TrapFinding(BaseModel):
    trap_type: TrapCategory
    severity: str = Field(description="CRITICAL, HIGH, or MEDIUM")
    title: str
    title_malayalam: str
    explanation: str
    matched_snippet: str
    kerala_statute: str
    whatsapp_question_for_seller: str
    whatsapp_question_for_seller_en: str = ""


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
            "Digital resurvey discrepancy: Cross-check ULPIN (Bhu-Aadhaar) and Unique Thandaper on entebhoomi.kerala.gov.in.",
        ]
    )
    mandatory_next_step: str = (
        "AI is an investigative triage tool, not a legal title insurer. "
        "Take this flagged report to a licensed Kerala advocate for formal search and conduct on-site boundary verification."
    )


class SingleDeedScanner:
    """Scans deed text in English or Malayalam for fatal Kerala real-estate traps."""

    EASEMENT_PATTERNS = [
        # Malayalam script patterns
        (r"(നടപ്പുവഴി|നടപുവഴി|വഴിയവകാശം|വഴി\s*അവകാശം|വണ്ടിവഴി|വണ്ടിപ്പാത|വണ്ടിയോടാനുള്ള\s*വഴി|സഞ്ചാര\s*സ്വാതന്ത്ര്യം|സഞ്ചാര\s*മാർഗ്ഗം|വഴിയായി\s*മാറ്റി|വഴിയായി\s*ഒഴിഞ്ഞു)", "Malayalam right of way / pathway", "വഴി അവകാശം / നടപ്പുവഴി"),
        (r"(പോക്കുവരവി(?:നു|ന്)(?:ള്ള)?\s*(?:വഴി|അവകാശ)|പോക്കുവരവ്\s*(?:വഴി|അവകാശം))", "Malayalam passage (pokkuvaravu) right", "പോക്കുവരവിനുള്ള വഴി അവകാശം"),
        (r"(കിണർ\s*അവകാശം|കിണറ്റിൽ\s*നിന്നു[ംള]|വെള്ളമെടുക്കാനുള്ള\s*അവകാശം)", "Malayalam well / water servitude", "കിണർ അവകാശം"),
        (r"(\d+(?:\.\d+)?)\s*(മീറ്റർ|മീ|അടി)\s*(വീതിയിലുള്ള\s*)?(നടപ്പുവഴി|വഴി|പാത)", "Malayalam pathway dimension covenant", "പ്രത്യേക വീതിയുള്ള വഴി"),
        # KSEB electric line / transmission corridor servitude
        (r"(വൈദ്യുതി\s*ലൈൻ\s*(?:പോകുന്നതിനുള്ള\s*)?അവകാശം|വൈദ്യുതി\s*ലൈൻ|കെ\.?എസ്\.?ഇ\.?ബി|ഇലക്ട്രിക്\s*ലൈൻ\s*അവകാശം)", "Malayalam KSEB electric transmission corridor easement", "വൈദ്യുതി ലൈൻ അവകാശം / KSEB കോറിഡോർ"),
        # Transliterated / English patterns
        (r"(?i)\b(vazhi\s*avakasham|nadappu\s*vazhi|nadapu\s*vazhi|nadappuvazh[yi]|vandi\s*povanulla|vazhikkayi\s*maatti)\b", "Malayalam transliterated right of way", "വഴി അവകാശം / നടപ്പുവഴി"),
        (r"(?i)\b(kinaril\s*ninnum\s*vellam|kinar\s*avakasham)\b", "Well / water access servitude", "കിണർ അവകാശം"),
        (r"(?i)\b(right\s*of\s*way|pathway\s*reserved|easement\s*of\s*necessity|common\s*passage|cart\s*track|foot\s*path)\b", "English easement clause", "വഴി അവകാശം (ഇംഗ്ലീഷ് ക്ലോസ്)"),
        (r"(?i)(\d+(?:\.\d+)?)\s*(meter|metre|adi|feet|ft)\s*(vazhi|pathway|passage|road)", "Specific pathway dimension reservation", "പ്രത്യേക വീതിയുള്ള വഴി"),
        (r"(?i)\b(kseb|k\.s\.e\.b|electric\s*(?:transmission\s*)?line(?:\s*easement)?|transmission\s*corridor|high\s*tension\s*line|power\s*line\s*corridor)\b", "KSEB transmission line corridor easement", "വൈദ്യുതി ലൈൻ അവകാശം / KSEB കോറിഡോർ"),
    ]

    CRZ_PATTERNS = [
        # Malayalam script patterns
        (r"(തീരദേശ\s*പരിപാലന\s*നിയമം|തീരദേശ\s*നിയന്ത്രണ\s*മേഖല|തീരദേശ\s*പരിപാലനം|സി\.?ആർ\.?ഇസെഡ്|CRZ|തീരദേശ\s*ബഫർ|കായൽത്തീര\s*ബഫർ|തീരദേശ\s*പരിധി)", "Malayalam CRZ coastal regulation zone", "തീരദേശ പരിപാലന നിയമം (CRZ) നിയന്ത്രണം"),
        # Transliterated / English patterns
        (r"(?i)\b(coastal\s*regulation\s*zone|crz(?:\s*setback|\s*buffer|\s*clearance|\s*regulations?)?|no\s*development\s*zone|ndz\s*buffer|coastal\s*buffer\s*zone|tidal\s*watercourse\s*buffer)\b", "CRZ coastal regulation zone restriction", "തീരദേശ പരിപാലന നിയമം (CRZ) നിയന്ത്രണം"),
    ]

    TRUST_ALIENATION_PATTERNS = [
        # Malayalam script patterns
        (r"(വഖഫ്\s*(?:സ്വത്ത്|ബോർഡ്|ഭൂമി|വക)|ദേവസ്വം\s*(?:സ്വത്ത്|ബോർഡ്|ഭൂമി|വക|ട്രസ്റ്റ്)|ക്ഷേത്ര\s*സ്വത്ത്|ക്ഷേത്ര\s*ട്രസ്റ്റ്|പള്ളി\s*വക\s*സ്വത്ത്|ട്രസ്റ്റ്\s*വക\s*സ്വത്ത്|അന്യാധീനപ്പെടുത്താൻ\s*പാടില്ലാത്ത|കൈമാറ്റ\s*വിലക്ക്)", "Malayalam Waqf / Devaswom trust property alienation restriction", "വഖഫ് / ദേവസ്വം ട്രസ്റ്റ് സ്വത്ത് കൈമാറ്റ നിരോധനം"),
        # Transliterated / English patterns
        (r"(?i)\b(waqf(?:\s*property|\s*board|\s*land)?|wakf|devaswom(?:\s*property|\s*board|\s*trust|\s*land)?|temple\s*trust\s*property|mosque\s*property|religious\s*trust\s*property|inalienable\s*trust|bar\s*on\s*alienation|trust\s*property\s*alienation)\b", "Waqf / Devaswom trust property alienation restriction", "വഖഫ് / ദേവസ്വം ട്രസ്റ്റ് സ്വത്ത് കൈമാറ്റ നിരോധനം"),
    ]

    WETLAND_PATTERNS = [
        # Malayalam script patterns
        (r"(നിലം|നഞ്ചനിലം|നഞ്ച\s*നിലം|നഞ്ച|പുഞ്ചനിലം|പുഞ്ച\s*നിലം|പുഞ്ച|കണ്ടം|നെൽവയൽ|നെല്വയല്|തണ്ണീർത്തടം|പള്ളിയാൽ)", "Malayalam Paddy land / Wetland category", "നിലം / തണ്ണീർത്തട വർഗ്ഗീകരണം"),
        # Malayalam OCR noise / typos (e.g. നില without anusvara ം in context of land classification)
        (r"(നഞ്ച\s*നില|പുഞ്ച\s*നില|തരം\s*[:\s]*നില|വർഗ്ഗീകരണം\s*[:\s]*നില|ഭൂമി\s*[:\s]*നില)", "Noisy OCR Nilam classification", "നിലം (OCR പിശക്)"),
        # Transliterated / English patterns
        (r"(?i)\b(nilam|nanja|punja|kandom|palliyal|thanneerthadam|nilan|kandam)\b", "Paddy land / Wetland category", "നിലം / തണ്ണീർത്തട വർഗ്ഗീകരണം"),
        (r"(?i)\b(paddy\s*field|paddy\s*land|wet\s*land|marshy\s*land|waterlogged\s*land)\b", "English wetland category", "നെൽവയൽ / തണ്ണീർത്തടം"),
    ]

    MINOR_PATTERNS = [
        # Malayalam script patterns
        (r"(മൈനർക്ക്\s*വേണ്ടി|മൈനറുടെ\s*കാര്യത്തിന്|മൈനർ\s*മകൾ|മൈനർ\s*മകൻ|മൈനർ\s*അവകാശം|മൈനർ\s*സ്വത്ത്|അപ്രാപ്ത\s*വയസ്ക|പ്രായപൂർത്തിയാകാത്ത|മൈനർ)", "Malayalam minor representation", "മൈനർക്ക് വേണ്ടി രക്ഷിതാവ്"),
        (r"(മാതാവും\s*സ്വാഭാവിക\s*രക്ഷാകർത്താവും|പിതാവും\s*സ്വാഭാവിക\s*രക്ഷാകർത്താവും|രക്ഷാകർത്താവ)", "Malayalam guardian clause", "രക്ഷാകർത്താവ് മുഖേന"),
        # Transliterated / English patterns
        (r"(?i)\b(minor-kku\s*vendi|minor\s*inu\s*vendi|rakshakarthavaya|rakshakartha|apraptavayasskan)\b", "Malayalam transliterated minor representation", "മൈനർക്ക് വേണ്ടി രക്ഷിതാവ്"),
        (r"(?i)\b(guardian\s*on\s*behalf\s*of\s*minor|represented\s*by\s*(?:father|mother|guardian)\s*as\s*minor)\b", "English minor guardian representation", "മൈനറുടെ രക്ഷിതാവ്"),
        (r"(?i)\b(minor\s*(?:child|daughter|son|children|interest|share|property|owner)|on\s*behalf\s*of\s*(?:her|his)?\s*minor)\b", "Minor child mentioned as owner", "പ്രായപൂർത്തിയാകാത്ത ഉടമ"),
        (r"(?i)\b(?:mother|father|guardian)\s*selling\s*minor(?:'s|\s+daughter|\s+son)?\b", "Parent selling minor property", "മൈനറുടെ സ്വത്ത് വിൽക്കൽ"),
        (r"(?<![\d.])(?:[1-9]|1[0-7])\s*വയസ്സ", "Malayalam party aged under 18", "പ്രായപൂർത്തിയാകാത്ത കക്ഷി"),
        (r"(?i)\baged\s*(?:about\s*)?(?:[1-9]|1[0-7])\b(?!\s*(?:cents|ares|sq))", "Party aged under 18", "പ്രായപൂർത്തിയാകാത്ത കക്ഷി"),
        (r"(?i)\b((?:mother|father)\s*and\s*(?:natural\s*)?guardian|natural\s*guardian)\b", "Natural guardian clause", "സ്വാഭാവിക രക്ഷാകർത്താവ്"),
        (r"(?i)\b(natural\s*guardian\s*on\s*behalf\s*of|acting\s*as\s*(?:mother|father|natural)\s*guardian)\b", "Natural guardian representation", "സ്വാഭാവിക രക്ഷാകർത്താവ്"),
    ]

    MAINTENANCE_PATTERNS = [
        # Malayalam script patterns
        (r"(ജീവിതകാലം\s*മുഴുവൻ|ജീവിതകാലത്ത്|ജീവനാംശം|സംരക്ഷിക്കേണ്ടതാണ്|ശുശ്രൂഷിക്കേണ്ടതാണ്|സംരക്ഷിക്കണമെന്ന\s*വ്യവസ്ഥ|നോക്കിക്കൊള്ളണം)", "Malayalam senior citizen maintenance condition", "ജീവിതകാല സംരക്ഷണ വ്യവസ്ഥ"),
        (r"(മാതാപിതാക്കളെ\s*(?:സംരക്ഷിക്ക|നോക്ക|ശുശ്രൂഷിക്ക)|മാതാപിതാക്കളുടെ\s*സംരക്ഷണം|വൃദ്ധരായ\s*മാതാപിതാക്കൾ)", "Malayalam parental maintenance condition", "മാതാപിതാക്കളുടെ സംരക്ഷണ വ്യവസ്ഥ"),
        (r"(ആധാരം\s*റദ്ദാക്ക|റദ്ദാക്കാൻ\s*അധികാരം|റദ്ദ്\s*ചെയ്യ|തിരിച്ചുവാങ്ങൽ|വ്യവസ്ഥ\s*ലംഘിച്ചാൽ\s*റദ്ദ്|ദാനാധാരം\s*റദ്ദ്)", "Malayalam deed revocation / cancellation clause", "ആധാരം റദ്ദാക്കൽ വ്യവസ്ഥ"),
        # Transliterated / English patterns
        (r"(?i)\b(jeevithakalam\s*muzhuvan|jeevanamsam|samrakshikkuka|samrakshikuka|shushrooshikkuka)\b", "Malayalam transliterated maintenance condition", "ജീവിതകാല സംരക്ഷണ വ്യവസ്ഥ"),
        (r"(?i)\b(condition\s*to\s*maintain|condition\s*of\s*looking\s*after|look\s*after\s*(?:elderly\s*)?parents|look\s*after\s*the\s*(?:settlor|donor|executant|vendor)s?|maintain\s*(?:elderly\s*)?parents|elderly\s*parents)\b", "English maintenance condition", "മാതാപിതാക്കളുടെ സംരക്ഷണ വ്യവസ്ഥ"),
        (r"(?i)\b(life\s*interest|subject\s*to\s*maintenance|during\s*(?:their|her|his|my)?\s*lifetime|lifelong\s*maintenance|care\s*and\s*maintenance)\b", "English lifetime maintenance clause", "ജീവിതകാല സംരക്ഷണ വ്യവസ്ഥ"),
        (r"(?i)\b(deed\s*cancellation|cancel\s*(?:the\s*)?deed|clause\s*allowing\s*(?:deed\s*)?cancellation|cancellation\s*clause|power\s*to\s*revoke|revocation\s*clause|revoking\s*the\s*gift)\b", "Deed cancellation / Revocation clause", "ആധാരം റദ്ദാക്കൽ വ്യവസ്ഥ"),
        (r"(?i)\b(thirichuvangal|reconveyance|conditional\s*sale|conditional\s*gift)\b", "Conditional sale / Right of re-purchase", "തിരിച്ചുവാങ്ങൽ വ്യവസ്ഥ"),
    ]

    # Pre-2009 Malayalam encodes chillu as consonant + virama + ZWJ; OCR and
    # older deeds still produce it. Map to atomic chillu so patterns match.
    _CHILLU_MAP = {
        "\u0d23\u0d4d\u200d": "\u0d7a",  # ണ് -> ൺ
        "\u0d28\u0d4d\u200d": "\u0d7b",  # ന് -> ൻ
        "\u0d30\u0d4d\u200d": "\u0d7c",  # ര് -> ർ
        "\u0d32\u0d4d\u200d": "\u0d7d",  # ല് -> ൽ
        "\u0d33\u0d4d\u200d": "\u0d7e",  # ള് -> ൾ
        "\u0d15\u0d4d\u200d": "\u0d7f",  # ക് -> ൿ
    }
    _NEGATION_BEFORE = re.compile(
        r"(?i)\b(?:no|not|nor|without|free\s+from|devoid\s+of)\s+(?:\w+\s+){0,3}$"
    )

    @classmethod
    def normalize(cls, text: str) -> str:
        text = unicodedata.normalize("NFC", text)
        for old, new in cls._CHILLU_MAP.items():
            text = text.replace(old, new)
        return text.replace("\u200d", "").replace("\u200c", "")

    def scan(self, deed_text: str) -> DeedSanityResult:
        deed_text = self.normalize(deed_text or "")
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
                    whatsapp_question_for_seller_en=(
                        f"The deed specifically reserves an easement pathway right ('{snippet}'). "
                        "Could you please clarify where this pathway is physically located on the ground, "
                        "and whether neighboring owners hold vehicular access rights through it?"
                    ),
                )
            )

        # 2. Scan for Wetland / Nilam Risk
        wetland_match = self._find_first_pattern(deed_text, self.WETLAND_PATTERNS)
        if wetland_match:
            snippet, desc, mal_title = wetland_match
            # Check if conversion is negated (e.g. "without Form 6 approval", "not converted")
            conversion_negated = re.search(
                r"(?i)\b(without|no|not|pending|awaiting|lacking)\s+(?:any\s+)?(?:form\s*6|sec(?:tion)?\s*27a|conversion|regulariz)\b|"
                r"(ഫോറം\s*6\s*അനുമതിയില്ലാതെ|മാറ്റാത്ത|പരിവർത്തനം\s*ചെയ്യാത്ത)",
                deed_text,
            )
            is_converted = False
            if not conversion_negated:
                is_converted = bool(re.search(
                    r"(?i)(form\s*6\s*(?:approved|order|sanction)|sec(?:tion)?\s*27a\s*(?:order|sanction|approval)|"
                    r"27a\s*regulariz|order\s*under\s*sec(?:tion)?\s*27a|ഫോറം\s*6\s*(?:ഉത്തരവ്|അംഗീകാരം|അനുമതി)|"
                    r"27\s*എ\s*ഉത്തരവ്|purayidam\s*aayi\s*maattiya|converted\s*under\s*form\s*6)",
                    deed_text,
                ))
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
                        kerala_statute="Kerala Conservation of Paddy Land and Wetland Act, 2008 (Section 27A, Form 5/6 & Act 12 of 2024)",
                        whatsapp_question_for_seller=(
                            "വില്ലേജ് റിക്കാർഡിലും ഡാറ്റാ ബാങ്കിലും ഈ സ്ഥലം 'നിലം' ആണോ അതോ 'പുരയിടം' ആയി മാറിയിട്ടുണ്ടോ? "
                            "2008-ലെ നെൽവയൽ തണ്ണീർത്തട നിയമപ്രകാരം ഫോറം 5/6 അനുമതി ആവശ്യമുണ്ടോ?"
                        ),
                        whatsapp_question_for_seller_en=(
                            f"In the Village Revenue Records and the 2008 Agricultural Data Bank, is this land categorized as 'Nilam' ('{snippet}') or converted to 'Purayidam'? "
                            "Have Form 5 (Data Bank exclusion) and Section 27A (Form 6 conversion) orders been obtained?"
                        ),
                    )
                )

        # 3. Scan for Minor Rights
        minor_match = self._find_first_pattern(deed_text, self.MINOR_PATTERNS)
        if minor_match:
            snippet, desc, mal_title = minor_match
            # Check if court sanction is negated (e.g. "without court sanction", "court order not obtained")
            sanction_negated = re.search(
                r"(?i)\b(without|no|not|lacking|nil)\s+(?:any\s+)?(?:prior\s+)?(?:district\s+)?(?:court\s+)?(?:order|sanction|permission)\b|"
                r"(കോടതി\s*അനുമതിയില്ലാതെ|കോടതി\s*ഉത്തരവില്ലാതെ|അനുമതി\s*കൂടാതെ)",
                deed_text,
            )
            has_court_order = False
            if not sanction_negated:
                has_court_order = bool(re.search(
                    r"(?i)(district\s*court\s*(?:order|sanction)|court\s*order|court\s*sanction|sanction\s*order\s*in|"
                    r"o\.p\.\s*no|op\s*no\b|section\s*8\(2\)\s*permission|vide\s*order\s*no|"
                    r"ജില്ലാ\s*കോടതി\s*(?:ഉത്തരവ്|അനുമതി)|കോടതി\s*ഉത്തരവ്|ഒ\.പി\.\s*നമ്പർ)",
                    deed_text,
                ))
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
                        whatsapp_question_for_seller_en=(
                            f"The deed indicates transfer of a minor's property interest ('{snippet}'). "
                            "Was prior sanction obtained from the District Court under Section 8(2) of the HMGA, "
                            "or is there a registered ratification / release deed executed by the minor upon attaining majority?"
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
                        f"The deed contains an explicit maintenance covenant ('{snippet}'). Under Section 23 of the Senior Citizens Act "
                        "and Supreme Court precedent (Sudesh Chhikara v. Ramti Devi, 2022), explicit conditions to provide basic amenities "
                        "empower the Maintenance Tribunal (RDO) to declare the deed void if neglected."
                    ),
                    matched_snippet=snippet,
                    kerala_statute="Section 23, Maintenance and Welfare of Parents and Senior Citizens Act, 2007 (Sudesh Chhikara SC 2022)",
                    whatsapp_question_for_seller=(
                        "ആധാരത്തിൽ മാതാപിതാക്കളുടെ സംരക്ഷണ വ്യവസ്ഥയുണ്ടല്ലോ ('" + snippet + "'). "
                        "മാതാപിതാക്കൾ ഇപ്പോഴും ജീവിച്ചിരിപ്പുണ്ടോ? പുതിയ ആധാരത്തിൽ അവർ സമ്മതക്കാരായി ഒപ്പിടുമോ?"
                    ),
                    whatsapp_question_for_seller_en=(
                        f"The deed contains a parental maintenance covenant ('{snippet}'). "
                        "Are the parents currently alive, and will they be joining as consenting executants to sign the proposed conveyance deed?"
                    ),
                )
            )

        # 5. Scan for Coastal Regulation Zone (CRZ) / Backwater Buffer Risk
        crz_match = self._find_first_pattern(deed_text, self.CRZ_PATTERNS)
        if crz_match:
            snippet, desc, mal_title = crz_match
            clearance_negated = re.search(
                r"(?i)\b(without|no|not|lacking|nil|awaiting)\s+(?:any\s+)?(?:kczma\s+)?(?:crz\s+)?(?:clearance|permission|approval|sanction)\b|"
                r"(അനുമതിയില്ലാതെ|അനുമതി\s*കൂടാതെ|ക്ലിയറൻസ്\s*ഇല്ലാതെ)",
                deed_text,
            )
            has_crz_clearance = False
            if not clearance_negated:
                has_crz_clearance = bool(re.search(
                    r"(?i)(kczma\s*(?:clearance|approved|sanction|permission)|crz\s*clearance\s*obtained|"
                    r"തീരദേശ\s*പരിപാലന\s*അനുമതി\s*ലഭിച്ചിട്ടുള്ള)",
                    deed_text,
                ))
            if not has_crz_clearance:
                score -= 40
                has_critical = True
                findings.append(
                    TrapFinding(
                        trap_type=TrapCategory.CRZ_COASTAL_REGULATION_RISK,
                        severity="CRITICAL",
                        title="Coastal Regulation Zone (CRZ) / Backwater Buffer Restriction",
                        title_malayalam=mal_title,
                        explanation=(
                            f"The property is subject to Coastal Regulation Zone (CRZ) restrictions ('{snippet}'). "
                            "Under the CRZ Notification and KCZMA regulations, construction within No Development Zones (NDZ) "
                            "or backwater buffer corridors is strictly prohibited or severely restricted."
                        ),
                        matched_snippet=snippet,
                        kerala_statute="CRZ Notification 2011/2019 & Environment (Protection) Act, 1986",
                        whatsapp_question_for_seller=(
                            "ഈ സ്ഥലം തീരദേശ പരിപാലന നിയമത്തിന്റെ (CRZ) ബഫർ സോണിലോ നോ-ഡെവലപ്‌മെന്റ് സോണിലോ (NDZ) ഉൾപ്പെട്ടിട്ടുണ്ടോ? "
                            "കേരള കോസ്റ്റൽ സോൺ മാനേജ്മെന്റ് അതോറിറ്റിയുടെ (KCZMA) മുൻകൂർ നിർമ്മാണാനുമതി ഉണ്ടോ?"
                        ),
                        whatsapp_question_for_seller_en=(
                            f"Is this property located within the Coastal Regulation Zone (CRZ) buffer or No Development Zone ('{snippet}')? "
                            "Has mandatory clearance from the Kerala Coastal Zone Management Authority (KCZMA) been obtained?"
                        ),
                    )
                )

        # 6. Scan for Waqf / Devaswom / Religious Trust Inalienability
        trust_match = self._find_first_pattern(deed_text, self.TRUST_ALIENATION_PATTERNS)
        if trust_match:
            snippet, desc, mal_title = trust_match
            sanction_negated = re.search(
                r"(?i)\b(without|no|not|lacking|nil)\s+(?:any\s+)?(?:prior\s+)?(?:board\s+)?(?:court\s+)?(?:order|sanction|permission|approval)\b|"
                r"(അനുമതിയില്ലാതെ|ഉത്തരവില്ലാതെ|അനുമതി\s*കൂടാതെ)",
                deed_text,
            )
            has_board_sanction = False
            if not sanction_negated:
                has_board_sanction = bool(re.search(
                    r"(?i)(waqf\s*board\s*(?:sanction|permission|order)|devaswom\s*board\s*(?:sanction|order|approval)|"
                    r"court\s*sanction\s*under\s*section\s*92|വഖഫ്\s*ബോർഡ്\s*(?:അനുമതി|ഉത്തരവ്)|"
                    r"ദേവസ്വം\s*ബോർഡ്\s*(?:അനുമതി|ഉത്തരവ്))",
                    deed_text,
                ))
            if not has_board_sanction:
                score -= 45
                has_critical = True
                findings.append(
                    TrapFinding(
                        trap_type=TrapCategory.TRUST_DEVASWOM_WAQF_ALIENATION,
                        severity="CRITICAL",
                        title="Waqf / Devaswom Trust Property Alienation Bar",
                        title_malayalam=mal_title,
                        explanation=(
                            f"The property is recited as temple/mosque/trust property ('{snippet}'). Under Section 51 of the "
                            "Waqf Act 1995 and Section 27 of the Travancore-Cochin Hindu Religious Institutions Act 1950, "
                            "alienation of trust/Devaswom/Waqf land without prior statutory board or court sanction is void ab initio."
                        ),
                        matched_snippet=snippet,
                        kerala_statute="Waqf Act, 1995 (Section 51) / Travancore-Cochin Hindu Religious Institutions Act, 1950 (Section 27 - Devaswom Board)",
                        whatsapp_question_for_seller=(
                            "ആധാരത്തിൽ ദേവസ്വം/വഖഫ്/ട്രസ്റ്റ് സ്വത്ത് എന്ന് പറഞ്ഞിട്ടുണ്ടല്ലോ ('" + snippet + "'). "
                            "ഈ കൈമാറ്റത്തിന് ദേവസ്വം ബോർഡിന്റെയോ വഖഫ് ബോർഡിന്റെയോ മുൻകൂർ അനുമതി ഉത്തരവ് വാങ്ങിയിട്ടുണ്ടോ?"
                        ),
                        whatsapp_question_for_seller_en=(
                            f"The deed recites religious trust endowment property ('{snippet}'). "
                            "Was prior statutory sanction obtained from the Devaswom Board or Waqf Board under relevant statutes before execution?"
                        ),
                    )
                )

        # 7. Scan for Extent Inflation / Internal Discrepancy in Single Deed
        parsed_extent = parse_extents_from_text(deed_text)
        if parsed_extent.cents and (parsed_extent.ares or parsed_extent.hectares or parsed_extent.sq_meters):
            inconsistent, diff, explanation = verify_internal_extent_consistency(
                cents=parsed_extent.cents,
                ares=parsed_extent.ares,
                hectares=parsed_extent.hectares,
                sq_meters=parsed_extent.sq_meters,
                tolerance_pct=5.0,
            )
            if inconsistent:
                score -= 25
                findings.append(
                    TrapFinding(
                        trap_type=TrapCategory.EXTENT_INFLATION_DISCREPANCY,
                        severity="HIGH",
                        title="Extent Inflation / Unit Discrepancy Found in Schedule",
                        title_malayalam="വിസ്തീർണ്ണത്തിൽ പൊരുത്തക്കേട് / അളവ് പെരുപ്പിച്ചു കാണിക്കൽ",
                        explanation=(
                            f"The deed contains contradictory land measurements: {explanation}. "
                            "This indicates potential extent inflation where more cents are claimed than the underlying revenue survey record supports."
                        ),
                        matched_snippet=explanation,
                        kerala_statute="Nemo dat quod non habet & Kerala Land Tax Act / Survey and Boundaries Act, 1961",
                        whatsapp_question_for_seller=(
                            f"ആധാരത്തിലെ വിസ്തീർണ്ണത്തിൽ പൊരുത്തക്കേട് കാണുന്നുണ്ടല്ലോ ({explanation}). "
                            "വില്ലേജ് ഓഫീസറുടെ FMB സ്കെച്ചും തണ്ടപ്പേർ റിക്കാർഡും പ്രകാരമുള്ള ശരിയായ വിസ്തീർണ്ണം എത്രയാണ്?"
                        ),
                        whatsapp_question_for_seller_en=(
                            f"There is a discrepancy in the stated land measurements ({explanation}). "
                            "Could you provide the certified Village Officer FMB sketch and Thandaper extract confirming the exact ground extent?"
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
                "None of the known red-flag phrases (easements, wetland status, minor rights, maintenance covenants) were found in this text. "
                "This is not a clean-title opinion: a pattern scan cannot see what the deed omits. Get the Encumbrance Certificate (EC), "
                "inspect the site, and have an advocate review the title before paying any advance."
            )

        return DeedSanityResult(
            verdict=verdict,
            sanity_score=score,
            findings=findings,
            summary_advice=advice,
        )

    def _find_first_pattern(self, text: str, patterns: list):
        for pattern, desc, mal_title in patterns:
            for match in re.finditer(pattern, text):
                # "no right of way ...", "free from easements" -> not a trap
                if self._NEGATION_BEFORE.search(text[max(0, match.start() - 40):match.start()]):
                    continue
                start = max(0, match.start() - 20)
                end = min(len(text), match.end() + 30)
                snippet = text[start:end].strip().replace("\n", " ")
                return snippet, desc, mal_title
        return None
