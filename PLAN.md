# Plan

> Plans are temporary. Delete each item once it is implemented, and delete this file when it is empty.
> Finished work belongs in git history, not here.

Remaining work, ordered by impact within each section.

## UX

The buyer's question is: *can I pay the advance, and what do I still need?* Every screen should answer that. Today the first screen shows about 30 controls (three rows of navigation, three ways to start, eight map tools, a five-box plot panel) before the user has done anything.

1. **Too many ways in.** The chat pane has the drop area with three cards, a welcome bubble with three questions and a chip row. All of them do the same job: start a check.
   → One start card: "Drop your deed or EC" with Upload, plus one "Try a sample" link. Move the three questions under the input as quiet suggestions, and hide them after the first message.
2. **Three rows of navigation.** Header (language, Chat / Split / Map), the 1–4 stepper with Back / Next, then a per-step chip row. The stepper only switches which chips are shown, and its steps aren't real stages of the buyer's work.
   → Header: brand and language only. Drop Back / Next and the chip row. Keep the four steps as a slim progress line that shows what has been checked (✓) and what is still missing, and is clickable.
3. **The map toolbar overflows** (eight buttons, the last cut off) and asks the user to pick tools before they have a plot.
   → The map starts with one thing: search or tap to pin your plot. Show the other tools only after a pin: Measure road, Draw plot, Data Bank. Move Outline from extent into Draw plot, and the layer picker and region presets into a small ⋯ menu.
4. **The plot panel covers the map** and shows empty boxes before there is a plot.
   → Show one line (extent · road · elevation), which expands on tap. Keep only the values that were actually measured or fetched.
5. **The deed result card is busy.** It has a score pill, a model badge ("Gemini 3.8 Flash Vision"), the document type, the verdict, a four-box grid, three action buttons, a PDF banner and a hint line.
   → Order: verdict and findings first, then the facts (survey no, village, extent, classification), then one row of actions (Ask seller, Check prior deeds, PDF). Drop the model badge and the hint line.
6. **The seller message is scattered.** Every card has its own WhatsApp draft.
   → One "Ask the seller" message that collects the questions from every check so far, reachable from the progress line.
7. **Mobile:** the drop area fills the whole first screen, and the map is a separate mode.
   → On phones, stack the result first and the map below it as a collapsible section. Collapse the drop area once a document is scanned or a message sent.
8. **Mixed type roles.** HUD labels are serif caps and values sans, buttons mix weights, and there are about 9 font sizes.
   → Define a scale (12 / 14 / 16 / 20 / 28). Serif for headings and big numbers (extent, score); sans for labels, buttons and body.
9. **Glyph accessibility.** ●▲■ have no text equivalent for screen readers (the verdict box already marks them `aria-hidden`).
   → Add `<span class="sr-only">Danger:</span>` and similar labels next to each status glyph.

## Correctness

10. **Wrong locality without a Maps key.** The elevation fallback names the nearest landmark it knows, so a Kaloor pin becomes "Kakkanad" in the flood WhatsApp text.
    → Without geocoding, say "the plot at <lat, lng>" rather than naming a place.
11. **EC parser merges entries.** Several entries can end up in one block, and a later "release" line then hides an earlier mortgage.
    → Split on entry and document-number boundaries, then match releases to the document they discharge.
12. **`exportPlotDossier()` invents a score and verdict.** Nothing calls it.
    → Delete it.

## Tests

13. **UI tests reference removed elements.** `tests/ui/test_ui_playwright.py`, `test_contextual_chips_and_hud.py`, `test_cadastral_map_tools.py` and `test_bilingual_workflow_ui.py` look up IDs that no longer exist (`btn-undo`, `btn-hud-export`, `chip-sample-deed`, `legal-disclaimer`, `btn-pdf-export`, `step-nav-label`, `badge-kerala`).
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
