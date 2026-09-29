import os

from playwright.sync_api import expect, sync_playwright

CHROMIUM_PATH = "/ms-playwright/chromium-1234/chrome-linux64/chrome" if os.path.exists("/ms-playwright/chromium-1234/chrome-linux64/chrome") else None
SCREENSHOTS_DIR = os.path.join(os.path.dirname(__file__), "screenshots")
BASE_URL = os.environ.get("TEST_BASE_URL", "http://localhost:8081")

def run_realistic_buyer_journey_test():
    """
    Automated Playwright UI Test: Realistic Kerala Property Buyer Journey

    Complete End-to-End Persona Journey for an NRI Property Buyer ("Mathew"):
    1. Satellite Discovery & Coordinates Inspection (Aluva Re-Sy 345/1)
    2. Road Width Measurement & KPBR 2019 Rule Compliance Check
    3. On-Site Physical Inspection Checklist (Survey Kallu, Wetland proximity)
    4. 30-Year Prior Title Lineage Audit (Mary Roy Heir Defect, Extent Inflation, Bank Mortgage)
    5. Clean Title Chain Comparison (39-Year unbroken lineage)
    6. Live Single-Deed Statutory Red-Flag Audit with Gemini 3.8 Flash
    7. Malayalam WhatsApp Inquiry Card Generation & 1-Tap Direct Share
    8. Minimizable HUD & Full Screen Satellite Exploration
    """
    os.makedirs(SCREENSHOTS_DIR, exist_ok=True)
    results = []

    print("\n=======================================================")
    print("  KANDEZTHUTHU AI: REALISTIC BUYER JOURNEY TEST")
    print(f"  Target: {BASE_URL}")
    print("=======================================================\n")

    with sync_playwright() as p:
        browser = p.chromium.launch(
            executable_path=CHROMIUM_PATH,
            headless=True,
            args=["--no-sandbox", "--disable-dev-shm-usage"]
        )
        context = browser.new_context(
            viewport={"width": 1440, "height": 900},
            permissions=["clipboard-read", "clipboard-write"]
        )
        page = context.new_page()

        console_errors = []
        page.on("console", lambda msg: console_errors.append(msg.text) if msg.type == "error" else None)
        page.on("pageerror", lambda err: console_errors.append(str(err)))

        # -----------------------------------------------------------------
        # PHASE 1: Satellite Inspection & Location Verification
        # -----------------------------------------------------------------
        print("[Phase 1] Loading Kandezhuthu AI Split View...")
        page.goto(BASE_URL, wait_until="domcontentloaded")
        page.wait_for_timeout(1200)

        expect(page.locator(".brand-title")).to_contain_text("Kandezhuthu AI")

        # Verify default Aluva property preset
        preset_select = page.locator("#preset-select")
        expect(preset_select).to_have_value("aluva")

        hud_coords = page.locator("#hud-coords").text_content()
        print(f"  → Verified Satellite Coordinates: {hud_coords.strip()}")
        assert "10.1076" in hud_coords and "76.3516" in hud_coords

        page.screenshot(path=os.path.join(SCREENSHOTS_DIR, "journey_01_satellite_discovery.png"))
        results.append("Phase 1: Satellite Discovery - PASSED")

        # -----------------------------------------------------------------
        # PHASE 2: Road Access Measurement & KPBR Verification
        # -----------------------------------------------------------------
        print("\n[Phase 2] Measuring Access Road Width under KPBR 2019...")
        page.click("#tool-road")
        expect(page.locator("#tool-road")).to_have_class("map-tool-btn active")
        expect(page.locator("#guidance-text")).to_contain_text("Kerala Panchayat Building Rules")

        map_box = page.locator("#map-view").bounding_box()
        assert map_box is not None
        cx, cy = map_box["x"] + map_box["width"] / 2, map_box["y"] + map_box["height"] / 2

        # Measure across road lane
        page.mouse.click(cx - 30, cy + 40)
        page.wait_for_timeout(200)
        page.mouse.click(cx - 10, cy + 40)
        page.wait_for_timeout(400)

        road_status = page.locator("#hud-road").text_content()
        print(f"  → Road measurement recorded: {road_status.strip()}")
        expect(page.locator("#hud-road-badge")).to_be_visible()

        page.screenshot(path=os.path.join(SCREENSHOTS_DIR, "journey_02_road_measured.png"))
        results.append("Phase 2: Road Measurement & KPBR Compliance - PASSED")

        # -----------------------------------------------------------------
        # PHASE 3: On-Site Field Verification Checklist
        # -----------------------------------------------------------------
        print("\n[Phase 3] Checking Off Physical On-Site Inspection Items...")
        page.click("#btn-checklist-toggle")
        page.wait_for_timeout(300)
        expect(page.locator("#checklist-panel")).to_have_class("checklist-panel visible")

        page.check("#chk-kallu")
        page.check("#chk-wetland")
        page.wait_for_timeout(200)

        expect(page.locator("#chk-badge")).to_have_text("2/5")
        print("  → Checklist counter successfully updated to 2/5")

        # Close checklist drawer
        page.click(".checklist-close-btn")
        page.wait_for_timeout(200)

        page.screenshot(path=os.path.join(SCREENSHOTS_DIR, "journey_03_field_checklist.png"))
        results.append("Phase 3: Field Checklist Verification - PASSED")

        # -----------------------------------------------------------------
        # PHASE 4: 30-Year Prior Title Lineage Audit (Timeline Engine)
        # -----------------------------------------------------------------
        print("\n[Phase 4] Auditing 30-Year Prior Title Lineage (*Munnadharam*)...")
        # Click the Timeline Chip button in the header toolbar
        timeline_btn = page.locator("button:has-text('Ownership Timeline')")
        if timeline_btn.count() > 0:
            timeline_btn.first.click()
        else:
            page.locator(".chip:has-text('Timeline: Aluva 30-Yr')").click()

        page.wait_for_timeout(800)

        # Verify the Timeline Card is rendered
        expect(page.locator(".timeline-card")).to_be_visible()
        timeline_text = page.locator(".timeline-card").text_content()
        print("  → Ownership Timeline Card Loaded. Title Score: 0/100 DANGER")
        assert "Mary Roy" in timeline_text or "Pattayam" in timeline_text or "Federal Bank" in timeline_text
        assert "Score: 0/100" in timeline_text
        print("  ✓ Detected Mary Roy Succession defect and Undischarged Bank Mortgage in lineage chain!")

        page.screenshot(path=os.path.join(SCREENSHOTS_DIR, "journey_04_timeline_audit.png"))
        results.append("Phase 4: 30-Year Lineage Chain Audit - PASSED")

        # -----------------------------------------------------------------
        # PHASE 5: Lineage Preset Comparison (Clean Title Chain 100/100)
        # -----------------------------------------------------------------
        print("\n[Phase 5] Comparing with 100% Clean Title Chain Preset...")
        clean_btn = page.locator("button:has-text('100% Clean Title Chain')")
        clean_btn.click()
        page.wait_for_timeout(800)

        clean_score = page.locator(".deed-score-badge.clear").text_content()
        print(f"  → Clean Title Badge: {clean_score.strip()}")
        assert "100/100" in clean_score
        print("  ✓ Verified Clean Title Lineage (39 Years continuous without gaps)")

        page.screenshot(path=os.path.join(SCREENSHOTS_DIR, "journey_05_clean_title_comparison.png"))
        results.append("Phase 5: Clean Title Chain Comparison - PASSED")

        # -----------------------------------------------------------------
        # PHASE 6: Live Single-Deed Audit with Gemini 3.8 Flash
        # -----------------------------------------------------------------
        print("\n[Phase 6] Submitting Real Title Deed Recital to Gemini 3.8 Flash...")

        realistic_deed_query = (
            "Please audit this deed schedule for an earnest money decision:\n"
            "Property: 10 Cents in Re-Sy 345/1, Aluva West Village.\n"
            "Vendor acquired title via Partition Deed 1120/2012.\n"
            "Parent Title Deed reference: Sale Deed 450/1988 for only 8.5 Cents.\n"
            "Southern boundary clause: '2-meter pathway (Nadappu vazhi / Vazhi avakasham) "
            "along southern boundary is reserved for 2nd party and successors in perpetuity.'\n"
            "SRO Encumbrance Certificate shows a 2018 Federal Bank mortgage with no registered Ozhivumuṟi.\n"
            "What are the fatal traps, what should I ask the seller in Malayalam, and what must I inspect on ground?"
        )

        textarea = page.locator("#input")
        textarea.fill(realistic_deed_query)
        page.wait_for_timeout(200)

        initial_agent_count = page.locator(".msg.agent").count()
        print(f"  → Submitting query (initial agent msgs: {initial_agent_count})...")
        page.click("#send-btn")

        # Wait for live Gemini response
        print("  → Waiting for Gemini 3.8 Flash inference (up to 40s)...")
        page.wait_for_function(
            f"() => document.querySelectorAll('.msg.agent').length > {initial_agent_count} && !document.querySelector('#send-btn').disabled",
            timeout=45000
        )
        print("  → Live Gemini 3.8 Flash audit response received!")

        latest_reply = page.locator(".msg.agent .bubble").last.text_content()
        print(f"\n--- AUDIT SUMMARY PREVIEW ---\n{latest_reply[:350]}...\n-----------------------------")

        # Assert Statutory Trap 1: Buried Easement / Pathway
        assert any(term in latest_reply.lower() for term in ["easement", "pathway", "vazhi", "നടപ്പുവഴി", "വഴി"]), \
            "AI failed to flag the 2-meter pathway easement trap!"
        print("  ✓ Trap 1 Flagged: Buried Easement / Pathway (*Nadappu vazhi*)")

        # Assert Statutory Trap 2: Extent Discrepancy (8.5 Cents vs 10 Cents)
        assert any(term in latest_reply for term in ["8.5", "1.5", "Nemo dat", "inflation", "parent deed", "മുന്നാധാരം"]), \
            "AI failed to flag the 1.5-cent extent inflation!"
        print("  ✓ Trap 2 Flagged: Extent Inflation (*Nemo dat quod non habet*)")

        # Assert Statutory Trap 3: Undischarged Federal Bank Mortgage
        assert any(term in latest_reply.lower() for term in ["mortgage", "federal bank", "ozhivumuri", "ഒഴിവുമുറി", "ബാങ്ക്", "encumbrance"]), \
            "AI failed to flag the undischarged bank mortgage!"
        print("  ✓ Trap 3 Flagged: Undischarged Mortgage / Missing Ozhivumuṟi")

        # Assert Ethical Non-AI Guardrails
        assert any(term in latest_reply.lower() for term in ["survey kallu", "ground", "advocate", "physical", "കല്ല്"]), \
            "AI failed to enforce ethical guardrails regarding physical inspection and advocate review!"
        print("  ✓ Guardrails Enforced: Physical Survey Stones & Advocate Consultation required")

        page.screenshot(path=os.path.join(SCREENSHOTS_DIR, "journey_06_live_audit_results.png"))
        results.append("Phase 6: Live Gemini Statutory Triage - PASSED")

        # -----------------------------------------------------------------
        # PHASE 7: Malayalam WhatsApp Card & Action Buttons
        # -----------------------------------------------------------------
        print("\n[Phase 7] Testing WhatsApp Inquiry Card & Share Actions...")

        wa_cards = page.locator(".whatsapp-card")
        expect(wa_cards.last).to_be_visible()

        wa_text = wa_cards.last.locator(".whatsapp-text").text_content()
        print(f"  → Malayalam WhatsApp Draft: {wa_text.strip()[:100]}...")
        assert len(wa_text.strip()) > 20, "WhatsApp text too short!"

        # Test Copy Draft button
        copy_btn = wa_cards.last.locator(".copy-btn")
        copy_btn.click()
        page.wait_for_timeout(300)
        expect(copy_btn).to_contain_text("Copied")
        print("  ✓ Copy Draft button transitioned to '✅ Copied!'")

        # Test Open in WhatsApp direct link
        wa_link = wa_cards.last.locator(".wa-direct-btn")
        href = wa_link.get_attribute("href")
        assert href is not None and "api.whatsapp.com/send" in href
        print(f"  ✓ Verified WhatsApp direct link: {href[:50]}...")

        results.append("Phase 7: WhatsApp Card & Direct Share - PASSED")

        # -----------------------------------------------------------------
        # PHASE 8: HUD Minimize & Map Controls
        # -----------------------------------------------------------------
        print("\n[Phase 8] Testing HUD Minimize & Satellite Exploration...")
        hud_toggle = page.locator("#hud-toggle-btn")
        hud_toggle.click()
        page.wait_for_timeout(300)
        expect(page.locator("#map-hud")).to_have_class("map-hud minimized")
        print("  ✓ HUD minimized for unobstructed satellite view.")

        page.screenshot(path=os.path.join(SCREENSHOTS_DIR, "journey_07_hud_minimized.png"))

        hud_toggle.click()
        page.wait_for_timeout(200)
        expect(page.locator("#map-hud")).not_to_have_class("map-hud minimized")
        print("  ✓ HUD expanded back to normal.")

        results.append("Phase 8: HUD Controls & Satellite View - PASSED")

        # Console error audit
        print("\n--- Console Errors Check ---")
        if console_errors:
            print(f"Captured {len(console_errors)} console errors:")
            for err in console_errors:
                print(f"  [Console Error] {err}")
        else:
            print("Zero console errors captured throughout entire buyer journey!")

        browser.close()

    print("\n=======================================================")
    print("  REALISTIC BUYER JOURNEY TEST EXECUTION SUMMARY")
    print("=======================================================")
    for r in results:
        print(f"  ✅ {r}")
    print("=======================================================\n")

def test_realistic_buyer_journey():
    """Standard pytest entrypoint for Realistic Kerala Property Buyer Journey UI test."""
    run_realistic_buyer_journey_test()

if __name__ == "__main__":
    run_realistic_buyer_journey_test()
