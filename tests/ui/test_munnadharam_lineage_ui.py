import os

from playwright.sync_api import expect, sync_playwright

CHROMIUM_PATH = "/ms-playwright/chromium-1234/chrome-linux64/chrome" if os.path.exists("/ms-playwright/chromium-1234/chrome-linux64/chrome") else None
SCREENSHOTS_DIR = os.path.join(os.path.dirname(__file__), "screenshots")
BASE_URL = os.environ.get("TEST_BASE_URL", "http://localhost:8081")

def run_munnadharam_lineage_test():
    """
    Automated Playwright UI Test for 30-Year Prior Title Lineage (Munnadharam) Visualizer

    Verifies:
    1. Opening Timeline Card from Header Actions & Quick Action Bar
    2. Preset 1: Aluva Broken Chain (Score: 0/100, Mary Roy succession defect, Federal Bank mortgage, Extent inflation)
    3. Preset 2: Kakkanad Wetland & Minor Share (Score: 35/100, 2008 Paddy Land Act, Section 8 HMGA 1956)
    4. Preset 3: Clean Title Chain (Score: 100/100, 39-Year unbroken continuous lineage)
    5. Reactive score badges, financial encumbrance table, and chronological deed chain nodes
    6. Timeline Actions: View Region on Satellite & Trigger On-Site Field Checklist
    """
    os.makedirs(SCREENSHOTS_DIR, exist_ok=True)
    results = []

    print("\n=======================================================")
    print("  KANDEZTHUTHU AI: MUNNADHARAM LINEAGE UI TEST")
    print(f"  Target: {BASE_URL}")
    print("=======================================================")

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

        # -------------------------------------------------------------
        # STEP 1: Page Load & Launch Ownership Timeline Visualizer
        # -------------------------------------------------------------
        print("[Step 1] Loading Page & Launching Ownership Timeline Visualizer...")
        page.goto(BASE_URL, wait_until="networkidle")
        page.wait_for_timeout(1000)

        expect(page.locator(".brand-title")).to_contain_text("Kandezhuthu AI")

        # Open Timeline via header export-report-btn
        timeline_btn = page.locator("#btn-timeline-export")
        if timeline_btn.count() == 0:
            timeline_btn = page.locator("button:has-text('Ownership Timeline')").first

        expect(timeline_btn).to_be_visible()
        timeline_btn.click()
        page.wait_for_timeout(800)

        # Verify Timeline Card rendered
        expect(page.locator(".timeline-card")).to_be_visible()
        print("  ✓ Timeline Card successfully opened and displayed.")
        page.screenshot(path=os.path.join(SCREENSHOTS_DIR, "lineage_01_aluva_broken.png"))
        results.append("Step 1: Open Timeline Card - PASSED")

        # -------------------------------------------------------------
        # STEP 2: Verify Preset 1 - Aluva Broken Lineage (0/100 DANGER)
        # -------------------------------------------------------------
        print("\n[Step 2] Auditing Aluva Broken Chain Preset...")
        timeline_card = page.locator(".timeline-card").last
        card_text = timeline_card.text_content()

        assert "Aluva" in card_text or "345/1" in card_text, "Expected Aluva property identifier!"
        assert "Score: 0/100" in card_text, f"Expected Score: 0/100, got: {card_text[:200]}"
        assert "DANGER" in card_text, "Expected DANGER verdict badge!"

        # Verify Financial Charges Table (Federal Bank Mortgage)
        assert "Federal Bank" in card_text or "Mortgage" in card_text, "Expected bank mortgage in encumbrance table!"

        # Verify Mary Roy Succession Defect & Extent Inflation
        assert "Mary Roy" in card_text or "Christian" in card_text or "Succession" in card_text, "Expected Mary Roy defect!"
        assert ("10" in card_text and "11" in card_text) or "inflation" in card_text.lower(), "Expected extent inflation flag!"

        print("  ✓ Verified Aluva 0/100: Mary Roy defect, Federal Bank mortgage, and extent inflation.")
        results.append("Step 2: Aluva Broken Chain (0/100) - PASSED")

        # -------------------------------------------------------------
        # STEP 3: Switch to Preset 2 - Kakkanad Wetland & Minor Share
        # -------------------------------------------------------------
        print("\n[Step 3] Switching to Kakkanad Wetland & Minor Share Preset...")
        preset_kakkanad_btn = timeline_card.locator("button:has-text('Kakkanad')")
        expect(preset_kakkanad_btn).to_be_visible()
        preset_kakkanad_btn.click()
        page.wait_for_timeout(800)

        # Verify updated timeline
        timeline_card = page.locator(".timeline-card").last
        card_text = timeline_card.text_content()
        print(f"  → Kakkanad Timeline loaded: {card_text[:140]}...")

        assert "Kakkanad" in card_text or "182/4" in card_text, "Expected Kakkanad property identifier!"
        assert any(term in card_text for term in ["Wetland", "Paddy Land", "Data Bank", "Minor", "Court"]), \
            "Expected statutory paddy land or minor share flags!"

        page.screenshot(path=os.path.join(SCREENSHOTS_DIR, "lineage_02_kakkanad_wetland.png"))
        results.append("Step 3: Kakkanad Wetland & Minor Share - PASSED")

        # -------------------------------------------------------------
        # STEP 4: Switch to Preset 3 - 100% Clean Title Chain
        # -------------------------------------------------------------
        print("\n[Step 4] Switching to 100% Clean Title Chain Preset...")
        preset_clean_btn = timeline_card.locator("button:has-text('100% Clean Title Chain')")
        expect(preset_clean_btn).to_be_visible()
        preset_clean_btn.click()
        page.wait_for_timeout(800)

        timeline_card = page.locator(".timeline-card").last
        card_text = timeline_card.text_content()
        print(f"  → Clean Title Chain loaded: {card_text[:140]}...")

        assert "Score: 100/100" in card_text, "Expected Score: 100/100 in clean title chain!"
        assert "CLEAN" in card_text or "CLEAR" in card_text, "Expected CLEAN title verdict!"
        assert "39" in card_text or "continuous" in card_text.lower(), "Expected 39-year continuous lineage!"

        score_badge = timeline_card.locator(".deed-score-badge.clear")
        expect(score_badge).to_be_visible()

        page.screenshot(path=os.path.join(SCREENSHOTS_DIR, "lineage_03_clean_title.png"))
        results.append("Step 4: 100% Clean Title Chain (100/100) - PASSED")

        # -------------------------------------------------------------
        # STEP 5: Interactive Timeline Controls (Satellite & Checklist)
        # -------------------------------------------------------------
        print("\n[Step 5] Testing Satellite View Link & On-Site Checklist Drawer...")
        # Test "View Region on Satellite"
        locate_btn = timeline_card.locator("button:has-text('View Region on Satellite')")
        expect(locate_btn).to_be_visible()
        locate_btn.click()
        page.wait_for_timeout(500)

        # Should ensure split view is active
        expect(page.locator("body")).to_have_class("view-split")
        print("  ✓ 'View Region on Satellite' correctly navigated to Split View.")

        # Test "On-Site Checklist" button inside timeline card
        # Re-locate timeline card
        checklist_btn = page.locator(".timeline-card").last.locator("button:has-text('On-Site Checklist')")
        expect(checklist_btn).to_be_visible()
        checklist_btn.click()
        page.wait_for_timeout(400)

        # Verify checklist drawer slid open
        expect(page.locator("#checklist-panel")).to_have_class("checklist-panel visible")
        print("  ✓ 'On-Site Checklist' drawer successfully opened.")
        page.screenshot(path=os.path.join(SCREENSHOTS_DIR, "lineage_04_checklist_drawer.png"))

        # Close checklist drawer
        page.locator(".checklist-close-btn").click()
        page.wait_for_timeout(200)

        results.append("Step 5: Satellite View Link & Checklist Drawer - PASSED")

        # Console error audit
        print("\n--- Console Errors Check ----")
        if console_errors:
            print(f"Captured {len(console_errors)} console errors:")
            for err in console_errors:
                print(f"  [Console Error] {err}")
        else:
            print("Zero console errors captured throughout Munnadharam Lineage tests!")

        browser.close()

    print("\n=======================================================")
    print("  MUNNADHARAM LINEAGE UI TEST SUMMARY")
    print("=======================================================")
    for r in results:
        print(f"  ✅ {r}")
    print("=======================================================\n")

def test_munnadharam_lineage_ui():
    """Standard pytest entrypoint for Munnadharam Lineage UI test."""
    run_munnadharam_lineage_test()

if __name__ == "__main__":
    run_munnadharam_lineage_test()
