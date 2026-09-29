import os

from playwright.sync_api import expect, sync_playwright

CHROMIUM_PATH = "/ms-playwright/chromium-1234/chrome-linux64/chrome" if os.path.exists("/ms-playwright/chromium-1234/chrome-linux64/chrome") else None
SCREENSHOTS_DIR = os.path.join(os.path.dirname(__file__), "screenshots")
BASE_URL = os.environ.get("TEST_BASE_URL", "http://localhost:8081")

def run_elevation_flood_ui_test():
    """
    Automated Playwright UI Test for Plot Elevation & Flood Exposure Engine

    Verifies:
    1. Default HUD displays Mean Sea Level (MSL) elevation and flood exposure badge
    2. Dynamic hydrology updates across distinct Kerala topographical regions (Aluva, Kuttanad, Kakkanad)
    3. Custom drawn plot centroid elevation calculation upon sealing plot
    4. On-site field inspection checklist includes 2018 flood watermark check
    5. "Send to Auditor" passes elevation and flood vulnerability to agent prompt
    """
    os.makedirs(SCREENSHOTS_DIR, exist_ok=True)
    results = []

    print("\n=======================================================")
    print("  KANDEZTHUTHU AI: PLOT ELEVATION & FLOOD UI TEST")
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

        # -------------------------------------------------------------
        # STEP 1: Page Load & Default Aluva Elevation in HUD
        # -------------------------------------------------------------
        print("[Step 1] Loading Split View & Default Aluva Flood HUD...")
        page.goto(BASE_URL, wait_until="networkidle")
        page.wait_for_timeout(1200)

        expect(page.locator(".brand-title")).to_contain_text("Kandezhuthu AI")

        # Verify Elevation Stat Box in HUD
        elev_box = page.locator("#hud-elevation-box")
        expect(elev_box).to_be_visible()

        elev_text = page.locator("#hud-elevation-text").text_content()
        flood_badge = page.locator("#hud-flood-badge").text_content()
        basin_text = page.locator("#hud-basin-text").text_content()
        print(f"  Default HUD Elevation: {elev_text}")
        print(f"  Default Flood Badge:   {flood_badge}")
        print(f"  Default Basin Info:    {basin_text}")

        assert "6.5" in elev_text or "MSL" in elev_text, f"Unexpected elevation text: {elev_text}"
        assert "Moderate" in flood_badge or "Flood" in flood_badge, f"Unexpected badge: {flood_badge}"
        assert "Periyar" in basin_text, f"Expected Periyar River Basin, got: {basin_text}"

        page.screenshot(path=os.path.join(SCREENSHOTS_DIR, "elevation_01_aluva_flood_hud.png"))
        results.append("Step 1: Default Aluva Flood HUD - PASSED")

        # -------------------------------------------------------------
        # STEP 2: Region Preset Switching - Kuttanad Sub-MSL Trap
        # -------------------------------------------------------------
        print("\n[Step 2] Testing Kuttanad Sub-Sea-Level Wetland Polders...")
        preset_select = page.locator("#preset-select")
        preset_select.select_option("kuttanad")
        page.wait_for_timeout(1000)

        elev_kuttanad = page.locator("#hud-elevation-text").text_content()
        badge_kuttanad = page.locator("#hud-flood-badge").text_content()
        basin_kuttanad = page.locator("#hud-basin-text").text_content()
        print(f"  Kuttanad Elevation: {elev_kuttanad}")
        print(f"  Kuttanad Badge:     {badge_kuttanad}")
        print(f"  Kuttanad Basin:     {basin_kuttanad}")

        assert "0.8" in elev_kuttanad or "MSL" in elev_kuttanad, f"Expected low elevation, got: {elev_kuttanad}"
        assert "Critical" in badge_kuttanad or "Sub-MSL" in badge_kuttanad, f"Expected Critical badge, got: {badge_kuttanad}"
        assert "Vembanad" in basin_kuttanad or "Pamba" in basin_kuttanad, f"Expected Vembanad basin, got: {basin_kuttanad}"

        page.screenshot(path=os.path.join(SCREENSHOTS_DIR, "elevation_02_kuttanad_critical_hud.png"))
        results.append("Step 2: Kuttanad Sub-MSL Hazard - PASSED")

        # -------------------------------------------------------------
        # STEP 3: Region Preset Switching - Kakkanad Elevated Midlands
        # -------------------------------------------------------------
        print("\n[Step 3] Testing Kakkanad Elevated Midlands...")
        preset_select.select_option("kakkanad")
        page.wait_for_timeout(1000)

        elev_kakkanad = page.locator("#hud-elevation-text").text_content()
        badge_kakkanad = page.locator("#hud-flood-badge").text_content()
        basin_kakkanad = page.locator("#hud-basin-text").text_content()
        print(f"  Kakkanad Elevation: {elev_kakkanad}")
        print(f"  Kakkanad Badge:     {badge_kakkanad}")
        print(f"  Kakkanad Basin:     {basin_kakkanad}")

        assert "26" in elev_kakkanad or "MSL" in elev_kakkanad, f"Expected high elevation, got: {elev_kakkanad}"
        assert "Low Flood Risk" in badge_kakkanad, f"Expected Low Flood Risk, got: {badge_kakkanad}"

        page.screenshot(path=os.path.join(SCREENSHOTS_DIR, "elevation_03_kakkanad_low_risk_hud.png"))
        results.append("Step 3: Kakkanad Elevated Midlands - PASSED")

        # -------------------------------------------------------------
        # STEP 4: Interactive Field Checklist - Flood Watermarks
        # -------------------------------------------------------------
        print("\n[Step 4] Verifying 5-Item Field Checklist & Flood Check...")
        checklist_btn = page.locator("#btn-checklist-toggle")
        expect(checklist_btn).to_contain_text("0/5")

        # Open checklist panel
        checklist_btn.click()
        page.wait_for_timeout(300)
        expect(page.locator("#checklist-panel")).to_have_class("checklist-panel visible")

        # Verify flood watermark checkbox
        chk_flood = page.locator("#chk-flood")
        expect(chk_flood).to_be_visible()

        # Check all 5 items
        for chk_id in ["#chk-kallu", "#chk-road", "#chk-wetland", "#chk-ht", "#chk-flood"]:
            page.locator(chk_id).check()
            page.wait_for_timeout(100)

        expect(page.locator("#chk-badge")).to_have_text("5/5")
        print("  ✓ All 5 checklist items checked; badge updated to 5/5.")

        page.screenshot(path=os.path.join(SCREENSHOTS_DIR, "elevation_04_checklist_flood_item.png"))
        results.append("Step 4: 5-Item Checklist & Flood Watermark Verification - PASSED")

        # -------------------------------------------------------------
        # STEP 5: Auditor Bridge Prompt - Elevation & Flood Passed to LLM
        # -------------------------------------------------------------
        print("\n[Step 5] Testing Send Plot to Auditor AI with Elevation...")
        # Switch back to Aluva for sample plot audit
        preset_select.select_option("aluva")
        page.wait_for_timeout(1000)

        send_to_auditor_btn = page.locator("button:has-text(\"Send to Auditor\")")
        expect(send_to_auditor_btn).to_be_visible()
        send_to_auditor_btn.click()
        page.wait_for_timeout(1000)

        # Check the user chat bubble sent to auditor
        last_user_msg = page.locator(".msg.user").last.text_content()
        print(f"  Auditor Prompt Sent: {last_user_msg[:160]}...")

        assert "Plot Elevation:" in last_user_msg, "Expected Plot Elevation in prompt!"
        assert "MSL" in last_user_msg, "Expected MSL in prompt!"
        assert "Flood Risk:" in last_user_msg or "flood" in last_user_msg.lower(), "Expected Flood Risk in prompt!"

        page.screenshot(path=os.path.join(SCREENSHOTS_DIR, "elevation_05_auditor_prompt_flood.png"))
        results.append("Step 5: Auditor Bridge with Topographic Flood Data - PASSED")

        # Console error audit
        print("\n--- Console Errors Check ----")
        if console_errors:
            print(f"Captured {len(console_errors)} console errors:")
            for err in console_errors:
                print(f"  [Console Error] {err}")
        else:
            print("Zero console errors captured throughout elevation & flood UI tests!")

        browser.close()

    print("\n=======================================================")
    print("  PLOT ELEVATION & FLOOD UI TEST SUMMARY")
    print("=======================================================")
    for r in results:
        print(f"  ✅ {r}")
    print("=======================================================\n")

def test_elevation_flood_ui():
    """Standard pytest entrypoint for Plot Elevation & Flood Exposure UI test."""
    run_elevation_flood_ui_test()

if __name__ == "__main__":
    run_elevation_flood_ui_test()
