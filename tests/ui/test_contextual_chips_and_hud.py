import os
from playwright.sync_api import sync_playwright, expect

CHROMIUM_PATH = "/ms-playwright/chromium-1234/chrome-linux64/chrome" if os.path.exists("/ms-playwright/chromium-1234/chrome-linux64/chrome") else None
BASE_URL = os.environ.get("TEST_BASE_URL", "http://localhost:8081")

def test_contextual_chips_and_hud():
    with sync_playwright() as p:
        browser = p.chromium.launch(
            executable_path=CHROMIUM_PATH,
            headless=True,
            args=["--no-sandbox", "--disable-dev-shm-usage"]
        )
        context = browser.new_context(viewport={"width": 1440, "height": 900})
        page = context.new_page()

        print(f"Connecting to {BASE_URL}...")
        page.goto(BASE_URL, wait_until="networkidle")
        page.wait_for_timeout(1000)

        # 1. Verify Automation Hooks exist
        required_ids = [
            "btn-hud-export", "btn-hud-auditor", "btn-hud-maps", "hud-elevation",
            "preset-select", "tool-road", "tool-plot", "btn-checklist-toggle",
            "chk-kallu", "chk-road", "chk-wetland", "chk-ht", "chk-flood",
            "btn-pdf-export", "send-btn", "input", "form", "chips-container"
        ]
        for elem_id in required_ids:
            locator = page.locator(f"#{elem_id}")
            assert locator.count() > 0, f"Missing required element #{elem_id}"
        print("✓ All critical automation hooks and IDs exist.")

        # 2. Verify Step 1 Chips
        page.evaluate("setWorkflowStep(1)")
        page.wait_for_timeout(200)
        step1_expected = ["chip-sample-deed", "chip-sample-ec", "chip-upload-deed"]
        for cid in step1_expected:
            expect(page.locator(f"#{cid}")).to_be_visible()
        # Verify chips from other steps are hidden
        hidden_in_step1 = ["chip-timeline-aluva", "chip-measure-road", "chip-open-checklist"]
        for cid in hidden_in_step1:
            expect(page.locator(f"#{cid}")).not_to_be_visible()
        print("✓ Step 1 shows exactly dedicated Ingest chips.")

        # 3. Verify Step 2 Chips
        page.evaluate("setWorkflowStep(2)")
        page.wait_for_timeout(200)
        step2_expected = ["chip-timeline-aluva", "chip-mary-roy", "chip-timeline-clean", "chip-fair-value"]
        for cid in step2_expected:
            expect(page.locator(f"#{cid}")).to_be_visible()
        # Verify step 1 chips hidden
        expect(page.locator("#chip-sample-deed")).not_to_be_visible()
        print("✓ Step 2 shows exactly dedicated Lineage Audit chips.")

        # 4. Verify Step 3 Chips
        page.evaluate("setWorkflowStep(3)")
        page.wait_for_timeout(200)
        step3_expected = ["chip-measure-road", "chip-demarcate-plot", "chip-check-elevation", "chip-switch-map-view"]
        for cid in step3_expected:
            expect(page.locator(f"#{cid}")).to_be_visible()
        expect(page.locator("#chip-timeline-aluva")).not_to_be_visible()
        print("✓ Step 3 shows exactly dedicated Satellite & KPBR chips.")

        # 5. Verify Step 4 Chips
        page.evaluate("setWorkflowStep(4)")
        page.wait_for_timeout(200)
        step4_expected = ["chip-open-checklist", "chip-wa-inquiry", "chip-export-dossier", "chip-restart-diligence"]
        for cid in step4_expected:
            expect(page.locator(f"#{cid}")).to_be_visible()
        # Statutory chips from legacy should NOT leak in step 4
        expect(page.locator("#chip-survey-kallu")).not_to_be_visible()
        expect(page.locator("#chip-sec45a")).not_to_be_visible()
        print("✓ Step 4 shows exactly dedicated Action & Resolution chips.")

        # 6. Verify HUD Buttons and CSS
        auditor_btn = page.locator("#btn-hud-auditor")
        export_btn = page.locator("#btn-hud-export")
        maps_btn = page.locator("#btn-hud-maps")

        assert "To Auditor" in auditor_btn.text_content()
        assert "Export PDF" in export_btn.text_content()
        assert "Google Maps" in maps_btn.text_content()
        print("✓ HUD button texts match specification ('🚀 To Auditor', '📑 Export PDF', '🗺️ Google Maps').")

        # Test CSS on hud-actions and buttons
        actions_display = page.evaluate("() => window.getComputedStyle(document.querySelector('.hud-actions')).display")
        actions_gap = page.evaluate("() => window.getComputedStyle(document.querySelector('.hud-actions')).gap")
        btn_white_space = page.evaluate("() => window.getComputedStyle(document.querySelector('#btn-hud-export')).whiteSpace")
        btn_font_size = page.evaluate("() => window.getComputedStyle(document.querySelector('#btn-hud-export')).fontSize")

        assert actions_display == "flex", f"Expected flex, got {actions_display}"
        assert actions_gap == "6px", f"Expected 6px gap, got {actions_gap}"
        assert btn_white_space == "nowrap", f"Expected nowrap, got {btn_white_space}"
        assert btn_font_size == "11px", f"Expected 11px font size, got {btn_font_size}"
        print("✓ HUD actions CSS (.hud-actions display:flex, gap:6px; .hud-btn white-space:nowrap, font-size:11px) verified.")

        # 7. Bilingual translations test for chips and HUD
        page.evaluate("setLanguage('ml')")
        page.wait_for_timeout(200)
        page.evaluate("setWorkflowStep(1)")
        page.wait_for_timeout(200)
        expect(page.locator("#chip-sample-deed")).to_contain_text("മാതൃകാ തീറാധാരം")
        expect(auditor_btn).to_contain_text("ഓഡിറ്ററിലേക്ക്")
        expect(export_btn).to_contain_text("PDF റിപ്പോർട്ട്")
        expect(maps_btn).to_contain_text("ഗൂഗിൾ മാപ്പ്")
        print("✓ Malayalam translations for contextual chips and HUD buttons verified.")

        # Switch back to English
        page.evaluate("setLanguage('en')")
        page.wait_for_timeout(200)
        expect(page.locator("#chip-sample-deed")).to_contain_text("Test Kerala Sale Deed")
        expect(auditor_btn).to_contain_text("To Auditor")
        expect(export_btn).to_contain_text("Export PDF")
        expect(maps_btn).to_contain_text("Google Maps")
        print("✓ English translations verified.")

        browser.close()
        print("\nALL CONTEXTUAL CHIPS AND HUD VERIFICATION TESTS PASSED SUCCESSFULLY! 🎉")

if __name__ == "__main__":
    test_contextual_chips_and_hud()
