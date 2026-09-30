# Plan

> Plans are temporary. Delete each item once it is implemented, and delete this file when it is empty.
> Finished work belongs in git history, not here.

Remaining work after the FT / streamlining pass. Ordered by impact.

## Tests

1. **UI tests reference removed elements.** `tests/ui/test_ui_playwright.py`, `test_contextual_chips_and_hud.py`, `test_cadastral_map_tools.py` and `test_bilingual_workflow_ui.py` look up IDs that no longer exist (`btn-undo`, `btn-hud-export`, `chip-sample-deed`, `legal-disclaimer`, `btn-pdf-export`, `step-nav-label`, `badge-kerala`).
   → Update them to the new flow. Also replace the hardcoded `/ms-playwright/chromium-1234/...` browser path, and have the suite start the web UI itself instead of expecting one on :8081.
2. **Eval dataset still rewards disclaimers.** About 10 `reference` answers in `tests/eval/datasets/basic-dataset.json` mention advocates or disclaimers, which the judge's keyword overlap scores.
   → Rewrite the references to state findings only.
3. **Live checks not yet done**: agent replies with real Gemini credentials (Markdown only, no LaTeX, no disclaimers), and satellite tiles on a normal network.

## Copy

4. **README still preaches** (`README.md` lines ~110–117: "NOT a guarantee of title…", "consult a licensed Kerala advocate before advancing money!").
   → Rewrite it in line with the no-preaching rule in `AGENTS.md`.

## UI

5. **Mixed type roles.** HUD labels are serif caps and values sans, buttons mix weights, and there are about 9 font sizes.
   → Define a scale (12 / 14 / 16 / 20 / 28). Serif for headings and big numbers (extent, score); sans for labels, buttons and body.
6. **Glyph accessibility.** ●▲■ have no text equivalent for screen readers (the verdict box already marks them `aria-hidden`).
   → Add `<span class="sr-only">Danger:</span>` and similar labels next to each status glyph.
7. **Chat drop area stays on screen after a scan** and can cover the start of the reply.
   → Collapse it automatically once a document has been scanned or a message sent.

## Structure

8. **`index.html` is about 6.5k lines** with inline `style=""` everywhere, and `ft_theme.css` overrides it with `!important`.
   → Move the inline CSS into `ft_theme.css` as classes and drop the `!important`s. Then split the JS into `static/js/*.js` modules (i18n, map, chat, workflow).
9. **i18n strings live in one giant object inside the HTML.**
   → Move them to `static/i18n/en.json` and `ml.json`, and add a check that both files have the same keys.
