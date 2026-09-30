"""Domain models for Munnadharam AI: Kerala Prior Deeds Title Lineage Auditor."""

from enum import Enum

from pydantic import BaseModel, Field


class DeedType(str, Enum):
    PATTAYAM = "Pattayam (Govt Land Assignment)"
    THEERADHARAM = "Theeradharam (Sale Deed)"
    BHAGAPATHRAM = "Bhagapathram (Partition Deed)"
    OZHIVUMURI = "Ozhivumuri (Release Deed)"
    DHANAM = "Dhanam (Gift Deed)"
    SETTLEMENT = "Settlement Deed"
    WILL_UDANPADI = "Will / Udanpadi"
    COURT_DECREE = "Court Decree / Auction"


class RiskSeverity(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class DeedNode(BaseModel):
    """Represents a single registered instrument in the chain of title."""
    doc_number: str = Field(description="Document number with year, e.g. 1420/1994")
    year: int
    sro_name: str = Field(description="Sub-Registrar Office where registered")
    deed_type: DeedType
    grantors: list[str] = Field(description="Parties conveying title (sellers / releasors / donors)")
    grantees: list[str] = Field(description="Parties receiving title (buyers / releasees / donees)")
    extent_cents: float = Field(description="Land extent mentioned in cents (1 cent = 40.4686 sq m)")
    survey_no: str
    resurvey_no: str | None = None
    consideration_inr: float = 0.0
    prior_doc_referenced: str | None = None

    # Crucial legal condition markers
    is_minor_involved: bool = False
    minor_court_sanction_present: bool = False
    unrepresented_heirs: list[str] = Field(default_factory=list, description="Known legal heirs omitted from partition or release")
    easements_reserved: list[str] = Field(default_factory=list, description="Easements, pathways, or well-access covenants")
    family_religion: str | None = "hindu"  # hindu, christian, muslim


class ECRecord(BaseModel):
    """Represents an entry in the SRO Encumbrance Certificate (EC)."""
    doc_number: str
    year: int
    sro_name: str
    nature: str
    parties: list[str] = Field(default_factory=list)


class RiskFlag(BaseModel):
    category: str
    severity: RiskSeverity
    title: str
    description: str
    legal_citation: str
    remedial_action: str


class CleanTitleScorecard(BaseModel):
    property_identifier: str
    overall_score: int
    risk_level: str
    chain_of_custody_intact: bool
    lineage_path: list[str]
    risk_flags: list[RiskFlag]
    recommendations_for_advocate: list[str]


class BuildingRuleMatch(BaseModel):
    occupancy_group: str
    plot_category: str
    min_road_width_m: float
    front_setback_m: float
    rear_setback_m: float
    side_setback_1_m: float
    side_setback_2_m: float
    well_septic_clearance_m: float = 7.5
    dead_wall_permitted: bool = False
    rule_citation: str
    notes: str | None = None


class PaddyLandFeeCalculation(BaseModel):
    extent_cents: float
    extent_ares: float
    fair_value_per_are_inr: float
    total_property_fair_value_inr: float
    applicable_fee_percentage: float
    statutory_conversion_fee_inr: float
    is_fee_exempt: bool
    description: str
    statutory_citation: str


class FloodRiskLevel(str, Enum):
    LOW = "LOW"
    MODERATE = "MODERATE"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class ElevationFloodResult(BaseModel):
    latitude: float
    longitude: float
    elevation_meters: float
    resolution_meters: float | None = None
    locality_name: str
    district: str
    taluk_or_village: str | None = None
    flood_risk_level: FloodRiskLevel
    flood_risk_score: int = Field(description="Safety score 0-100 (100 = safe from flood, 0 = severe flood risk)")
    river_basin: str | None = None
    inundation_2018_zone: bool = False
    ksdma_hazard_advisory: str
    wetland_topography_risk: str
    recommended_plinth_height_m: float
    physical_inspection_checklist: list[str]
    whatsapp_inquiry_for_seller: str
    whatsapp_inquiry_for_seller_en: str = ""


class ECEntry(BaseModel):
    """Represents a detailed entry in the SRO Encumbrance Certificate (EC / കുടിക്കടം)."""
    doc_number: str
    year: int
    sro_name: str
    volume: str | None = None
    page: str | None = None
    nature_of_act: str = Field(description="Nature of instrument (e.g. Theeradharam/Sale, Gehan/Mortgage, Court Attachment, Release)")
    executants: list[str] = Field(default_factory=list, description="Parties creating encumbrance / transferring")
    claimants: list[str] = Field(default_factory=list, description="Parties in whose favor encumbrance is created (e.g. Federal Bank, Court, Buyer)")
    consideration_inr: float = 0.0
    liability_amount_inr: float | None = None
    is_undischarged_liability: bool = False
    is_court_attachment: bool = False
    notes: str | None = None


class ECAuditResult(BaseModel):
    """Results of cross-validating SRO Encumbrance Certificate against title deeds."""
    property_identifier: str
    ec_period: str
    total_entries_count: int
    is_nil_encumbrance: bool
    entries: list[ECEntry] = Field(default_factory=list)
    undisclosed_mortgages: list[str] = Field(default_factory=list)
    court_attachments: list[str] = Field(default_factory=list)
    conflicting_alienations: list[str] = Field(default_factory=list)
    risk_flags: list[RiskFlag] = Field(default_factory=list)
    safety_score: int = Field(description="EC Safety Score 0-100 (100 = 100% clean nil EC, 0 = severe undischarged charges)")
    summary: str
    whatsapp_inquiry: str
    whatsapp_inquiry_en: str = ""
    checklist: list[str] = Field(default_factory=list)


class CadastralParcel(BaseModel):
    """Digital cadastral parcel geometry (BhuNaksha / ILIMS style FMB polygon)."""
    district: str
    taluk: str
    village: str
    block_no: str | None = None
    survey_no: str
    resurvey_no: str | None = None
    extent_cents: float
    polygon_coordinates: list[list[float]] = Field(description="List of [lat, lng] vertices")
    fmb_dimensions_m: list[dict[str, str | float]] = Field(default_factory=list, description="Edge segments with length in meters")
    adjacent_survey_numbers: list[str] = Field(default_factory=list)
    access_road_identified: bool = False
    subdivision_sketch_available: bool = True


class DataBankCheckResult(BaseModel):
    """Statutory check under Kerala Conservation of Paddy Land & Wetland Act, 2008."""
    survey_no: str
    village: str
    is_listed_in_databank: bool | None = Field(default=None, description="None when no Data Bank record is available")
    entry_status: str
    krishi_bhavan_name: str
    recommended_statutory_form: str
    fee_calculation: PaddyLandFeeCalculation | None = None
    building_permit_eligibility: str
    risk_advisory: str
    whatsapp_inquiry: str
    whatsapp_inquiry_en: str = ""

