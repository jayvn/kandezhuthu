# Plan

> Plans are temporary. Delete each item once it is implemented, and delete this file when it is empty.
> Finished work belongs in git history, not here.

Remaining work, ordered by impact within each section.

## UX

19. **The WhatsApp draft is pushed at the user.** It is step 4 of the progress line ("Ask seller"), the primary button on every result card, and the agent's prompt tells it to always add a "WhatsApp Message for Seller" section. Messaging the seller is a side feature, not the main job of the app.
    → Generate a draft only when the user asks for it. Take "Ask seller" out of the progress line and off the primary button, and offer "Draft a message to the seller" as a quieter option (e.g. in a card's actions or a ⋯ menu). Drop the always-on WhatsApp section from the agent instruction in `app/agent.py`, and have the agent draft one only on request.

## Tests

13. **UI tests reference removed elements.** `tests/ui/test_ui_playwright.py`, `test_contextual_chips_and_hud.py`, `test_cadastral_map_tools.py` and `test_bilingual_workflow_ui.py` look up IDs that no longer exist (`btn-undo`, `btn-hud-export`, `chip-sample-deed`, `legal-disclaimer`, `btn-pdf-export`, `step-nav-label`, `badge-kerala`, and since the UX pass `btn-next-step`, `chips-container`, `layman-card`, `tool-pin`, `btn-bhunaksha`, `exportPlotDossier`).
    → Update them to the new flow. Also replace the hardcoded `/ms-playwright/chromium-1234/...` browser path, and have the suite start the web UI itself (in demo mode, `app.fixtures.DEMO_ENV`) instead of expecting one on :8081.
15. **Live checks not yet done**: agent replies with real Gemini credentials (Markdown only, no LaTeX, no disclaimers), and satellite tiles on a normal network.

## Real data

20. **Timeline and PDF dossier only show demo presets.** They are hidden outside demo mode.
    → Feed them from a real `MunnadharamAuditor` result and a real EC audit, so a buyer's own chain can be shown and exported. Do not keep feeding them from `seed_demo_audit` (the invented Aluva Re-Sy 345/1 file).

21. **Nothing in `scrapers/` fetches, and a reseed would not pick up a fetch anyway.** `scrape_building_rules.py`, `scrape_paddy_land.py`, and `scrape_court_precedents.py` write markdown strings. `seed_building_rules`, `seed_paddy_land_fee_slabs`, and `seed_legal_precedents` ignore those files and insert a second hardcoded copy. Only `seed_knowledge_corpus_fts` reads `data/knowledge/*.md`. Fair value and resurvey SQL import the scraper classes, which return static lists. Every seeder returns when `COUNT(*) > 0`, so an existing `data/kandezhuthu.db` never updates.
    → One parser writes both the markdown and the SQL rows. Upsert on a natural key. Delete the `COUNT(*) > 0` early return for these tables.

22. **The building-rule rows cite the wrong instrument and the wrong rule, and the widths are not the table.** The repo says S.R.O. 777/2019 and 776/2019. S.R.O. 777/99 is the repealed 1999 municipality rules. In force:
    - KMBR 2019: G.O.(P) No. 77/2019/LSGD, Extraordinary No. 2691, **S.R.O. 828/2019**. PDF: `https://lsgkerala.gov.in/system/files/2019-11/kerala-municipality-building-rules-2019.pdf`
    - KPBR 2019: G.O.(P) No. 78/2019/LSGD, Extraordinary No. 2692, **S.R.O. 829/2019**
    - KPBR amendment now in force: G.O.(P) No. 54/2025/LSGD, 29 Oct 2025, **S.R.O. 1241/2025**. PDF: `https://lsgd.kerala.gov.in/wp-content/uploads/lsgd_orders_pdf/gz20251029_39868.pdf`
    - Municipality compilation, not yet extracted: `https://buildingpermit.lsgkerala.gov.in/Content/Rules/KBR2025.pdf` (last-modified 11 Feb 2026). Confirm it before copying panchayat numbers into KMBR rows.

    Access is **Rule 28, Table 7**, not Rule 5. Rule 5 is the permit application. 2019 KMBR Table 7, Group A1, by built-up area: up to 200 m² no minimum; above 200–400 m² is 1.5 m; above 400–4000 m² is 3.6 m. The 3 m figure is a proviso for off-street parking, and an A1 building of at most 8 units may use 2.4 m to that parking. The seeded row "single family up to 300 m² needs 3.0 m or the permit is refused" is not the table.

    S.R.O. 1241/2025 replaces KPBR Table 7 for Group A1:

    | Floor area | Minimum access |
    |---|---|
    | Single unit up to 300 m² | No minimum |
    | Multiple units up to 300 m² | 1.20 m |
    | Above 300 up to 600 | 2.00 m |
    | Above 600 up to 1000 | 3.00 m |
    | Above 1000 up to 4000 | 3.60 m |
    | Above 4000 up to 8000 | 5.00 m |
    | Above 8000 up to 18000 | 6.00 m |
    | Above 18000 up to 24000 | 7.00 m |
    | Above 24000 | 8.00 m |

    Substituted Table 8, Group F up to 300 m²: 1.20 m, not 3.6 m. Substituted Table 4, small plot (Group A1/F, built-up ≤ 200 m² and plot ≤ 125 m²): front 1.8 m average / 1.2 m minimum, rear 1.0 / 0.5, both sides 0.6 / 0.6. Standard A1: front 3.0 / 1.8, rear 1.5 / 1.0, sides 1.0 / 1.0. The seeded 0.9 m side and "Chapter VIII Rule 62" are not this table. Well-to-septic clearance of 7.5 m is real, but it is **Rule 75** (also 1.2 m from the boundary), not Rule 91/92.
    → Parse Table 7 and Table 4 out of those PDFs into `building_rules`. Separate KPBR and KMBR if the municipality amendment differs. `rule_citation` is the S.R.O. plus the rule and table, for example `KPBR Rule 28 Table 7, substituted by S.R.O. 1241/2025`. Drop the 3.0 m single-family row.

23. **Paddy fee slabs are the old corporation schedule, filed under the wrong G.O.** The seeder stores 0% / 10% / 20% / 30% by extent and cites G.O.(P) No. 167/2020/RD. The order quoted by the High Court in the conversion-fee appeals is **G.O.(Rt) No. 1166/2021/Rev, 25 Feb 2021**:
    - Up to 25 cents: no fee, only if that holding was already ≤ 25 cents on **30 Dec 2017**. A later split into 25-cent pieces is charged as one unit.
    - Above 25 cents: **10% of fair value**, same rate in panchayat, municipality, and corporation.
    - Above 1 acre: **20%**.
    - No 30% band. Thirty percent is the pre-2021 corporation rate.

    A 2023 High Court line computes the 10% only on the extent above 25 cents. That is case law, not the G.O.
    → Replace the four slabs with those three rows. Put the 30 Dec 2017 condition in `description`. Add the excess-over-25-cents computation as a `legal_precedents` row, not as `fee_percentage_of_fair_value`.

24. **Fair-value rows are round numbers with S.R.O. 420/2023 pasted on.** That S.R.O. (G.O.(P) No. 45/2023/TAXES) is a statewide percentage hike from 1 Apr 2023. It contains no rupees per are. The public register is `https://igr.kerala.gov.in/index.php/fairvalue/view_fairvalue`. District, RDO, taluk, and village are required; survey number is optional. View lists every survey in the village; Report exports it. Same survey is often several rows (road, interior, wet, commercial). This is a public rate card, not a title record: pull it by village, not one survey per request, and not as a deed scrape. Kerala is 14 districts, 27 revenue divisions, 78 taluks, on the order of 1,600 revenue villages. An older description of this site says the HTML is the **base** value and the hikes (S.R.O. 698/2014, then 420/2023) were applied outside the page. IGR timed out from the environment that checked it, so the form's XHR names are not confirmed, and whether the page is still pre-hike is not confirmed.
    → Walk district → RDO → taluk → village → Report. Before the batch, compare one survey you can see in a gazette and record whether 420/2023 is already in the figure; apply that factor to the whole table only if it is not. Add survey number, subdivision, block, desam, and land category to `fair_value_benchmarks`. Store the raw figure, `source=igr`, and `retrieved_at`. Do not set `gazette_notification` to S.R.O. 420/2023 unless the hike is confirmed inside the figure. Delete the seeded village rates. The host has to be one that can open IGR.

25. **Resurvey "status" is eight invented strings.** Phase lists (survey.entebhoomi village PDFs) are district, taluk, village, and hectares. They do not say "d-BTR Published" or "drone survey in progress." The data-portal chart of 239 Phase-2 villages is district area totals. G.O.(Ms) No. 7/2025/RD is what makes d-BTR the record after one-time verification.
    → Load a village as `listed in <notification>`, with the PDF URL on the row. Set a finalized status only when that village is named in an order under the Survey and Boundaries Act.

26. **Precedent rows are handwritten, and the markdown scraper does not query a court.** The documented API is `https://api.indiankanoon.org/search/?formInput=...&pagenum=0` with `Authorization: Token …`. Reference client: `sushant354/IKAPI` `python/ikapi.py` (POST, empty body, same header). Put `doctypes:kerala` or `doctypes:supremecourt` inside `formInput`. Paid per page.
    → Search, then store `case_name`, `citation`, `court`, `year`, and a short `key_principle` written for this app. Do not copy the judgment into `knowledge_corpus_fts`. Seed queries: Mary Roy, Section 27A conversion fee, Section 23 senior-citizen gifts, easement, HMGA Section 8(2), Suraj Lamp.

27. **`administrative_divisions` is 18 rows with codes like `SRO-EKM-01`.** The department has about 315 SROs.
    → Replace it with the Registration Department's office list. EC order-instructions (item 28) match against this list. Drop the fake codes.

28. **The buyer does not know which prior deeds to get, and a missing upload is called a competing title.** Public search is SRO + document number + year. Name and survey search is for the SRO, so there is no citizen query "every deed on survey 123/4." The EC is the index. Section 57 of the Registration Act, 1908, lets any person get a Book 1 copy; Book 4 wills are not the same. `audit_ec` already diffs EC document numbers against uploaded deeds, but only when the nature looks like a sale or `theeradharam`, and it files the miss as `conflicting_alienations` ("undisclosed partial sale," Section 48). Partitions, gifts, settlements, and releases never enter. `prior_doc_referenced` is unused. `sro_name` defaults to `"Kerala SRO"` when the header regex misses. Certified copy and online view are different products: the 2024 certified-copy SOP still ends at the SRO (copying fee, ₹50 stamp paper, print). PEARL View Document (`keralaregistration.gov.in/pearlpublic`, Queries → View → Document) is first-page preview, ₹100 for the full scan for 15 days. Pre-1980 scans were still a backlog in the 2024 PEARL note, with a 2025 target; do not hardcode a cutoff. The EC covers its search period only: a recital outside the window, a parent survey before subdivision, or another office will not be on it.
    → Gap list = union of parsed EC rows and `prior_doc_referenced` on uploaded deeds, minus uploaded documents. For each gap show document number, year, and SRO, matched to item 27. Name both PEARL actions: View Document (the scan to upload and OCR) and Certified Copy (SRO visit, for the advocate). Do not call a missing upload a competing title. Do not scrape PEARL or Ente Bhoomi.

29. **Data Bank and BhuNaksha still have no source that was verified.** There is no statewide parcel API for the LLMC data bank; what exists are local-body gazettes and land-use layers, which are not a BTR classification. Do not infer "not paddy" from a satellite tile. Whether a plot is in the data bank stays a document check: BTR says nilam or not, data-bank inclusion or not, Form 5 / Form 6 present or not.
    → Leave both as "not on file" until a gazette or an official extract for that village is in hand. Do not invent a status the way resurvey rows were invented.

## Structure

17. **Inline styles fight the theme.** CSS and JS now live in `static/app.css` and `static/js/*.js`, but `index.html` and the JS templates still carry ~200 inline `style=""` attributes, and `ft_theme.css` overrides them with `!important`.
    → Move them into classes as each area is touched, then drop the `!important`s.
