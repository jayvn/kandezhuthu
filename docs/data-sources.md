# Kerala property data: sources, scraping jobs, data model

The portals are what limit access, not the law. Kerala already publishes most of the district-wide data as gazette PDFs, district NIC documents and open GIS. The captcha in front of a deed scan is not hiding a second copy of those tables. So the database is built from gazettes and cadastral polygons, and the buyer's documents supply the property-specific side.

## Sources

| Dataset | What you get | Source | Effort |
|---|---|---|---|
| Fair-value gazette schedules | Survey/subdiv × land category × ₹/are, notification no., effective date | compose.kerala.gov.in eGazette, archive.org mirrors (`in.gazette.keralacompose`) | Low–medium |
| IGR fair-value village report | The IGR figures, one POST per village | igr.kerala.gov.in (needs a host that can reach it) | Medium |
| LLMC paddy/wetland data bank | Survey/subdiv, extent, class, per local body | `https://<district>.nic.in/` document libraries + gazette | Low–medium |
| Cadastral polygons | Parcel outline + survey number, no owners, CC0 | ramSeraph/indian_cadastrals (check coverage for each district) | Low |
| LGD village master | ~1,666 village codes | data.gov.in CSV | Low |
| IGR admin ids | District/RDO/taluk/village ids the form uses | Captured during the IGR crawl | Low, once IGR answers |
| SRO directory | ~315 offices | Registration Department office list | Low |
| Resurvey phase lists | Villages in each phase | survey.entebhoomi.kerala.gov.in PDFs | Low |
| Section 13 / 13A orders | Villages where the resurvey record is final | Gazette | Medium |
| LRIS layers | Land use, wetland, roads | KSLUB LRIS | Low–medium (access method still to confirm) |
| KPBR/KMBR, paddy fee G.O. | Rule tables, fee slabs | Official PDFs | Low |
| Judgments | Case, citation, short principle | Indian Kanoon API (paid per page) | Low |

**On demand only (buyer supplies):** deed, EC, BTR/d-BTR, tax receipt, possession certificate, survey sketch.

**Not collected:**
- Owner and possessor names. The data-bank PDFs print possessors because the gazette does. Drop that column at parse time. eMaps and Ente Bhoomi popups add the owner's name behind a captcha, and that field doesn't improve the audit because the buyer already has the deed. A statewide person → property list only lists people. It fills no gap in the title check.
- A bulk deed dump. PEARL has no survey-wide deed list, and Ente Bhoomi's ILIMS gateway isn't a public dump.

## The join problem

Everything hangs off survey numbers, and they don't agree across sources:

- Fair-value and data-bank gazettes often use old survey numbers. Resurveyed villages use re-survey numbers. The cadastral layer uses whichever its source had.
- IGR, LGD and the gazettes spell village names differently.

So the first build job is two crosswalks:

1. LGD code ↔ IGR village id ↔ gazette spelling. LGD is the join key and the list of villages still unmatched. It is never the IGR POST body.
2. Old survey ↔ re-survey, per village. The resurvey records and BTR documents carry both numbers.

Without these crosswalks, no check below is reliable.

## Data model

### Gazette index first

The gazette is the main data source, published as PDFs. Index it once, then let each parser read from the index:

```
gazette_documents
  gazette_id, publication_date, department, notification_no,
  sro_no, go_no, title, keywords, source_url, mirror_url,
  local_pdf, sha256, doc_type, parsed_at
```

The compose record is the identity, and archive.org is only a mirror. Dedupe on sha256. Parsers: fair value, data bank, Section 13/13A, building rules. None of them searches for PDFs again.

### Store observations, not a merged answer

```
parcel_observation
  parcel_key        (village LGD code + survey + subdiv)
  source            FAIR_VALUE | LLMC_DATA_BANK | LRIS | CADASTRAL | BTR | DEED | RESURVEY
  attribute         classification | area_are | inr_per_are | listed
  value
  evidence          notification no. / S.R.O. / document no.
  source_url, sha256, retrieved_at
```

Never collapse sources into one `land_type` or one `area`. When records disagree, that disagreement is the finding. Area stays as separate figures (deed, BTR, cadastral GIS, resurvey), and none of them is picked silently.

## Jobs

### 1. Fair value, from the gazette

Individual RDO notifications are ordinary gazette PDFs, and they are mirrored. Example: Adoor, Pathanamthitta, RDOADR/648/2025-C5, on archive.org as a compose gazette. Its schedule is by survey number, and column 11 is the figure. The notification itself says the resultant fair value is 264% of the figure in the schedule.

- Search compose eGazette: department Revenue, keywords `fair value` / `ന്യായവില` / `28A`, type Extraordinary. Download the results. Don't click View Fair Value village by village.
- Parse column 11 as `base_inr_per_are`, for each survey and land category.
- Store `notified = base × multiplier` only when that notification prints the multiplier line. Later notifications that already print the revised figure get none.
- Don't derive the multiplier from S.R.O. arithmetic. S.R.O. 420/2023 is a +20% hike from 1 Apr 2023. Older copies of IGR served the base figure and expected S.R.O. 698/2014 to be applied separately. Use what the notification prints.

### 2. Fair value, from IGR (check and fill gaps)

Target the village report, not the survey box: ~1,666 villages, one POST per village, which returns every survey × land category. Leave survey, desam and block empty.

```
GET  https://igr.kerala.gov.in/index.php/fairvalue/view_fairvalue
     parse the district <select>, or whatever its onchange fires
GET  the district → RDO → taluk → village calls the page already makes
POST view with the village id set and the survey fields blank
```

- Drive the dropdowns from the form. Post IGR's ids and spelling, not LGD names.
- The XHR paths aren't in any public client. Log them once from a browser on the first district, then hardcode them.
- igr.kerala.gov.in timed out from the checking host. registration.kerala.gov.in answered. Run this job from a host where IGR answers.
- Result pages list ₹/are, often several rows per survey (road, interior, wet, commercial). Some link the gazette PDF for that notification. Keep the HTML and the PDF.

```
data/raw/fairvalue/{district}/{village}.html
data/raw/fairvalue/{district}/{village}.pdf    # if the page offered one
data/raw/fairvalue/rows.jsonl
```

`rows.jsonl` columns: district, rdo, taluk, village, desam, block, survey, subdiv, resurvey, resurvey_subdiv, land_type, raw_inr_per_are, page_url, retrieved_at.

- Leave out `gazette_notification` until the linked PDF, or a survey you can check against a gazette, shows whether the hike is already in the figure. Compare one row against a gazette on the first village. If the page shows the base figure, record the multiplier once and apply it at SQL load time. Don't rewrite the raw file.
- Keep a resume file: village id → fetched | empty | error. Run one worker. Retry on 429/5xx.
- A village with zero rows is a parse bug, not a success.
- Replace `fair_value_benchmarks`, add the survey columns, and delete the seeded round numbers.

### 3. Paddy data bank

LLMC data-bank lists are gazette PDFs, one local body at a time, hosted on district NIC sites. Example: kannur.nic.in lists Pattuvam, Thalassery, Mattannur and others. A Kottayam page is a table of survey, subdivision, extent, and whether each row is paddy.

- Crawl the 14 district NIC document libraries, plus a compose search for `data bank` / `നിലം`.
- Parse survey, block, subdivision, extent, class. Drop names.
- This gives the Form 5 check the app doesn't have yet: a survey number in this PDF means it is in the data bank.

### 4. Parcel shape and village keys

- indian_cadastrals: Kerala polygons + survey numbers → outline, and a GIS area to compare with the deed.
- LGD CSV: village codes for the crosswalk.
- LRIS: land-use, wetland and road layers. Label wetland as land-use, not BTR. Nilam for a permit comes from the data-bank PDF plus the BTR classification on the buyer's document.

### 5. Building rules

No HTML to crawl, just PDFs:

```
https://lsgkerala.gov.in/system/files/2019-11/kerala-municipality-building-rules-2019.pdf
    KMBR 2019, S.R.O. 828/2019: Rule 28 Table 7, Rule 75 (7.5 m well)
https://lsgd.kerala.gov.in/wp-content/uploads/lsgd_orders_pdf/gz20251029_39868.pdf
    KPBR amendment, S.R.O. 1241/2025, replaces Table 4 and Table 7
https://buildingpermit.lsgkerala.gov.in/Content/Rules/KBR2025.pdf
    municipality compilation, last-modified 11 Feb 2026. Read its S.R.O. before using it.
```

- KPBR 2019 base: S.R.O. 829/2019, G.O.(P) No. 78/2019/LSGD, Extraordinary No. 2692. Pull it from the gazette, not the scraper's "776/2019".
- Use pdfplumber on Table 7 and Table 4 only. Write one row per occupancy band. Set `rule_citation` to the S.R.O. that actually substituted the table.
- Keep KPBR and KMBR as separate rows where the tables differ.
- The 2019 KMBR text doesn't say "3 m for a house under 300 m²". That figure is the off-street-parking proviso.

### 6. Paddy conversion fee

Not a crawl. One order, three rows: G.O.(Rt) No. 1166/2021/Rev (25 Feb 2021).

- ≤ 25 cents: free, only if the holding was already ≤ 25 cents on 30 Dec 2017
- Above 25 cents: 10% of fair value
- Above 1 acre: 20%

There is no 30% slab. The reading that charges only on the extent above 25 cents goes in as a precedent row, not as a fee percentage.

### 7. Resurvey

- Download the phase village-list PDFs from survey.entebhoomi.kerala.gov.in. Phase III is already a flat district / taluk / village / hectares table.
- Parse into `digital_resurvey_villages`, with status `listed in <filename>` and the PDF URL.
- Write "d-BTR Published" only for a village named in a Section 13 / 13A order.
- G.O.(Ms) No. 7/2025/RD is the rule that d-BTR replaces the paper BTR after one-time verification. It is not a village list.

### 8. Judgments

```
POST https://api.indiankanoon.org/search/?formInput=<q>&pagenum=<n>
Authorization: Token <token>
Accept: application/json
```

Same request shape as sushant354/IKAPI `python/ikapi.py`. Page each query until it comes back empty:

```
doctypes:kerala "section 27A" paddy
doctypes:kerala "section 23" "senior citizen" gift
doctypes:supremecourt "Mary Roy" Kerala
doctypes:supremecourt easement pathway
doctypes:supremecourt "section 8" "minor" immovable
doctypes:supremecourt "Suraj Lamp"
```

Keep docid, title, citation, court, year, and a short principle written for the auditor. Don't store the full text in `knowledge_corpus_fts`.

### 9. SRO list

Load the department's office directory (~315 offices) into `administrative_divisions`. Also keep the district / RDO / taluk / village ids from the IGR crawl, because the next fair-value run replays them. Census and LGD codes are a crosswalk, not the POST body.

### 10. Deeds

Nothing to crawl. Citizen search is SRO + document number + year, and there is no survey-wide listing. The EC the buyer uploads is the list. After `ec_parser` runs, the only fetch left is for each missing document number:

- PEARL View Document: ₹100 for the scan, viewable for 15 days
- Certified copy: still finished at the SRO

Both need the document number first. Skipping the EC doesn't unlock a dump.

## Load

- Parsers write `data/raw/*.jsonl`. One loader upserts SQLite on natural keys.
- Drop the `COUNT(*) > 0` early returns in `seed_data.py`, or new rows never replace the seeded ones.
- Generate the markdown in `data/knowledge/` from the same JSONL, not from strings in the current scraper files.

## What the buyer sees

Say the deed reads "Village A, Re-Sy 173/14, 8.25 are, purayidam." The database adds:

- Cadastral 173/14: GIS area ≈ 8.3 are (a small difference, not a flag)
- Fair value: category and ₹/are from the named notification
- Data bank: 173/14 listed in [gazette, date]
- LRIS: polygon overlaps mapped wetland (a land-use layer, not a revenue classification)

> **Land classification mismatch**
> Deed: Purayidam · BTR: Purayidam · Data bank: listed ([gazette]) · LRIS: wetland overlap
> Next: get the data-bank removal order or Form 5/6 before relying on building on this plot.

The app doesn't decide which record prevails. It shows the conflict and the document that would settle it.

## First-district MVP

Pick one district where all of these exist:

1. Cadastral polygons + LGD/IGR village crosswalk
2. Old ↔ re-survey crosswalk
3. Fair-value gazettes (IGR used to check and fill gaps)
4. Data-bank gazettes
5. LRIS land use / wetland / roads
6. Resurvey phase lists + Section 13/13A orders

Plus the rules, fee and judgment tables. The property-specific analysis starts when the buyer uploads deed + EC + BTR.

If the gazette crawl leaves gaps, ask the Registration Department for the fair-value master as a spreadsheet. They already keep it as a table, and that request works more often than another pass at the HTML form.
