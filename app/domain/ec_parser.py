"""SRO Encumbrance Certificate (EC / കുടിക്കടം) parser and cross-validation engine for Kerala real estate.

Analyzes digitized Nil-EC and Encumbrance Certificates (issued via pearl.registration.kerala.gov.in
and SRO Volume Books), extracts tabular registration entries, and cross-references them against
seller-provided title deeds to detect:
1. Undischarged equitable bank mortgages (Gehan / ബാങ്ക് ബാധ്യത) without registered release (ഒഴിവുമുറി).
2. Civil court / DRT attachments or revenue recovery orders (കോടതി ജപ്തി).
3. Secret prior sales, fractional alienations, or conflicting encumbrances.
"""

from __future__ import annotations

import re
from typing import Any

from app.domain.models import (
    DeedNode,
    ECAuditResult,
    ECEntry,
    RiskFlag,
    RiskSeverity,
)


class EncumbranceCertificateAuditor:
    """Forensic auditor for Kerala SRO Encumbrance Certificates."""

    BANK_KEYWORDS = [
        "bank", "federal", "sbi", "canara", "cooperative", "co-operative",
        "hdfc", "icici", "south indian bank", "kerala bank", "ksfe", "gehan",
        "mortgage", "ധനകാര്യ", "ബാങ്ക്", "ഗെഹാൻ"
    ]

    ATTACHMENT_KEYWORDS = [
        "attachment", "court", "decree", "sub court", "munsiff", "drt",
        "revenue recovery", "collector", "ജപ്തി", "കോടതി", "അറ്റാച്ച്മെന്റ്"
    ]

    RELEASE_KEYWORDS = [
        "release", "receipt", "discharge", "ozhivumuri", "ഒഴിവുമുറി",
        "ബാധ്യത തീർപ്പ്", "തീർപ്പുമുറി", "ക്ലിയറൻസ്"
    ]

    def __init__(self, property_identifier: str = "Kerala SRO Property"):
        self.property_identifier = property_identifier

    def parse_ec_text(self, raw_text: str) -> list[ECEntry]:
        """Parses raw OCR or copied tabular text from an SRO Encumbrance Certificate."""
        entries: list[ECEntry] = []
        if not raw_text or not raw_text.strip():
            return entries

        # Check for Nil Encumbrance marker
        if re.search(r"nil\s+encumbrance|zero\s+encumbrance|ബാധ്യതകളൊന്നും\s+കാണുന്നില്ല|nil\s+liability", raw_text, re.I):
            return entries

        # Line-by-line / block parser
        lines = [line.strip() for line in raw_text.splitlines() if line.strip()]
        current_block: list[str] = []

        for line in lines:
            # Check if this line begins a new doc entry (e.g. "Doc No: 1420/2014" or "1420/2014" or "1. 3012/2022")
            doc_match = re.search(r"(?:Doc(?:\s*No)?[:\.\s]+)?(\d+)\s*/\s*(19\d\d|20\d\d)", line, re.I)
            if doc_match and (not current_block or len(current_block) >= 2):
                if current_block:
                    entry = self._parse_block("\n".join(current_block))
                    if entry:
                        entries.append(entry)
                current_block = [line]
            else:
                current_block.append(line)

        if current_block:
            entry = self._parse_block("\n".join(current_block))
            if entry:
                entries.append(entry)

        return entries

    def _parse_block(self, block_text: str) -> ECEntry | None:
        doc_match = re.search(r"(\d+)\s*/\s*(19\d\d|20\d\d)", block_text)
        if not doc_match:
            return None

        doc_num = f"{doc_match.group(1)}/{doc_match.group(2)}"
        year = int(doc_match.group(2))

        # SRO detection
        sro = "Kerala SRO"
        sro_m = re.search(r"(?:SRO|Sub-Registrar(?: Office)?|സബ്\s*രജിസ്ട്രാർ)[:\s]+([^\n,\.]+)", block_text, re.I)
        if sro_m:
            sro = sro_m.group(1).strip()

        # Nature detection
        nature = "Transaction"
        if any(b in block_text.lower() for b in self.BANK_KEYWORDS):
            nature = "Bank Mortgage / Gehan (ബാങ്ക് ബാധ്യത)"
        elif any(a in block_text.lower() for a in self.ATTACHMENT_KEYWORDS):
            nature = "Court / RR Attachment (കോടതി ജപ്തി)"
        elif any(r in block_text.lower() for r in self.RELEASE_KEYWORDS):
            nature = "Release / Discharge Receipt (ഒഴിവുമുറി)"
        elif re.search(r"sale|theer|തീറാധാരം|വിലയാധാരം", block_text, re.I):
            nature = "Theeradharam / Sale Deed (തീറാധാരം)"
        elif re.search(r"partition|bhagapat|ഭാഗപത്രം", block_text, re.I):
            nature = "Bhagapathram / Partition Deed (ഭാഗപത്രം)"
        elif re.search(r"gift|settlement|dhanam|ധനം|ധനനിശ്ചയം", block_text, re.I):
            nature = "Settlement / Gift Deed (ധനനിശ്ചയാധാരം)"

        # Consideration or liability amount
        amount = 0.0
        amt_match = re.search(r"(?:₹|Rs\.?|INR|തുക)[:\s]*([0-9,]+(?:\.\d+)?)", block_text, re.I)
        if amt_match:
            try:
                amount = float(amt_match.group(1).replace(",", ""))
            except Exception:
                pass

        # Parties extraction
        executants: list[str] = []
        claimants: list[str] = []
        exec_m = re.search(r"(?:Executant|From|എഴുതിക്കൊടുത്തയാൾ)[:\s]+([^\n;]+)", block_text, re.I)
        if exec_m:
            executants = [p.strip() for p in exec_m.group(1).split(",") if p.strip()]

        claim_m = re.search(r"(?:Claimant|To|Bank|എഴുതിവാങ്ങിയയാൾ)[:\s]+([^\n;]+)", block_text, re.I)
        if claim_m:
            claimants = [p.strip() for p in claim_m.group(1).split(",") if p.strip()]

        is_undischarged = any(k in block_text.lower() for k in self.BANK_KEYWORDS) and not any(r in block_text.lower() for r in self.RELEASE_KEYWORDS)
        is_attachment = any(a in block_text.lower() for a in self.ATTACHMENT_KEYWORDS)

        return ECEntry(
            doc_number=doc_num,
            year=year,
            sro_name=sro,
            nature_of_act=nature,
            executants=executants,
            claimants=claimants,
            consideration_inr=amount,
            liability_amount_inr=amount if (is_undischarged or is_attachment) else None,
            is_undischarged_liability=is_undischarged,
            is_court_attachment=is_attachment,
            notes=block_text.strip()[:200],
        )

    def audit_ec(
        self,
        ec_entries: list[ECEntry] | None = None,
        raw_ec_text: str | None = None,
        known_deeds: list[DeedNode] | None = None,
        period_label: str = "30 Years (1994-2024)",
    ) -> ECAuditResult:
        """Cross-references EC entries against known title deeds."""
        if ec_entries is None and raw_ec_text:
            ec_entries = self.parse_ec_text(raw_ec_text)
        elif ec_entries is None:
            ec_entries = []

        known_deed_numbers = {d.doc_number.strip().lower() for d in (known_deeds or [])}
        known_years = {d.year for d in (known_deeds or [])}

        risk_flags: list[RiskFlag] = []
        undisclosed_mortgages: list[str] = []
        court_attachments: list[str] = []
        conflicting_alienations: list[str] = []

        # Find released documents
        released_docs: set[str] = set()
        for entry in ec_entries:
            if "release" in entry.nature_of_act.lower() or "receipt" in entry.nature_of_act.lower() or "ഒഴിവുമുറി" in entry.nature_of_act:
                for target in ec_entries:
                    if target.is_undischarged_liability and target.year <= entry.year:
                        released_docs.add(target.doc_number)

        # Evaluate each EC entry
        for entry in ec_entries:
            # 1. Undischarged Mortgages / Gehan
            if entry.is_undischarged_liability and entry.doc_number not in released_docs:
                liability_str = f"₹{entry.liability_amount_inr:,.0f}" if entry.liability_amount_inr else "Undisclosed Amount"
                party_str = f" in favor of {', '.join(entry.claimants)}" if entry.claimants else ""
                desc = (
                    f"Doc #{entry.doc_number} ({entry.year}, SRO {entry.sro_name}) records an active bank mortgage / Gehan {liability_str}{party_str}. "
                    f"No registered release deed or bank discharge certificate (ഭാരരഹിത സർട്ടിഫിക്കറ്റ്) is found on record. "
                    f"Property is subject to statutory attachment under SARFAESI Act, 2002."
                )
                undisclosed_mortgages.append(f"Doc #{entry.doc_number}: {liability_str}{party_str}")
                risk_flags.append(
                    RiskFlag(
                        category="Mortgage / Bank Lien",
                        severity=RiskSeverity.CRITICAL,
                        title=f"Undischarged Bank Mortgage in SRO EC (Doc #{entry.doc_number})",
                        description=desc,
                        legal_citation="Sec 17 & 51 Indian Registration Act, 1908 / Sec 13 SARFAESI Act, 2002",
                        remedial_action=(
                            "Do not part with earnest money. Require seller to produce a formal Bank Loan Closure Certificate, "
                            "No Objection Certificate (NOC), and registered Gehan Release Deed (ബാധ്യതാ ഒഴിവുമുറി)."
                        ),
                    )
                )

            # 2. Civil Court Attachments
            if entry.is_court_attachment:
                court_attachments.append(f"Doc #{entry.doc_number} ({entry.year})")
                risk_flags.append(
                    RiskFlag(
                        category="Court Attachment",
                        severity=RiskSeverity.CRITICAL,
                        title=f"Civil Court / Revenue Recovery Attachment (Doc #{entry.doc_number})",
                        description=(
                            f"An order of attachment is registered under Doc #{entry.doc_number} at SRO {entry.sro_name}. "
                            f"Alienation of property under attachment is void under Section 64 of the Civil Procedure Code."
                        ),
                        legal_citation="Section 64 Code of Civil Procedure (CPC) / Section 52 Transfer of Property Act (Lis Pendens)",
                        remedial_action="Conduct immediate civil litigation search at the jurisdictional District/Munsiff Court before executing any sale agreement.",
                    )
                )

            # 3. Conflicting Prior Alienation
            if ("sale" in entry.nature_of_act.lower() or "theer" in entry.nature_of_act.lower()) and known_deeds:
                if entry.doc_number.strip().lower() not in known_deed_numbers:
                    conflicting_alienations.append(f"Doc #{entry.doc_number} ({entry.year})")
                    risk_flags.append(
                        RiskFlag(
                            category="Title Continuity Break",
                            severity=RiskSeverity.HIGH,
                            title=f"Unexplained Registered Sale Deed in EC (Doc #{entry.doc_number})",
                            description=(
                                f"Doc #{entry.doc_number} registered in {entry.year} at SRO {entry.sro_name} is listed in the official EC "
                                f"but missing from the seller's title lineage. This indicates an undisclosed partial sale or competing title."
                            ),
                            legal_citation="Section 48 Indian Registration Act (Priority of registered documents)",
                            remedial_action="Obtain certified copy of Doc #{entry.doc_number} from SRO pearl portal to verify exact property boundaries and parties.",
                        )
                    )

        # Calculate safety score
        if court_attachments or undisclosed_mortgages:
            score = max(10, 100 - (len(undisclosed_mortgages) * 45) - (len(court_attachments) * 50))
        elif conflicting_alienations:
            score = max(35, 100 - (len(conflicting_alienations) * 30))
        elif not ec_entries:
            score = 100  # Nil EC
        else:
            score = 90

        is_nil = len(ec_entries) == 0

        # Build summary
        if is_nil:
            summary = "Official SRO Nil-Encumbrance verified: Zero recorded bank mortgages, civil court attachments, or conflicting transfers during search period."
        elif not risk_flags:
            summary = f"EC contains {len(ec_entries)} regular title transactions consistent with known title lineage. Zero undischarged charges detected."
        else:
            summary = f"ALERT: Detected {len(risk_flags)} high-risk statutory liabilities in official SRO records ({len(undisclosed_mortgages)} active mortgages, {len(court_attachments)} court attachments)."

        # WhatsApp inquiry
        wa_questions: list[str] = []
        if undisclosed_mortgages:
            wa_questions.append(
                f"സബ് രജിസ്ട്രാർ ഓഫീസിലെ ബാധ്യതാ സർട്ടിഫിക്കറ്റിൽ (EC) കാണുന്ന ബാങ്ക് ബാധ്യതകൾ ({', '.join(undisclosed_mortgages)}) "
                f"പൂർണ്ണമായും തീർത്തതാണോ? ബാങ്കിൽ നിന്നുള്ള ഔദ്യോഗിക ക്ലോഷർ കത്തും (NOC) രജിസ്റ്റർ ചെയ്ത ബാധ്യത ഒഴിവുമുറിയും (Release Deed) ലഭ്യമാണോ?"
            )
        if court_attachments:
            wa_questions.append(
                f"പ്രമാണത്തിൽ കോടതി ജപ്തി ഉത്തരവുകൾ ({', '.join(court_attachments)}) കാണുന്നുണ്ട്. ഈ കേസ് ഒത്തുതീർപ്പാക്കി കോടതിയിൽ നിന്ന് ജപ്തി പിൻവലിച്ച രേഖകൾ ലഭ്യമാണോ?"
            )
        if conflicting_alienations:
            wa_questions.append(
                f"കുടിക്കടത്തിൽ (EC) രേഖപ്പെടുത്തിയിട്ടുള്ള തീറാധാരം ({', '.join(conflicting_alienations)}) കൈമാറ്റം ചെയ്തത് ഈ വസ്തുവിൽ ഉൾപ്പെടുന്നതാണോ എന്ന് വ്യക്തമാക്കാമോ?"
            )

        if not wa_questions:
            whatsapp_inquiry = (
                f"നമസ്കാരം, {self.property_identifier}-ന്റെ {period_label} കുടിക്കടം (EC) പരിശോധിച്ചു. "
                f"യാതൊരു ബാങ്ക് ബാധ്യതകളോ കോടതി ജപ്തികളോ ഇല്ലാത്തത് വളരെ സംതൃപ്തികരമാണ്. "
                f"രജിസ്ട്രേഷന് മുൻപായി ഏറ്റവും പുതിയ ഒറിജിനൽ EC ലഭ്യമാക്കുമല്ലോ."
            )
        else:
            joined_q = "\n".join(f"{i+1}. {q}" for i, q in enumerate(wa_questions))
            whatsapp_inquiry = (
                f"നമസ്കാരം, {self.property_identifier}-ന്റെ കുടിക്കടം (EC) പരിശോധിച്ചപ്പോൾ താഴെ പറയുന്ന പ്രധാന കാര്യങ്ങളിൽ വ്യക്തത ആവശ്യമുണ്ട്:\n"
                f"{joined_q}"
            )

        checklist = [
            "Verify official SRO digital seal and barcoded EC from pearl.registration.kerala.gov.in",
            "Demand written Bank Loan Closure Certificate & NOC if prior mortgage exists",
            "Cross-verify survey numbers across all EC entries to ensure no sub-division omission",
            "Check for any un-registered or oral agreements with neighbors / local society",
        ]

        return ECAuditResult(
            property_identifier=self.property_identifier,
            ec_period=period_label,
            total_entries_count=len(ec_entries),
            is_nil_encumbrance=is_nil,
            entries=ec_entries,
            undisclosed_mortgages=undisclosed_mortgages,
            court_attachments=court_attachments,
            conflicting_alienations=conflicting_alienations,
            risk_flags=risk_flags,
            safety_score=score,
            summary=summary,
            whatsapp_inquiry=whatsapp_inquiry,
            checklist=checklist,
        )
