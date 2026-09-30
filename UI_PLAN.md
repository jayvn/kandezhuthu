# UI Improvement Plan

Status: ✓ = done. Remaining work is items 13, 15 and P3.

Based on the demo and UI-test screenshots (desktop 1440×900, phone 390×844) after the FT glyph pass.
Ordered by impact. Each item names the problem, then the change.

## P0: Broken or misleading

1. ✓ **Agent markdown renders raw.** Chat shows literal `####`, `---`, inline `* ` bullets and LaTeX (`$\leftarrow$`).
   → Use a real markdown renderer (e.g. marked + DOMPurify from cdnjs), and tell the agent not to emit LaTeX.
2. ✓ **Horizontal overflow on phones.** The page is wider than the viewport (white strip on the right), and the header, stepper and "Online Mode" are clipped.
   → Wrap the header onto two rows below 480px. Stepper shows only the current step name (`2/4 Prior Lineage`). Make chip rows and toolbars `overflow-x: auto` with a fade edge.
3. ✓ **Chat bubble clips on the left** ("andezhuthu AI" cut off in the audit result).
   → Fix the bubble container width and padding. The bubble should never be wider than the column.
4. ✓ **The HUD covers the map.** On desktop the floating HUD hides about 40% of the map, including the plot and its popup. On phone it covers the whole map.
   → Dock the HUD as a collapsible bottom strip (one line: extent · road · MSL · risk) that expands on tap. Start it collapsed on phone.
5. ✓ **Map is blank when Leaflet or the tiles fail to load** (unpkg blocked means `L is not defined` and an empty panel).
   → Self-host Leaflet in `/static`, and show a "Map unavailable, check connection" state instead of white space.
6. ~~Clear verdicts need an explicit caveat.~~ Dropped: the app states what was checked and found, with no disclaimers (see AGENTS.md).

## P1: Too much chrome

7. ✓ **About 200px of controls before any content**: brand, language, 3 view buttons, Online Mode, Guardrail badge, stepper, 2 header buttons, a step sub-header with Prev/Next, then a chip row.
   → Merge the stepper and step sub-header into one row. Move Prev/Next to the bottom of the step. Drop the "Kerala Real Estate Guardrail" badge, and show "Online Mode" only when offline.
8. ✓ **Duplicate actions.** Export PDF appears 3 times (header, HUD, action row), plus Auto-Demarcate ×2, Undo ×2, and sample deeds both as chips and as cards.
   → One home per action: Export in the step 4 action row, map tools in the map toolbar only, samples as cards only.
9. ✓ **The disclaimer footer uses about 80px on phones permanently.**
   → Keep it as one line with a "Read more" link on phones. Keep the full text in the PDF and in verdict boxes.
10. ✓ **The chat input placeholder wraps and gets clipped** ("scanned deed..." cut).
    → Use a shorter placeholder: "Paste a deed clause or ask a question".

## P2: FT consistency

11. ✓ **Leftover non-FT palette**: green dashed audit card, mint WhatsApp card, blue lineage box, purple boundaries box, Tailwind slate and blue in inline styles.
    → Use paper, card, claret, navy and teal only. Severity colour appears only on the ●▲■ glyph and a 3px left rule.
12. ✓ **Rounded pills and soft shadows.** FT uses square corners, hairline rules and no shadows.
    → Set border-radius to 0–2px on cards and buttons, replace box shadows with `1px solid var(--ft-border)`, and use flat filled claret for primary buttons only.
13. **Mixed type roles.** HUD labels are serif caps and values sans, buttons mix weights, and there are about 9 font sizes.
    → Define a scale (12 / 14 / 16 / 20 / 28). Serif for headings and big numbers (extent, score); sans for labels, buttons and body.
14. ✓ **Finding cards show broken snippets** ("'nts Classification: Nilam Boundaries: - East:'").
    → Expand the snippet to word or clause boundaries in `single_deed_scanner._find_first_pattern`, and highlight the matched phrase.
15. **Glyph accessibility.** ●▲■ have no text equivalent for screen readers.
    → Wrap them as `<span aria-hidden="true">■</span><span class="sr-only">Danger:</span>`.

## P3: Structural (makes the rest cheap)

16. **`index.html` is 6.6k lines** with inline `style=""` everywhere, and `ft_theme.css` overrides it with `!important`.
    → Move the inline CSS into `ft_theme.css` as classes, drop the `!important`s, then split the JS into `static/js/*.js` modules (i18n, map, chat, workflow).
17. **i18n strings live in one giant object inside the HTML.**
    → Move them to `static/i18n/en.json` and `ml.json`.
18. ✓ **Demo-only UI ships to users** (checked: the "SCENE" banner is injected by `scripts/record_demo.py` only; sample cards now just say "Sample") ("SCENE 2/10" banner, test cards labelled "3 TRAPS HIDDEN").
    → Show these only with `?demo=1`.
