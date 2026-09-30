# Plan

> Plans are temporary. Delete each item once it is implemented, and delete this file when it is empty.
> Finished work belongs in git history, not here.

Remaining work, ordered by impact within each section.

## Tests

13. **UI tests reference removed elements.** `tests/ui/test_ui_playwright.py`, `test_contextual_chips_and_hud.py`, `test_cadastral_map_tools.py` and `test_bilingual_workflow_ui.py` look up IDs that no longer exist (`btn-undo`, `btn-hud-export`, `chip-sample-deed`, `legal-disclaimer`, `btn-pdf-export`, `step-nav-label`, `badge-kerala`, and since the UX pass `btn-next-step`, `chips-container`, `layman-card`, `tool-pin`, `btn-bhunaksha`, `exportPlotDossier`).
    → Update them to the new flow. Also replace the hardcoded `/ms-playwright/chromium-1234/...` browser path, and have the suite start the web UI itself instead of expecting one on :8081.
15. **Live checks not yet done**: agent replies with real Gemini credentials (Markdown only, no LaTeX, no disclaimers), and satellite tiles on a normal network.

## Structure

17. **Inline styles fight the theme.** CSS and JS now live in `static/app.css` and `static/js/*.js`, but `index.html` and the JS templates still carry ~200 inline `style=""` attributes, and `ft_theme.css` overrides them with `!important`.
    → Move them into classes as each area is touched, then drop the `!important`s.
18. **i18n strings are one ~350-line object in `static/js/i18n.js`, and nothing checks that English and Malayalam have the same keys.**
    → Move them to `static/i18n/en.json` and `ml.json`, and add a check that both files have the same keys.
