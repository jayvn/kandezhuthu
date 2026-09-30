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
    → Feed them from real `MunnadharamAuditor` / EC audit results so a buyer's own chain can be shown and exported.
21. **No live source for Data Bank, BhuNaksha parcels, fair values or resurvey status.** The app reports these as not on file.
    → Add real sources where one exists (for example a fair-value import) using the same JSON shape as `tests/fixtures/`.

## Structure

17. **Inline styles fight the theme.** CSS and JS now live in `static/app.css` and `static/js/*.js`, but `index.html` and the JS templates still carry ~200 inline `style=""` attributes, and `ft_theme.css` overrides them with `!important`.
    → Move them into classes as each area is touched, then drop the `!important`s.
