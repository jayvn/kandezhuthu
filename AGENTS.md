# Kandezhuthu AI (കണ്ടെഴുത്ത് - ആധാരംനോക്കി) · Agent Guide

## Project Overview

**Kandezhuthu AI** is a specialized Kerala property legal audit assistant built with the Google Agent Development Kit (ADK) and deployed via `agents-cli`. Its primary mission is to protect home buyers and Non-Resident Indians (NRIs) from paying earnest money/advances on legally defective land or falling victim to title traps in Kerala real estate transactions.

### Core Capabilities
1. **Single-Deed Red-Flag Scanning**: Analyzes deed recitals and property schedules for 4 fatal statutory traps:
   - Buried easements/pathways (*Vazhi avakasham* / *Nadappu vazhi*)
   - 2008 Paddy Land / Wetland risk (*Nilam* vs *Purayidam*)
   - Minor's share sold without District Court sanction order
   - Senior citizen maintenance or conditional life-interest covenants
2. **30-Year Prior Title Lineage Audit (*Munnadharam*)**: Evaluates chronological chains of title deeds (`DeedNode`) for gaps in continuity, extent inflation (*Nemo dat quod non habet*), omitted legal heirs across religious succession laws, and unauthorized minor sales.
3. **SRO Encumbrance Certificate (EC) Triangulation**: Cross-references seller-provided title deeds with registered EC entries to unearth undisclosed mortgages, court attachments, or partial alienations.
4. **Bilingual Seller Inquiry Drafting**: Generates culturally polite, native Malayalam WhatsApp inquiry drafts for buyers to ask sellers before advancing funds.
5. **Ethical Non-AI Guardrails**: Strictly isolates document analysis from physical on-ground realities (boundary stones / *Survey Kallu*, road motorability, flooding history, oral covenants).

---

## Architecture & Codebase Map

Kandezhuthu follows a **Neuro-Symbolic architecture**:
- **Deterministic Core (`app/domain/`)**: Handles mathematical extent arithmetic, chronological chaining, statutory thresholds, and regex pattern matching without LLM hallucination.
- **Generative Agent (`app/agent.py`)**: Uses `gemini-3.8-flash` for Malayalam/English legal language understanding, document recital extraction, conversational triage, and disclaimer enforcement.

```
kandezhuthu/
├── app/
│   ├── agent.py                 # ADK Agent definition, root prompt, and exposed tool interfaces
│   ├── fast_api_app.py          # FastAPI backend server with A2A Protocol (/a2a/kandezhuthu)
│   ├── app_utils/               # A2A routing, sessions, and GCP services
│   ├── db/                      # SQLite WAL connection, schema, knowledge repository & seed data
│   └── domain/
│       ├── models.py            # Pydantic schemas (DeedNode, ECRecord, RiskFlag, CleanTitleScorecard, DeedSanityResult)
│       ├── deed_ocr.py          # Multimodal deed vision extraction using Gemini Flash
│       ├── single_deed_scanner.py # SingleDeedScanner engine: 4 trap categories, scoring, Malayalam WhatsApp generator
│       └── auditor.py           # MunnadharamAuditor engine: multi-decade title chain continuity & EC cross-validation
├── frontend/
│   ├── main.py                  # Full-stack FastAPI server with Web UI, OCR and upload endpoints
│   └── static/
│       └── index.html           # Dual-pane UI (Chat, Drag-and-drop OCR, Satellite Map)
├── data/
│   ├── kandezhuthu.db           # Embedded SQLite database (auto-seeded)
│   ├── knowledge/               # Statutory diligence guides (KPBR, court rulings, paddy land act)
│   └── sample_deeds/            # Synthetic Kerala title deed PDFs
├── tests/
│   ├── unit/                    # Fast deterministic unit tests (scanner & auditor)
│   ├── integration/             # Live agent & FastAPI e2e tests
│   ├── ui/                      # Playwright UI & browser workflow tests
│   └── eval/                    # Response quality & eval datasets
├── AGENTS.md                    # AI assistant guidance (this file; CLAUDE.md imports it)
└── pyproject.toml               # Project dependencies and configurations managed via uv
```

---

## Key Legal Statutes & Kerala Real Estate Concepts

When enhancing or modifying reasoning logic, adhere to these governing laws:

| Statute / Precedent | Scope & Application in Agent |
|---|---|
| **Kerala Conservation of Paddy Land and Wetland Act, 2008** | Section 27A, Form 5 (Data Bank exclusion), Form 6 (Revenue land conversion). Flags *Nilam* / *Nanja* / *Punja* vs *Purayidam*. |
| **Indian Easements Act, 1882** | Sections 13 & 15. Pathway (*Vazhi avakasham* / *Nadappu vazhi*) and well access rights that run with the land. |
| **Hindu Minority and Guardianship Act, 1956** | Section 8(2). Mandatory prior sanction from the District Court before disposing of a minor's immovable property. |
| **Maintenance and Welfare of Parents & Senior Citizens Act, 2007** | Section 23. Conditional gift/settlement deeds subject to maintenance can be voided by the Maintenance Tribunal (RDO). |
| **Christian Succession (*Mary Roy v. State of Kerala, 1986*)** | Indian Succession Act, 1925. Female heirs have equal rights in intestate parental property; prevents exclusion in partition deeds. |
| **Hindu Succession (Amendment) Act, 2005** | Daughters are coparceners by birth (*Vineeta Sharma v. Rakesh Sharma*). |
| **Transfer of Property Act, 1882** | *Nemo dat quod non habet* — sellers cannot convey more extent (cents) than acquired in the parent deed. |
| **Indian Registration Act, 1908** | Sections 17 & 51. Encumbrance Certificate (EC) registration cross-validation. |

---

## Development Commands

Always run Python commands using `uv run` inside `kandezhuthu/`:

| Command | Purpose |
|---|---|
| `agents-cli playground` | Launch local ADK dev UI with auto-reload |
| `agents-cli lint` | Run code quality checks (ruff, ty, codespell) |
| `uv run python -m app.fast_api_app` | Run local FastAPI server with A2A protocol endpoint |
| `agents-cli deploy` | Deploy to Agent Runtime on Google Cloud (requires explicit user confirmation) |

---

## Parallel Agent Collaboration & Git Worktree Workflow

When multiple agents or subagents work concurrently on Kandezhuthu AI, they MUST avoid dirtying the primary working tree or colliding on git operations. Git worktrees allow multiple isolated checkouts linked to the same repository.

### Guidelines for Parallel Worktrees
1. **Isolated Workspaces**: Never execute concurrent edits or run write-heavy commands on the same working tree branch simultaneously. Use a separate worktree for each agent task or subagent session.
2. **Standard Worktree Directory**: Place worktrees under `.worktrees/` at the repository root (`/config/Desktop/BuildWithGemini/.worktrees/<agent-task-name>`), which is gitignored.
3. **Subagent Workspace Mode**: When invoking subagents via `invoke_subagent`, set `Workspace: 'share'` or `Workspace: 'branch'` so the subagent gets an isolated directory while sharing the underlying object store.

### Standard Worktree Lifecycle

```bash
# 1. Create a dedicated worktree and feature branch from root
git worktree add -b feat/<agent-task-name> .worktrees/<agent-task-name> HEAD

# 2. Work inside the worktree's kandezhuthu directory
cd .worktrees/<agent-task-name>/kandezhuthu
# Run UV or agent commands here in isolation:
uv run ...

# 3. Commit frequently inside the worktree (following atomic commit rules)
git add <target-files>
git commit -m "feat(<scope>): <description of progress>"

# 4. Integrate back to the main branch
cd /config/Desktop/BuildWithGemini
git checkout <target-branch>
git merge --no-ff feat/<agent-task-name>

# 5. Clean up the worktree when finished
git worktree remove .worktrees/<agent-task-name>
git worktree prune
git branch -d feat/<agent-task-name>
```

### Safety Rules for Agents
- **No Duplicate Branch Checkouts**: Git will error if two worktrees attempt to check out the same branch. Always create a unique branch per worktree (e.g., `agent/<name>-<topic>`).
- **Never Touch Another Agent's Worktree**: Check `git worktree list` before creating or removing worktrees. Never delete a worktree that is currently active or owned by another agent/subagent.
- **Keep Temporary Files Isolated**: Keep all scratch files and local test outputs within the designated worktree.

---

## Operational Guidelines for Coding Agents

- **Parallel Worktree Discipline**: For concurrent or multi-step agent tasks, always spawn a dedicated git worktree in `.worktrees/` or use `Workspace: 'share'`/`'branch'` to prevent index lock contention and file overwrite conflicts.
- **DO NOT RUN TESTS WITHOUT ASKING**: Do not run unit tests or integration tests unless explicitly requested by the user.
- **Always Multi-Commit on the Way**: Always make frequent, small atomic git commits along the way as discrete steps and milestones are completed, rather than waiting to create a single large commit at the very end.
- **Code preservation**: Only modify code directly targeted by the user's request. Preserve all surrounding code, config values (e.g., `model`), comments, and formatting.
- **NEVER change the model**: Keep `MODEL = "gemini-3.8-flash"` in `app/agent.py` unless explicitly directed by the user.
- **Bilingual Integrity**: Maintain accurate Malayalam legal terminology (e.g., ആധാരം, മുന്നാധാരം, തീറാധാരം, ഭാഗപത്രം, ഒഴിവുമുറി, നിലം, പുരയിടം, നടപ്പുവഴി, സർവേ കല്ല്) and ensure Malayalam WhatsApp inquiry messages remain culturally polite and natural.
- **Non-Negotiable Ethical Guardrails**:
  - Never state or guarantee that a title is "100% clear or clean".
  - Always retain the explicit list of what AI cannot verify on paper:
    - Physical boundary stones (*Survey Kallu*) and neighbor encroachment.
    - Physical motorability of access roads on the ground.
    - Oral family agreements (*Vaymozhi udanpadi*) and unfiled court caveats.
    - Ground topography, waterlogging, flooding history, or high-tension power lines.
  - Always advise the user to complete physical inspection and consult a licensed Kerala High Court or District advocate before parting with any advance money.
