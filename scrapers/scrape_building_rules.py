"""Kandezhuthu AI - Kerala Building Rules (KMBR / KPBR 2019) Extractor & Knowledge Generator.

Extracts and structures authoritative Kerala Building Rules (KMBR 2019 & KPBR 2019)
governing road access width, setbacks, small plot concessions, and sanitation clearances
into clean, structured markdown for LLM grounding.
"""

from pathlib import Path

KNOWLEDGE_OUTPUT_DIR = Path(__file__).resolve().parent.parent / "data" / "knowledge"
KNOWLEDGE_FILE = KNOWLEDGE_OUTPUT_DIR / "building_rules_kmbr_kpbr.md"

BUILDING_RULES_CONTENT = """# Kerala Building Rules (KMBR & KPBR 2019) · Legal Diligence Reference

> **Governing Statutes**:
> - **Kerala Municipality Building Rules, 2019 (KMBR)** — S.R.O. No. 777/2019 (Corporations & Municipalities)
> - **Kerala Panchayat Building Rules, 2019 (KPBR)** — S.R.O. No. 776/2019 (Grama Panchayats)

---

## 1. Access Road Width Requirements (റോഡ് വീതി വ്യവസ്ഥകൾ - Rule 5)

Under both KMBR and KPBR 2019, building permits require mandatory minimum road or access pathway widths. Purchasing land with non-compliant road width will prevent obtaining building permits from Local Self Government Institutions (LSGD - Panchayats/Municipalities).

| Occupancy / Building Type | Total Built-up Area / Height | Minimum Access Width Required | Notes & Caveats |
| :--- | :--- | :--- | :--- |
| **Group A1: Residential (Single Family)** | Up to $300\\text{ m}^2$ (height $\\le 10\\text{ m}$) | **$3.0\\text{ meters}$** | Standard motorable access road requirement. |
| **Group A1: Small Plot Concession** | Up to $150\\text{ m}^2$ (plots $\\le 3\\text{ cents}$ / $1.25\\text{ ares}$) | **$1.2\\text{ to }1.5\\text{ meters}$** | Pedestrian pathway access permitted for small plots registered before the cut-off date. |
| **Group A1: Multiple Family / Apartments** | $300\\text{ m}^2$ to $1000\\text{ m}^2$ | **$5.0\\text{ meters}$** | Fire engine / emergency vehicular maneuverability. |
| **Group A1: High-rise Residential** | Height $> 16\\text{ meters}$ | **$7.0\\text{ meters}$** | Clear motorable access for fire tenders. |
| **Group F / Mercantile (Commercial Shops)** | Up to $150\\text{ m}^2$ | **$3.6\\text{ meters}$** | Municipal commercial zoning requirement. |

> [!WARNING]
> **The 2-Meter Pathway Trap (*രണ്ട് മീറ്റർ വഴി ചതി*)**:
> Sellers often market plots asserting: *"There is a 6-foot (1.8m) or 2-meter concrete pathway, so a small car or auto can enter."*
> **Legal Reality**: If the plot exceeds 3 cents ($125\\text{ m}^2$), the local LSGD authority (Panchayat/Municipality) will strictly refuse a residential building permit unless a full **3.0-meter public or registered private access road** exists from an approved public street.

---

## 2. Setback & Open Space Standards (കെട്ടിട അകലങ്ങൾ - Rule 26 & Chapter VII)

Setbacks are mandatory unobstructed open spaces between the building exterior wall and plot boundaries.

### Standard Residential Plots (> 3 Cents / 1.25 Ares)
- **Front Open Space (മുൻവശത്തെ അകലം)**:
  - Minimum **$3.0\\text{ meters}$** from the street boundary / road widening alignment.
  - Can be relaxed to $1.8\\text{ meters}$ only in existing built-up streets with established average building lines.
- **Rear Open Space (പിൻവശത്തെ അകലം)**:
  - Minimum **$1.5\\text{ meters}$** average (never less than $1.0\\text{ meter}$ at any given point).
- **Side Open Spaces (വശങ്ങളിലെ അകലം)**:
  - Minimum **$1.2\\text{ meters}$** on one side and **$1.0\\text{ meter}$** on the other side.
  - Eaves/sunshades may project up to $0.6\\text{ meters}$ into setbacks.

---

## 3. Chapter VIII: Special Provisions for Small Plots (ചെറുകിട പ്ലോട്ടുകൾ $\\le$ 3 Cents)

To prevent unbuildable landlock situations in Kerala's densely populated areas, Chapter VIII provides explicit statutory concessions for plots **not exceeding $125\\text{ square meters}$ ($3.09\\text{ cents}$)**:

1. **Eligibility Criteria**:
   - The plot must have been legally partitioned or registered prior to the 2019 rules or derived from an approved sub-division layout.
   - Built-up area is restricted to Group A1 residential (maximum $150\\text{ m}^2$, up to two floors).
2. **Access Road Relaxation**:
   - Access pathway can be as narrow as **$1.2\\text{ meters}$** (pedestrian walkway).
3. **Setback Relaxations**:
   - **Front Setback**: Reduced to **$1.80\\text{ meters}$**.
   - **Rear Setback**: Reduced to **$1.00\\text{ meter}$**.
   - **Side Setback**: One side minimum **$0.90\\text{ meters}$**, and the other side can be reduced down to **$0.60\\text{ meters}$**.
   - **Zero Setback (Dead Wall / Blind Wall)**: A wall can be built directly on the boundary line without setbacks if:
     - The wall has **zero openings, doors, or windows** (dead wall).
     - The neighbor gives written consent / NOC, or statutory clearance is sanctioned under Rule 62.

---

## 4. Sanitation Clearances & Well Distance (കിണർ - സെപ്റ്റിക് ടാങ്ക് അകലം - Rule 91/92)

Under Kerala water safety and health regulations, the distance between any drinking water source and sewage disposal system is strictly enforced:

- **Well to Septic Tank / Leach Pit**: Minimum **$7.5\\text{ meters}$** ($24.6\\text{ feet}$) radius.
- **Neighbor's Septic Tank**: The $7.5\\text{m}$ clearance applies equally to a neighbor's septic tank, soak pit, or biological toilet pit across the boundary.
- **Boundary Clearance for Septic Tank**: Minimum **$1.2\\text{ meters}$** from the plot boundary, unless joint septic tanks or neighbor written consent is registered.

> [!CAUTION]
> In narrow Kerala plots (under 4 cents), establishing a $7.5\\text{m}$ clear circle between an open well/borewell and both your own and your neighbor's septic tanks is often geometrically impossible. Buyers must inspect neighboring soak pits before paying earnest money.

---

## 5. Electrical Line Clearances (വൈദ്യുതി ലൈൻ അകലം - Rule 25)

No building may be erected under or near Kerala State Electricity Board (KSEB) overhead power lines without mandatory horizontal and vertical clearances:

| Power Line Voltage | Vertical Clearance Required | Horizontal Clearance Required |
| :--- | :--- | :--- |
| **Low & Medium Tension (LT: $\\le 650\\text{ V}$)** | $2.5\\text{ meters}$ from roof/balcony | $1.2\\text{ meters}$ |
| **High Tension (HT: $11\\text{ kV}$ & $22\\text{ kV}$)** | $3.7\\text{ meters}$ | $1.8\\text{ meters}$ |
| **Extra High Tension ($33\\text{ kV}$ & above)** | $3.7\\text{ meters} + 0.3\\text{m}$ per $33\\text{ kV}$ | $2.0\\text{ meters}$ |

---

## 6. Pre-Purchase Legal Diligence Checklist for Kerala Buyers

Before paying earnest money (*Token Advance*) on any plot in Kerala:

1. [ ] **Verify Physical Road Width with Tape**: Do not trust deed recitals alone. Measure the narrowest choke point of the access road connecting the plot to the public PWD/Panchayat tar road. Is it at least $3.0\\text{ meters}$?
2. [ ] **Cross-Check Panchayat/Municipality Status**: Confirm whether the local body is a Grama Panchayat (KPBR) or Municipality/Corporation (KMBR).
3. [ ] **Confirm Road Ownership Type**: Is the access road a dedicated Panchayat public pathway, or a private right of way (*Nadappu vazhi*)? Private pathways require registered pathway ownership or unchallengeable registered easement deeds from all intervening landholders.
4. [ ] **Verify Plot Extent for Chapter VIII**: If relying on small plot relaxations, ensure the extent is strictly $\\le 125\\text{ m}^2$ (3.09 cents) and verified by a licensed surveyor.
5. [ ] **Check Neighbor Septic Pit Locations**: Walk the boundaries to identify the location of adjacent neighbors' septic tanks and leach pits relative to your proposed well/borewell.
"""


def generate_knowledge_doc() -> Path:
    """Writes the curated Kerala Building Rules knowledge document."""
    KNOWLEDGE_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    KNOWLEDGE_FILE.write_text(BUILDING_RULES_CONTENT, encoding="utf-8")
    print(f"✅ Successfully generated Kerala Building Rules knowledge document at: {KNOWLEDGE_FILE}")
    return KNOWLEDGE_FILE


if __name__ == "__main__":
    generate_knowledge_doc()
