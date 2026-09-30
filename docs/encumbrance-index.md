# Encumbrance index: technical plan

Technical plan only, with no legal section and nothing built yet. The index is the join, not the walk.

**Open against the rest of the repo.** `PLAN.md` item 28 and `docs/data-sources.md` §10 say not to scrape PEARL and that there is no deed list to crawl. This plan walks document details by `(SRO, year, number)`. It also stores parties from the payload, while `data-sources.md` drops possessor names. Decide which rule holds before any walk code lands.

Vectors, as used below:

1. Document details fetched by `(SRO, year, number)`
2. Ente Bhoomi / cadastral features
3. Monthly registration figures
4. Judgments and auction notices

## Product

An encumbrance index: for a canonical parcel, every Book document whose schedule hits it, ordered in time. Chain edges exist only where a recital names a prior document. If the metadata payload has no recital, call the result an index, not a chain of title. Do not infer ownership from party-name matching in v1.

## What is wrong with the four vectors as written

Vector 1 treats `(SRO, year, n)` as a dense counter. It is not. Holes are cancelled or refused numbers, and one empty response is not the end of the range. A binary search for `N_max` will stop early.

Vector 1 also stores a schedule string as if it were a key. It is prose. Without a parser and an SRO-in-force gazetteer, the inverted index splits one holding and glues strangers together.

Vector 2 is a parcel spine for resurveyed villages only (phase 1 is about 200 villages; phase 2 is partial). It usually carries the latest mutation, not the history. Use it as the dimension table, not as the event log.

Vector 3, if it is only district or SRO totals, does not list document numbers. It is still useful as a checksum and as the incremental cursor. It is not a backfill.

Vector 4 is the labeled set. Run it first. It is not a coverage layer.

## Order of work

**1. Ground truth, before any walk.** Parse High Court, Land Board, and SARFAESI or DRT texts for explicit `Doc no / year / SRO` chains and for schedules that cite both old survey and resurvey. Freeze a few dozen parcels whose chain is already written out in a judgment. Every later stage is scored against that set.

**2. Confirm the payload.** For those known document numbers, record which fields actually come back from document details: nature, date, parties, consideration, raw schedule, prior-document recital, book. Stop rule: if the recital is absent, the big walk builds an encumbrance index only, and chain edges then require the document text. Decide that before scaling.

**3. Gazetteer.** Official SRO codes, not `1..315`. LGD village codes. Which villages sit under which SRO, and when that changed. A deed keeps the SRO at registration time. A query for "this village today" must fan out across every historical SRO for that village.

**4. One SRO, one year.** Discover, parse, resolve village, link to parcel. Measure four rates against the judgment set: schedule parse, village resolution, parcel join, false join on survey number alone. Set the pass bar before looking at the rates. Only then backfill that SRO, then the district, then the state.

## Discovery, not a binary search

Shard by `(SRO, year)`. State machine: `probing → backfilling → caught_up → incremental`.

- Probe forward from the last hit. One empty id is a hole, not a stop. End the year only after a long run of consecutive misses (use 32).
- Retry an empty id once later, then mark it a permanent gap. Transient failures stay in the queue.
- Reconcile against Vector 3. If the published count is `C`, hits `H` and confirmed gaps `G`, then `H + G` should equal `C`. Short means missed ids. Long means duplicates or the wrong year bucket.
- Incremental: each night, continue from the high-water mark with the same miss rule. Do not rescan history.
- Checkpoint every id. Stages are separate: discover, parse, resolve, link, recital. A parser change reprocesses stored payloads and does not refetch.

Parallelize by SRO. The year-shard is the checkpoint. A full refetch of about 315 offices × roughly 5,000 instruments × 15 years is tens of millions of rows and on the order of 50 GB of raw metadata. Disk is not the constraint. Parse quality is.

## Identity

Store the raw schedule forever beside the parse, so the parser can be rerun.

| Object | Key |
|---|---|
| Document | `SRO + book + year + number` |
| Parcel version | `LGD village + regime (old, resurvey, or digital) + block + survey + subdiv + extent + from/to` |
| Alias | old survey ↔ resurvey ↔ ULPIN ↔ thandaper, with source and support count |
| Link | document ↔ parcel version, with match method and score |

Match ladder, first hit wins:

1. LGD village + resurvey block + survey + subdiv.
2. Alias learned from instruments that cite both old and new numbers, or from an Ente Bhoomi correlation. Higher support wins.
3. Same survey, extent is a subset, boundary tokens overlap.
4. Reject a bare survey-number match across villages or blocks.

Village resolution uses the SRO jurisdiction first, then the name. Duplicate village names are normal.

Mine the crosswalk from the corpus itself: any schedule that states both numbers becomes an alias row. Vector 2 overrides that row when it has the correlation.

## Graph

Edges, and only these: `recites`, `conveys`, `mortgages`, `releases`, `splits`, `merges`, `mutates`.

- Sale, gift, settlement, partition and assignment are the spine.
- A mortgage is a side edge, open until a release names that document.
- A rectification cites the original and is not a second conveyance.
- One document may touch many parcels. A split creates a new parcel version; it is not another row on the parent.
- Roots are documents whose prior id is outside the corpus. That is a gap, not a null owner.

## What each vector is for

| Vector | Role | Not for |
|---|---|---|
| 1. Document details | Historical event log. Backfill once per SRO-year | Chain of title, unless the recital is in the payload |
| 2. Ente Bhoomi / cadastral features | Parcel dimension and ULPIN where resurvey is finished. Prefer a published shapefile or the feature the map already shows for a parcel | Statewide history, unsurveyed villages |
| 3. Monthly figures | Checksum and freshness cursor | Discovering ids, unless the table actually prints document numbers |
| 4. Judgments and auction notices | Labels, parser training, recital patterns, pilot scoring | Coverage |

## Query

Input is any one of survey, thandaper, ULPIN, or a document number. Output is the set of linked documents in time, the edge list, and a completeness flag:

- `index-complete`: discovery reconciled to the published count
- `title-complete`: every spine recital resolves

Pre-1980 documents and unresolved aliases stay on the gap list.

## Still out of scope

Login, captcha, payment, and block evasion. This plan starts at a known `(SRO, year, number)` that already returns metadata. Party-name entity resolution is v2. It is too noisy in Kerala (initials, house names, father's name) to use as a chain.
