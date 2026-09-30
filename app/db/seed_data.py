"""Seed script to populate Kandezhuthu database with Kerala land data.

Ingests:
1. Building Rules (KPBR / KMBR 2019) dimensional setback & road width tables.
2. Paddy Land 2008 Section 27A conversion fee slabs.
3. Landmark Kerala Judicial Precedents (into legal_precedents & legal_precedents_fts).
4. Full text knowledge articles (into knowledge_corpus_fts).
5. Kerala Administrative master records (Districts, Taluks, SROs).
6. Demo mode only: fair values, resurvey villages and a demo title audit from `tests/fixtures/`.
"""

from pathlib import Path

from app import fixtures
from app.db.database import get_db_connection, init_db

KNOWLEDGE_DIR = Path(__file__).resolve().parent.parent.parent / "data" / "knowledge"


def seed_building_rules(conn):
    """Seeds KMBR/KPBR 2019 setback & road width rules."""
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM building_rules")
    if cursor.fetchone()[0] > 0:
        return

    rules = [
        (
            "Group A1: Residential (Single Family)",
            "standard",
            3.09,
            50.0,
            300.0,
            3.0,
            3.0,
            1.5,
            1.2,
            1.0,
            7.5,
            0,
            "KPBR/KMBR 2019 Rule 5 & Rule 26",
            "Mandatory 3.0m motorable access road. Standard setbacks: front 3m, rear 1.5m, sides 1.2m & 1.0m.",
        ),
        (
            "Group A1: Small Plot Concession",
            "small_plot",
            0.0,
            3.09,
            150.0,
            1.2,
            1.8,
            1.0,
            0.9,
            0.6,
            7.5,
            1,
            "KPBR/KMBR 2019 Chapter VIII (Rule 62)",
            "Plots <= 3.09 cents (125 sq m). Concession pathway down to 1.2m allowed. Dead wall with 0 setback allowed with neighbor NOC.",
        ),
        (
            "Group A1: Ultra-Small Plot Concession",
            "ultra_small_plot",
            0.0,
            2.0,
            100.0,
            1.2,
            1.0,
            1.0,
            0.9,
            0.6,
            7.5,
            1,
            "KPBR/KMBR Amendments (2023-2025)",
            "Plots <= 81 sq m (approx 2 cents) with built-up area <= 100 sq m abutting road <= 3m: front setback relaxed down to 1.0m.",
        ),
        (
            "Group A1: Multiple Family / Apartments",
            "commercial_residential",
            10.0,
            500.0,
            1000.0,
            5.0,
            5.0,
            3.0,
            2.0,
            2.0,
            7.5,
            0,
            "KPBR/KMBR 2019 Rule 5 Table 1",
            "Multi-family / apartment complexes (300-1000 sqm). Min 5.0m clear motorable access road.",
        ),
        (
            "Group A1: High-rise Residential",
            "high_rise",
            20.0,
            2000.0,
            10000.0,
            7.0,
            6.0,
            5.0,
            5.0,
            5.0,
            7.5,
            0,
            "KPBR/KMBR 2019 Chapter XVII (High-rise)",
            "Building height exceeding 16 meters. Mandatory 7.0m motorable road for fire tender access.",
        ),
        (
            "Group F: Mercantile (Commercial Shops)",
            "commercial",
            2.0,
            100.0,
            150.0,
            3.6,
            3.0,
            1.5,
            1.2,
            1.0,
            7.5,
            0,
            "KPBR/KMBR 2019 Rule 5 Table 2",
            "Small commercial shops up to 150 sqm. Minimum 3.6m access road.",
        ),
    ]

    cursor.executemany(
        """
        INSERT INTO building_rules (
            occupancy_group, plot_category, min_plot_cents, max_plot_cents,
            max_builtup_sqm, min_road_width_m, front_setback_m, rear_setback_m,
            side_setback_1_m, side_setback_2_m, well_septic_clearance_m,
            dead_wall_permitted, rule_citation, notes
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        rules,
    )


def seed_paddy_land_fee_slabs(conn):
    """Seeds Kerala Paddy Land Act Section 27A fee slabs."""
    cursor = conn.cursor()
    cursor.execute("DELETE FROM paddy_land_fee_slabs")

    citation = "Section 27A, Kerala Conservation of Paddy Land and Wetland Act, 2008; G.O.(Rt) No. 1166/2021/Rev, 25 Feb 2021"
    slabs = [
        (
            0.0,
            25.0,
            0.0,
            "No fee, only if the holding was already 25 cents or less on 30 Dec 2017. "
            "A later split of a larger holding into 25-cent pieces is charged as one unit.",
            citation,
        ),
        (
            25.0,
            100.0,
            10.0,
            "Holding above 25 cents up to 1 acre: 10% of fair value, same rate in panchayat, municipality and corporation.",
            citation,
        ),
        (
            100.0,
            99999.0,
            20.0,
            "Holding above 1 acre (100 cents): 20% of fair value.",
            citation,
        ),
    ]

    cursor.executemany(
        """
        INSERT INTO paddy_land_fee_slabs (
            min_cents, max_cents, fee_percentage_of_fair_value, description, statutory_citation
        ) VALUES (?, ?, ?, ?, ?)
        """,
        slabs,
    )


def seed_legal_precedents(conn):
    """Seeds Kerala High Court & Supreme Court precedents."""
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM legal_precedents")
    if cursor.fetchone()[0] > 0:
        return

    precedents = [
        (
            "Mary Roy v. State of Kerala",
            "1986 AIR 1011 / 1986 SCR (1) 371",
            "Supreme Court of India",
            1986,
            "christian_succession",
            "Declared Travancore/Cochin Christian Succession Acts void retrospective to 1951. Christian daughters have equal intestate succession rights as sons under the Indian Succession Act, 1925. Note: Partition challenges are strictly subject to 12-year limitation under Article 65 of Limitation Act from date of open ouster.",
            "Deeds post-1951 where property of an intestate Christian father was partitioned or sold without female siblings joining as executing parties.",
            "Obtain registered Ozhivumuri (Release Deed) or Supplementary Partition Deed with female heirs as co-executants before token advance, unless clearly barred by long-standing ouster exceeding 12 years.",
            "Indian Succession Act, 1925, Section 37; Limitation Act 1963, Article 65; Article 14 Constitution of India",
        ),
        (
            "Sudesh Chhikara v. Ramti Devi",
            "2022 SCC OnLine SC 1684",
            "Supreme Court of India",
            2022,
            "senior_citizen_maintenance",
            "Under Section 23(1) of the Senior Citizens Act 2007, a transfer can be declared void ONLY IF the deed contains an EXPLICIT condition that the transferee shall provide basic amenities and physical needs. Merely reciting 'love and affection' is a motive, not a condition. Without an express condition, Maintenance Tribunal has no jurisdiction to revoke the deed.",
            "Threat of cancellation under Section 23 by elderly parents where gift/settlement deed lacks an explicit maintenance condition.",
            "Inspect registered deed text: if no explicit clause mandating physical maintenance exists, subsequent purchaser is legally protected against Section 23 cancellation under Sudesh Chhikara.",
            "Maintenance and Welfare of Parents and Senior Citizens Act, 2007, Section 23(1)",
        ),
        (
            "Subhashini v. District Collector, Kozhikode",
            "2020 (5) KLT 403 (FB)",
            "Kerala High Court Full Bench",
            2020,
            "senior_citizen_maintenance",
            "Section 23 of Senior Citizens Act 2007 requires an explicit or clearly ascertainable condition that the transferee shall maintain the senior citizen. If breach occurs and condition exists, RDO Tribunal can declare the transfer void.",
            "Title deeds where property was acquired via Gift Deed (Dhanam) or Settlement from elderly parents.",
            "Inspect parent gift deed for maintenance recitals. Require senior citizen parent to be a concurring witness or sign an affidavit of satisfaction.",
            "Maintenance and Welfare of Parents and Senior Citizens Act, 2007, Section 23",
        ),
        (
            "State of Kerala v. Landowner (Paddy Fee Exemption)",
            "2025 Supreme Court",
            "Supreme Court of India",
            2025,
            "paddy_land_conversion",
            "The 25-cent fee exemption under Section 27A applies strictly only if the total landholding is 25 cents or less. There is NO pro-rata deduction: if a parcel exceeds 25 cents, conversion fee must be paid on the ENTIRE extent. Anti-fragmentation rule: parcels fragmented from larger units after 30 Dec 2017 are ineligible for 0% fee.",
            "Plots claiming 25-cent free exemption where total holding exceeds 25 cents, or land was subdivided after 30 Dec 2017.",
            "Calculate statutory conversion fee across entire plot extent if > 25 cents. Verify parent title for holding size as of 30 Dec 2017.",
            "Kerala Conservation of Paddy Land and Wetland Act, 2008, Section 27A; G.O.(P) No. 1166/2020/Rev",
        ),
        (
            "Sree Swayamprakash Ashramam v. G. Anandavally Amma",
            "2010 (2) SCC 689",
            "Supreme Court of India",
            2010,
            "easements_pathway",
            "Easement of necessity or quasi-easement: Pathway rights granted in earlier deeds run with the dominant heritage and cannot be unilaterally closed by subsequent purchasers.",
            "Recitals reserving 'Nadappu vazhi', 'Vazhi avakasham', or shared passage along northern/southern boundary.",
            "Conduct physical boundary survey. If pathway exists, obtain written relinquishment release or factor reduced usable area.",
            "Indian Easements Act, 1882, Sections 13 & 15",
        ),
        (
            "Vineeta Sharma v. Rakesh Sharma",
            "2020 (9) SCC 1",
            "Supreme Court of India (3-Judge Bench)",
            2020,
            "hindu_coparcenary",
            "Daughters have equal coparcenary birthright in Hindu Undivided Family (HUF) ancestral property under Section 6 HSA, even if father passed away before 9 Sept 2005 amendment.",
            "Partition deeds or alienation of ancestral Hindu property without signature of living or deceased daughter's legal heirs.",
            "Examine genealogy tree. Verify whether property was self-acquired or ancestral coparcenary property. Obtain release from all coparceners.",
            "Hindu Succession (Amendment) Act, 2005, Section 6",
        ),
        (
            "Saroj v. Sunder Singh",
            "2014 (15) SCC 727",
            "Supreme Court of India",
            2014,
            "minor_property_hindu",
            "Under Section 8(2) HMGA 1956, natural guardian cannot sell, gift, or mortgage minor's immovable property without prior permission of the District Court. Any unauthorized disposal is voidable at minor's instance.",
            "Prior deed where parents or guardian sold land on behalf of minors without mentioning District Court O.P. Sanction Order.",
            "Verify whether minor has attained 21 years (3 years after turning 18). If within 3 years of majority, obtain registered ratification deed.",
            "Hindu Minority and Guardianship Act, 1956, Section 8(2)",
        ),
        (
            "Imambandi v. Mutsaddi",
            "1918 (45) IA 73 (Privy Council) & Mohd. Amin v. Vakil Ahmad (1952 AIR 358)",
            "Privy Council / Supreme Court of India",
            1918,
            "minor_property_muslim",
            "Under Mohammedan Law, a de facto guardian (such as mother or brother) has zero legal power or authority to alienate minor's immovable property. Such alienations are ab initio VOID.",
            "Sale deeds executed by Muslim mother on behalf of her minor children without appointment by Court under Guardians and Wards Act, 1890.",
            "Sale is void. Fresh conveyance or registered ratification from the erstwhile minor upon attaining majority is strictly required.",
            "Principles of Mohammedan Law; Guardians and Wards Act, 1890",
        ),
        (
            "Suraj Lamp & Industries Pvt. Ltd. v. State of Haryana",
            "2012 (1) SCC 656",
            "Supreme Court of India",
            2012,
            "power_of_attorney_fraud",
            "General Power of Attorney (GPA / Mukthiyar) or Agreement to Sell does not convey title or ownership. Immovable property can only be transferred by a registered deed of conveyance.",
            "Purchasing property on the basis of an unregistered or expired GPA, or where principal died prior to deed registration.",
            "Ensure PoA is registered at SRO. If executed overseas, ensure stamping by Kerala District Collector within 3 months. Confirm principal is alive.",
            "Transfer of Property Act 1882 Sec 54; Registration Act 1908 Sec 17; Powers of Attorney Act 1882",
        ),
        (
            "Kudikidappu Tenancy Rights (Kerala Land Reforms Act)",
            "Sections 75 to 80B, Kerala Land Reforms Act, 1963",
            "Kerala High Court & Land Tribunal Precedents",
            1963,
            "kudikidappu_tenancy",
            "Kudikidappukars (hutment dwellers) possess permanent non-evictable statutory occupancy rights and purchase certificate rights up to 10 cents in Panchayats and 3 cents in Municipalities.",
            "Old family estates or ancestral parambus with unverified huts, caretakers, or agricultural workers residing on the land.",
            "Conduct physical inspection of land for residential dwellings. Verify Revenue Land Tribunal register for unassigned Kudikidappu purchase certificates.",
            "Kerala Land Reforms Act, 1963, Sections 75-80B",
        ),
        (
            "Doctrine of Lis Pendens (T.G. Ashok Kumar v. Govindammal)",
            "2010 (14) SCC 370",
            "Supreme Court of India",
            2010,
            "lis_pendens_litigation",
            "Under Section 52 of Transfer of Property Act, any transfer of property during pendency of a suit in court is subordinate to the rights of the decree holder.",
            "Discrepancies in revenue tax receipts, active boundary disputes, or unfiled court caveats.",
            "Run EC cross-check for court attachment notices. Search Kerala e-Courts database for pending OS or CMA cases against seller.",
            "Transfer of Property Act, 1882, Section 52; CPC Order 38 Rule 5",
        ),
        (
            "Adverse Possession vs. Government Puramboke (Joseph v. State of Kerala)",
            "2023 (KHC)",
            "Kerala High Court",
            2023,
            "puramboke_encroachment",
            "No adverse possession can be claimed against Government Puramboke land, road alignments, or river/thodu boundaries. Kerala Land Conservancy Act empowers immediate eviction.",
            "Land where registered extent on paper is 12 cents but physical fencing encloses 15 cents adjoining a canal (thodu) or road puramboke.",
            "Verify Village Survey Sketch and Taluk Resurvey FMB. Ensure purchase consideration only covers surveyed registered patta land.",
            "Kerala Land Conservancy Act, 1957, Section 3 & Limitation Act 1963 Art 112",
        ),
        (
            "R.D.O. Fort Kochi v. Jalaja Dileep & Baby v. Collector",
            "2015 (1) KLT 984 (SC) & 2021 (6) KLT 316 (DB)",
            "Supreme Court / Kerala High Court",
            2015,
            "paddy_land_conversion",
            "Lands converted prior to 12-08-2008 and not included in Data Bank are 'Unnotified Lands'. Section 27A applies for BTR reclassification, with statutory exemption from fee up to 25 cents.",
            "Land described as Nilam or Nanja in Village BTR or Prior Deeds but physically appearing as garden land with grown trees.",
            "Confirm exclusion from LLMC Data Bank via Village Office. Apply for Form 6 under Section 27A. Zero fee applies if <= 25 cents.",
            "Kerala Conservation of Paddy Land & Wetland Act, 2008, Section 27A; Kerala Land Tax Act 1961 Sec 6A",
        ),
    ]

    cursor.executemany(
        """
        INSERT INTO legal_precedents (
            case_name, citation, court, year, category, key_principle,
            risk_trigger, remedial_action, statute_reference
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        precedents,
    )

    # Populate FTS5 table
    cursor.execute("""
        INSERT INTO legal_precedents_fts (rowid, case_name, category, key_principle, risk_trigger, remedial_action, statute_reference)
        SELECT id, case_name, category, key_principle, risk_trigger, remedial_action, statute_reference FROM legal_precedents
    """)


def seed_knowledge_corpus_fts(conn):
    """Indexes markdown knowledge files into knowledge_corpus_fts."""
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM knowledge_corpus_fts")
    if cursor.fetchone()[0] > 0:
        return

    articles = [
        ("building_rules", "Kerala Building Rules (KMBR & KPBR 2019)", "building_rules_kmbr_kpbr.md", "road width, setback, small plot, kmbr, kpbr, septic, open well"),
        ("paddy_land", "Kerala Conservation of Paddy Land & Wetland Rules 2008", "paddy_land_wetland_guide.md", "nilam, purayidam, form 5, form 6, 27a, data bank, btr, unnotified, fee slab"),
        ("court_precedents", "Landmark Kerala Judicial Precedents & Title Trap Rules", "kerala_court_precedents.md", "mary roy, subhashini, senior citizens, easement, minor property, imambandi, saroj, vineeta sharma, suraj lamp, kudikidappu, lis pendens, puramboke"),
    ]

    for topic, title, filename, tags in articles:
        filepath = KNOWLEDGE_DIR / filename
        if filepath.exists():
            content = filepath.read_text(encoding="utf-8")
            cursor.execute(
                "INSERT INTO knowledge_corpus_fts (topic, title, content, tags) VALUES (?, ?, ?, ?)",
                (topic, title, content, tags),
            )


def seed_administrative_divisions(conn):
    """Seeds Kerala 14 Districts and key SROs."""
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM administrative_divisions")
    if cursor.fetchone()[0] > 0:
        return

    divisions = [
        ("Ernakulam", "Aluva", "Aluva West", "Aluva", "SRO-EKM-01"),
        ("Ernakulam", "Aluva", "Aluva East", "Aluva", "SRO-EKM-01"),
        ("Ernakulam", "Kanayannur", "Ernakulam", "Ernakulam", "SRO-EKM-02"),
        ("Ernakulam", "Kochi", "Mattancherry", "Mattancherry", "SRO-EKM-03"),
        ("Ernakulam", "Kunnathunad", "Perumbavoor", "Perumbavoor", "SRO-EKM-04"),
        ("Thiruvananthapuram", "Thiruvananthapuram", "Pattom", "Thiruvananthapuram", "SRO-TVM-01"),
        ("Thiruvananthapuram", "Neyyattinkara", "Neyyattinkara", "Neyyattinkara", "SRO-TVM-02"),
        ("Kollam", "Kollam", "Kollam East", "Kollam", "SRO-KLM-01"),
        ("Thrissur", "Thrissur", "Thrissur", "Thrissur", "SRO-TSR-01"),
        ("Kozhikode", "Kozhikode", "Kozhikode City", "Kozhikode", "SRO-KKD-01"),
        ("Kottayam", "Kottayam", "Kottayam", "Kottayam", "SRO-KTM-01"),
        ("Palakkad", "Palakkad", "Palakkad", "Palakkad", "SRO-PLK-01"),
        ("Malappuram", "Eranad", "Manjeri", "Manjeri", "SRO-MLP-01"),
        ("Alappuzha", "Ambalappuzha", "Alappuzha", "Alappuzha", "SRO-ALP-01"),
        ("Kannur", "Kannur", "Kannur", "Kannur", "SRO-KNR-01"),
        ("Pathanamthitta", "Kozhencherry", "Pathanamthitta", "Pathanamthitta", "SRO-PTA-01"),
        ("Idukki", "Thodupuzha", "Thodupuzha", "Thodupuzha", "SRO-IDK-01"),
        ("Wayanad", "Vythiri", "Kalpetta", "Kalpetta", "SRO-WYD-01"),
        ("Kasaragod", "Kasaragod", "Kasaragod", "Kasaragod", "SRO-KSD-01"),
    ]

    cursor.executemany(
        """
        INSERT INTO administrative_divisions (district, taluk, village, sro_name, sro_code)
        VALUES (?, ?, ?, ?, ?)
        """,
        divisions,
    )


def seed_demo_audit():
    """Seeds the demo title audit from fixtures (demo mode only)."""
    demo = fixtures.load("demo_audit")
    if not demo:
        return

    from app.db.repository import AuditRepository
    from app.domain.auditor import MunnadharamAuditor
    from app.domain.models import DeedNode, ECRecord

    repo = AuditRepository()
    if repo.get_property_audit_history(survey_no=demo["survey_no"], village=demo["village"]):
        return

    deeds = [DeedNode(**d) for d in demo["deeds"]]
    ec_records = [ECRecord(**e) for e in demo["ec_records"]]
    scorecard = MunnadharamAuditor(property_identifier=demo["property_identifier"]).audit(
        deeds=deeds, ec_records=ec_records
    )
    repo.save_audit(
        property_identifier=demo["property_identifier"],
        survey_no=demo["survey_no"],
        deeds=[d.model_dump(mode="json") for d in deeds],
        ec_records=[e.model_dump(mode="json") for e in ec_records],
        scorecard=scorecard.model_dump(mode="json"),
        session_id="demo_session",
        village=demo["village"],
        taluk=demo["taluk"],
        district=demo["district"],
        sro_name=demo["sro_name"],
    )


def seed_fair_value_benchmarks(conn):
    """Seeds Kerala notified benchmark Fair Values per Are under Section 28A."""
    benchmarks = fixtures.load("fair_value_benchmarks", [])
    if not benchmarks:
        return

    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM fair_value_benchmarks")
    if cursor.fetchone()[0] > 0:
        return

    rows = [
        (
            b["district"],
            b["taluk"],
            b["village"],
            b["local_body_type"],
            b["land_type"],
            b["fair_value_per_are_inr"],
            b["effective_year"],
            b["gazette_notification"],
        )
        for b in benchmarks
    ]
    cursor.executemany(
        """
        INSERT INTO fair_value_benchmarks (
            district, taluk, village, local_body_type, land_type,
            fair_value_per_are_inr, effective_year, gazette_notification
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        rows,
    )


def seed_digital_resurvey_villages(conn):
    """Seeds Kerala Digital Resurvey (Ente Bhoomi) village rollout statuses."""
    records = fixtures.load("digital_resurvey_villages", [])
    if not records:
        return

    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM digital_resurvey_villages")
    if cursor.fetchone()[0] > 0:
        return

    rows = [
        (
            r["district"],
            r["taluk"],
            r["village"],
            r["phase"],
            r["status"],
            r["portal_url"],
            r["advisory"],
        )
        for r in records
    ]
    cursor.executemany(
        """
        INSERT INTO digital_resurvey_villages (
            district, taluk, village, phase, status, portal_url, advisory
        ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        rows,
    )


def seed_all():
    """Initializes schema and seeds all master and knowledge data."""
    init_db()
    with get_db_connection() as conn:
        seed_building_rules(conn)
        seed_paddy_land_fee_slabs(conn)
        seed_legal_precedents(conn)
        seed_knowledge_corpus_fts(conn)
        seed_administrative_divisions(conn)
        seed_fair_value_benchmarks(conn)
        seed_digital_resurvey_villages(conn)
    seed_demo_audit()
    print("✅ Successfully seeded all Kandezhuthu database tables!")


if __name__ == "__main__":
    seed_all()

