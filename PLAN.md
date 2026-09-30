# Plan

> Plans are temporary. Delete each item once it is implemented, and delete this file when it is empty.
> Finished work belongs in git history, not here.

Remaining work, ordered by impact within each section.

## Tests

13. **UI tests reference removed elements.** `tests/ui/test_ui_playwright.py`, `test_contextual_chips_and_hud.py`, `test_cadastral_map_tools.py` and `test_bilingual_workflow_ui.py` look up IDs that no longer exist (`btn-undo`, `btn-hud-export`, `chip-sample-deed`, `legal-disclaimer`, `btn-pdf-export`, `step-nav-label`, `badge-kerala`, and since the UX pass `btn-next-step`, `chips-container`, `layman-card`, `tool-pin`, `btn-bhunaksha`, `exportPlotDossier`).
    → Update them to the new flow. Also replace the hardcoded `/ms-playwright/chromium-1234/...` browser path, and have the suite start the web UI itself instead of expecting one on :8081.
14. **Eval dataset still rewards disclaimers.** About 10 `reference` answers in `tests/eval/datasets/basic-dataset.json` mention advocates or disclaimers, which the judge's keyword overlap scores.
    → Rewrite the references to state findings only.
15. **Live checks not yet done**: agent replies with real Gemini credentials (Markdown only, no LaTeX, no disclaimers), and satellite tiles on a normal network.

## Copy

16. **README still preaches** (`README.md` lines ~110–117: "NOT a guarantee of title…", "consult a licensed Kerala advocate before advancing money!").
    → Rewrite it in line with the no-preaching rule in `AGENTS.md`.

## Structure

17. **Inline styles fight the theme.** CSS and JS now live in `static/app.css` and `static/js/*.js`, but `index.html` and the JS templates still carry ~200 inline `style=""` attributes, and `ft_theme.css` overrides them with `!important`.
    → Move them into classes as each area is touched, then drop the `!important`s.
18. **i18n strings live in one giant object inside the HTML.**
    → Move them to `static/i18n/en.json` and `ml.json`, and add a check that both files have the same keys.
