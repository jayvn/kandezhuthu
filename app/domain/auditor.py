"""Munnadharam Auditor Engine: Kerala Prior Deeds Title Lineage Legal Heuristic Evaluator."""

from typing import List, Tuple
from app.domain.models import (
    DeedNode,
    DeedType,
    ECRecord,
    RiskFlag,
    RiskSeverity,
    CleanTitleScorecard,
)


class MunnadharamAuditor:
    """Core reasoning engine that conducts multi-decade forensic title audits."""

    def __init__(self, property_identifier: str):
        self.property_identifier = property_identifier

    def audit(
        self,
        deeds: List[DeedNode],
        ec_records: List[ECRecord] = None,
    ) -> CleanTitleScorecard:
        if not deeds:
            raise ValueError("At least one deed must be provided for title audit.")

        # Sort deeds chronologically by year and doc number
        sorted_deeds = sorted(deeds, key=lambda d: (d.year, d.doc_number))
        ec_records = ec_records or []

        risk_flags: List[RiskFlag] = []
        recommendations: List[str] = []

        # 1. Chain of custody verification
        chain_intact, custody_flags = self._verify_chain_continuity(sorted_deeds)
        risk_flags.extend(custody_flags)

        # 2. Extent mathematical continuity
        extent_flags = self._verify_extent_continuity(sorted_deeds)
        risk_flags.extend(extent_flags)

        # 3. Inheritance & succession verification
        succession_flags = self._verify_succession_and_heirs(sorted_deeds)
        risk_flags.extend(succession_flags)

        # 4. Minor rights & guardianship verification
        minor_flags = self._verify_minor_rights(sorted_deeds)
        risk_flags.extend(minor_flags)

        # 5. Easements and restrictive covenants
        easement_flags = self._verify_easements(sorted_deeds)
        risk_flags.extend(easement_flags)

        # 6. EC Triangulation
        ec_flags = self._cross_validate_with_ec(sorted_deeds, ec_records)
        risk_flags.extend(ec_flags)

        # Generate lineage path summary strings
        lineage_path = [
            f"{d.year}: {d.deed_type.value} (Doc #{d.doc_number}, SRO {d.sro_name}) | "
            f"{', '.join(d.grantors)} -> {', '.join(d.grantees)} [{d.extent_cents:.2f} Cents]"
            for d in sorted_deeds
        ]

        # Calculate final score and risk level
        score, risk_level = self._compute_score(risk_flags)

        # Generate targeted legal recommendations
        for flag in risk_flags:
            if flag.severity in (RiskSeverity.CRITICAL, RiskSeverity.HIGH):
                recommendations.append(f"[{flag.category}] {flag.remedial_action}")

        if not recommendations:
            recommendations.append(
                "Title chain is healthy. Proceed with customary SRO encumbrance verification and spot inspection of boundaries."
            )

        return CleanTitleScorecard(
            property_identifier=self.property_identifier,
            overall_score=score,
            risk_level=risk_level,
            chain_of_custody_intact=chain_intact,
            lineage_path=lineage_path,
            risk_flags=risk_flags,
            recommendations_for_advocate=recommendations,
        )

    def _verify_chain_continuity(self, deeds: List[DeedNode]) -> Tuple[bool, List[RiskFlag]]:
        flags: List[RiskFlag] = []
        chain_intact = True

        for i in range(len(deeds) - 1):
            curr_deed = deeds[i]
            next_deed = deeds[i + 1]

            # Check if at least one grantee of current deed is a grantor in the next deed
            curr_grantees = {g.strip().lower() for g in curr_deed.grantees}
            next_grantors = {g.strip().lower() for g in next_deed.grantors}

            overlap = curr_grantees.intersection(next_grantors)
            if not overlap and next_deed.deed_type != DeedType.COURT_DECREE:
                chain_intact = False
                flags.append(
                    RiskFlag(
                        category="CHAIN_OF_TITLE_GAP",
                        severity=RiskSeverity.CRITICAL,
                        title=f"Gap in Chain of Title between {curr_deed.doc_number} and {next_deed.doc_number}",
                        description=(
                            f"Grantees of deed {curr_deed.doc_number} ({', '.join(curr_deed.grantees)}) "
                            f"do not match grantors in subsequent deed {next_deed.doc_number} ({', '.join(next_deed.grantors)}). "
                            "Missing link in ownership chain (possible unrecorded inheritance, death, or third-party conveyance)."
                        ),
                        legal_citation="Transfer of Property Act, 1882 (Section 7 - Persons competent to transfer)",
                        remedial_action=(
                            "Obtain missing link document (Legal Heirship Certificate, Partition Deed, or prior Sale Deed) "
                            f"establishing how {', '.join(next_deed.grantors)} acquired title from {', '.join(curr_deed.grantees)}."
                        ),
                    )
                )

        return chain_intact, flags

    def _verify_extent_continuity(self, deeds: List[DeedNode]) -> List[RiskFlag]:
        from app.domain.extent_converter import verify_extent_inflation, cents_to_ares, cents_to_sqm
        flags: List[RiskFlag] = []

        for i in range(len(deeds) - 1):
            curr_deed = deeds[i]
            next_deed = deeds[i + 1]

            # If the next deed conveys more land than the parent deed had
            is_inflated, excess = verify_extent_inflation(curr_deed.extent_cents, next_deed.extent_cents, tolerance=0.05)
            if is_inflated:
                excess_ares = cents_to_ares(excess)
                excess_sqm = cents_to_sqm(excess)
                flags.append(
                    RiskFlag(
                        category="EXTENT_INFLATION",
                        severity=RiskSeverity.HIGH,
                        title=f"Extent Deficit: {next_deed.doc_number} conveys more land than prior deed",
                        description=(
                            f"Prior deed {curr_deed.doc_number} ({curr_deed.year}) conveyed {curr_deed.extent_cents:.2f} Cents, "
                            f"but subsequent deed {next_deed.doc_number} ({next_deed.year}) purports to convey "
                            f"{next_deed.extent_cents:.2f} Cents (+{excess:.2f} Cents / {excess_ares:.2f} Ares / {excess_sqm:.1f} Sq.M unbacked by title)."
                        ),
                        legal_citation="Nemo dat quod non habet (No one can transfer a better title than he has)",
                        remedial_action=(
                            f"Demand seller provide a certified surveyor sketch or rectification deed explaining the {excess:.2f} Cent difference. "
                            "Do not purchase unbacked extent without Village Officer Field Measurement Book (FMB) verification."
                        ),
                    )
                )

        return flags

    def _verify_succession_and_heirs(self, deeds: List[DeedNode]) -> List[RiskFlag]:
        flags: List[RiskFlag] = []

        for deed in deeds:
            if deed.unrepresented_heirs:
                heir_list = ", ".join(deed.unrepresented_heirs)
                religion = (deed.family_religion or "hindu").lower()
                
                if religion == "christian":
                    law_name = "Indian Succession Act, 1925 & Supreme Court judgment in Mary Roy v. State of Kerala (1986)"
                    reason = "Female heirs have equal entitlement to intestate parental property."
                elif religion == "hindu":
                    law_name = "Hindu Succession (Amendment) Act, 2005 & Vineeta Sharma v. Rakesh Sharma (2020)"
                    reason = "Daughters are coparceners by birth with equal rights in joint family property."
                else:
                    law_name = "Muslim Personal Law (Shariat) Application Act, 1937"
                    reason = "Prescribed Quranic sharers cannot be excluded from inheritance."

                flags.append(
                    RiskFlag(
                        category="SUCCESSION_HEIR_EXCLUSION",
                        severity=RiskSeverity.CRITICAL,
                        title=f"Excluded Legal Heirs in {deed.deed_type.value} #{deed.doc_number}",
                        description=(
                            f"Deed {deed.doc_number} omitted legal heirs ({heir_list}) from execution. {reason}"
                        ),
                        legal_citation=law_name,
                        remedial_action=(
                            f"Require all omitted heirs ({heir_list}) or their surviving legal representatives to execute a "
                            "registered Release Deed (Ozhivumuri) or join as confirming parties in the proposed sale deed."
                        ),
                    )
                )

        return flags

    def _verify_minor_rights(self, deeds: List[DeedNode]) -> List[RiskFlag]:
        flags: List[RiskFlag] = []

        for deed in deeds:
            if deed.is_minor_involved and not deed.minor_court_sanction_present:
                flags.append(
                    RiskFlag(
                        category="MINOR_RIGHTS_VOIDABLE",
                        severity=RiskSeverity.HIGH,
                        title=f"Minor's Share Sold Without Court Permission in Deed #{deed.doc_number}",
                        description=(
                            f"Deed {deed.doc_number} ({deed.year}) involved alienation of property belonging to a minor "
                            "by a natural/de-facto guardian without prior sanction of the District Court."
                        ),
                        legal_citation="Section 8(2), Hindu Minority and Guardianship Act, 1956 / Guardians and Wards Act, 1890",
                        remedial_action=(
                            "Verify if the minor has attained majority (>18 years). If within 3 years of attaining majority, "
                            "the transfer is legally voidable. Obtain a registered ratification deed from the former minor."
                        ),
                    )
                )

        return flags

    def _verify_easements(self, deeds: List[DeedNode]) -> List[RiskFlag]:
        flags: List[RiskFlag] = []

        for deed in deeds:
            if deed.easements_reserved:
                for easement in deed.easements_reserved:
                    flags.append(
                        RiskFlag(
                            category="BURDEN_OR_EASEMENT",
                            severity=RiskSeverity.MEDIUM,
                            title=f"Reserved Easement / Servitude in Deed #{deed.doc_number}",
                            description=(
                                f"Deed {deed.doc_number} ({deed.year}) reserves: '{easement}'. "
                                "This creates an encumbrance running with the land."
                            ),
                            legal_citation="Indian Easements Act, 1882 (Section 4 & Section 13 - Easements of Necessity)",
                            remedial_action=(
                                f"Conduct on-site physical inspection to locate '{easement}'. "
                                "Ensure future building plan/compound wall will not obstruct this reserved pathway or water access."
                            ),
                        )
                    )

        return flags

    def _cross_validate_with_ec(
        self, deeds: List[DeedNode], ec_records: List[ECRecord]
    ) -> List[RiskFlag]:
        flags: List[RiskFlag] = []
        if not ec_records:
            return flags

        deed_numbers = {d.doc_number.strip() for d in deeds}
        ec_doc_numbers = {e.doc_number.strip() for e in ec_records}

        # Check for ghost documents in EC not in seller's file
        unaccounted_in_ec = ec_doc_numbers - deed_numbers
        for ghost_doc in unaccounted_in_ec:
            matching_ec = next((e for e in ec_records if e.doc_number.strip() == ghost_doc), None)
            nature = matching_ec.nature if matching_ec else "Registered Transaction"
            flags.append(
                RiskFlag(
                    category="GHOST_ENCUMBRANCE_IN_EC",
                    severity=RiskSeverity.CRITICAL,
                    title=f"Undisclosed Transaction Found in EC: Doc #{ghost_doc}",
                    description=(
                        f"The SRO Encumbrance Certificate logs a registered entry (Doc #{ghost_doc}, Nature: {nature}) "
                        "that was NOT provided in the seller's prior deeds dossier. Possible mortgage, attachment, or partial sale."
                    ),
                    legal_citation="Indian Registration Act, 1908 (Section 17 & Section 51)",
                    remedial_action=(
                        f"Apply for a certified copy of Doc #{ghost_doc} from the Sub-Registrar Office immediately. "
                        "Do not pay any advance until this registered document is inspected and cleared."
                    ),
                )
            )

        return flags

    def _compute_score(self, flags: List[RiskFlag]) -> Tuple[int, str]:
        score = 100
        for flag in flags:
            if flag.severity == RiskSeverity.CRITICAL:
                score -= 35
            elif flag.severity == RiskSeverity.HIGH:
                score -= 20
            elif flag.severity == RiskSeverity.MEDIUM:
                score -= 10
            elif flag.severity == RiskSeverity.LOW:
                score -= 5

        score = max(0, min(100, score))

        if score >= 85:
            risk_level = "CLEAN / LOW RISK"
        elif score >= 65:
            risk_level = "MODERATE RISK - REMEDIAL ACTION REQUIRED"
        elif score >= 40:
            risk_level = "HIGH RISK - DEFECTIVE TITLE"
        else:
            risk_level = "CRITICAL RISK - DO NOT PROCEED"

        return score, risk_level
