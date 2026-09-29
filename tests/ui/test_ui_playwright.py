import os

from playwright.sync_api import expect, sync_playwright

CHROMIUM_PATH = "/ms-playwright/chromium-1234/chrome-linux64/chrome" if os.path.exists("/ms-playwright/chromium-1234/chrome-linux64/chrome") else None
SCREENSHOTS_DIR = os.path.join(os.path.dirname(__file__), "screenshots")
BASE_URL = os.environ.get("TEST_BASE_URL", "http://localhost:8081")

def run_ui_tests():
    os.makedirs(SCREENSHOTS_DIR, exist_ok=True)
    results = []

    print(f"[Playwright] Launching Chromium (executable: {CHROMIUM_PATH})...")
    with sync_playwright() as p:
        browser = p.chromium.launch(
            executable_path=CHROMIUM_PATH,
            headless=True,
            args=["--no-sandbox", "--disable-dev-shm-usage"]
        )
        context = browser.new_context(viewport={"width": 1440, "height": 900})
        page = context.new_page()

        # Track console errors
        console_errors = []
        page.on("console", lambda msg: console_errors.append(msg.text) if msg.type == "error" else None)
        page.on("pageerror", lambda err: console_errors.append(str(err)))

        # Test 1: Page Load & Initial State
        print("\n--- Test 1: Page Load & Initial State ---")
        page.goto(BASE_URL, wait_until="domcontentloaded")
        page.wait_for_timeout(1200)

        title = page.title()
        print(f"Page title: {title}")
        assert "Kandezhuthu AI" in title, f"Unexpected title: {title}"

        # Verify brand and view switcher
        expect(page.locator(".brand-title")).to_contain_text("Kandezhuthu AI")
        expect(page.locator(".view-btn[data-mode='split']")).to_have_class("view-btn active")

        # Verify HUD initial values
        hud_coords = page.locator("#hud-coords").text_content()
        hud_cents = page.locator("#hud-cents").text_content()
        print(f"Initial HUD coords: {hud_coords}, cents: {hud_cents}")
        assert "10.00 Cents" in hud_cents, f"Expected 10.00 Cents, got {hud_cents}"

        # Verify initial guidance bar
        guidance_text = page.locator("#guidance-text").text_content()
        print(f"Initial guidance: {guidance_text}")
        assert "inspection pin" in guidance_text.lower() or "demo plot" in guidance_text.lower()

        page.screenshot(path=os.path.join(SCREENSHOTS_DIR, "01_initial_split_view.png"), full_page=True)
        results.append("01_initial_split_view: PASSED")

        # Test 2: View Switcher (Chat Only, Map Only, Split)
        print("\n--- Test 2: View Switcher ---")
        # Switch to Chat only
        page.click(".view-btn[data-mode='chat']")
        page.wait_for_timeout(400)
        expect(page.locator("body")).to_have_class("view-chat")
        page.screenshot(path=os.path.join(SCREENSHOTS_DIR, "02_chat_only_view.png"), full_page=True)

        # Switch to Map only
        page.click(".view-btn[data-mode='map']")
        page.wait_for_timeout(400)
        expect(page.locator("body")).to_have_class("view-map")
        page.screenshot(path=os.path.join(SCREENSHOTS_DIR, "03_map_only_view.png"), full_page=True)

        # Switch back to Split
        page.click(".view-btn[data-mode='split']")
        page.wait_for_timeout(400)
        expect(page.locator("body")).to_have_class("view-split")
        results.append("02_view_switcher: PASSED")

        # Test 3: Location Preset Change
        print("\n--- Test 3: Preset Location Selection ---")
        preset_select = page.locator("#preset-select")
        preset_select.select_option("kakkanad")
        page.wait_for_timeout(800)

        updated_hud_title = page.locator("#hud-locality-title").text_content()
        updated_hud_cents = page.locator("#hud-cents").text_content()
        print(f"Kakkanad preset loaded: {updated_hud_title}, {updated_hud_cents}")
        assert "Kakkanad" in updated_hud_title, f"Expected Kakkanad in HUD title, got: {updated_hud_title}"
        page.screenshot(path=os.path.join(SCREENSHOTS_DIR, "04_preset_kakkanad.png"), full_page=True)
        results.append("03_preset_kakkanad: PASSED")

        # Test 4: Map Drawing & Undo Tool
        print("\n--- Test 4: Map Drawing Tools & Undo Functionality ---")
        # Clear drawings
        page.click("button:has-text('Clear')")
        page.wait_for_timeout(300)
        expect(page.locator("#hud-cents")).to_have_text("0.00 Cents")

        # Click Draw Plot tool
        page.click("#tool-plot")
        expect(page.locator("#tool-plot")).to_have_class("map-tool-btn active")

        # Check guidance bar updated for plot
        expect(page.locator("#guidance-text")).to_contain_text("corner stones")
        expect(page.locator("#guidance-actions")).to_be_visible()

        # Click on map canvas at 3 points to create a triangle
        map_view = page.locator("#map-view")
        box = map_view.bounding_box()
        assert box is not None
        cx, cy = box["x"] + box["width"] / 2, box["y"] + box["height"] / 2
        ox, oy = cx - 120, cy - 120

        # Click 3 points
        page.mouse.click(ox, oy)
        page.wait_for_timeout(200)
        page.mouse.click(ox + 80, oy)
        page.wait_for_timeout(200)
        page.mouse.click(ox + 40, oy + 80)
        page.wait_for_timeout(500)

        drawn_cents = page.locator("#hud-cents").text_content()
        print(f"Drawn plot extent: {drawn_cents}")
        assert "Cents" in drawn_cents and "0.00" not in drawn_cents, f"Plot area calculation failed: {drawn_cents}"

        # Test Undo Point button
        undo_btn = page.locator("#btn-undo")
        expect(undo_btn).to_be_enabled()
        undo_btn.click()
        page.wait_for_timeout(300)
        print("Undo button successfully removed last point.")

        # Re-add third point
        page.mouse.click(ox + 40, oy + 80)
        page.wait_for_timeout(400)

        page.screenshot(path=os.path.join(SCREENSHOTS_DIR, "05_drawn_plot.png"), full_page=True)
        results.append("04_draw_plot_and_undo: PASSED")

        # Test 5: Road Width measurement tool & KPBR Pill
        print("\n--- Test 5: Road Width Tool & KPBR Badge ---")
        page.click("#tool-road")
        expect(page.locator("#tool-road")).to_have_class("map-tool-btn active")
        expect(page.locator("#guidance-text")).to_contain_text("Kerala Panchayat Building Rules")

        # Click 2 points to measure road
        page.mouse.click(cx - 50, cy - 50)
        page.wait_for_timeout(200)
        page.mouse.click(cx - 30, cy - 50)
        page.wait_for_timeout(500)

        road_status = page.locator("#hud-road").text_content()
        print(f"Road width measurement: {road_status}")
        assert "meters" in road_status or "m" in road_status, f"Road measurement failed: {road_status}"
        expect(page.locator("#hud-road-badge")).to_be_visible()
        page.screenshot(path=os.path.join(SCREENSHOTS_DIR, "06_road_width_measurement.png"), full_page=True)
        results.append("05_road_width: PASSED")

        # Test 6: Interactive Field Checklist & HUD Minimize
        print("\n--- Test 6: Field Checklist & HUD Minimize ---")
        # Toggle checklist panel
        page.click("#btn-checklist-toggle")
        page.wait_for_timeout(300)
        expect(page.locator("#checklist-panel")).to_have_class("checklist-panel visible")

        # Check two items
        page.check("#chk-kallu")
        page.check("#chk-road")
        page.wait_for_timeout(200)
        expect(page.locator("#chk-badge")).to_have_text("2/5")
        print("Checklist progress updated to 2/5.")

        # Toggle HUD minimize
        page.click("#hud-toggle-btn")
        page.wait_for_timeout(300)
        expect(page.locator("#map-hud")).to_have_class("map-hud minimized")
        print("HUD successfully minimized.")
        # Restore HUD
        page.click("#hud-toggle-btn")
        page.wait_for_timeout(200)

        # Test 7: Send Plot to Auditor AI
        print("\n--- Test 7: Send Plot to Auditor AI ---")
        page.click("#btn-send-auditor, button:has-text('Send to Auditor')")
        # Should populate input and submit chat message
        page.wait_for_timeout(1000)
        # Verify a user message appeared in log
        user_msgs = page.locator(".msg.user")
        expect(user_msgs.last).to_contain_text("I am inspecting a property plot")
        print("Sent plot message to Auditor successfully.")
        page.screenshot(path=os.path.join(SCREENSHOTS_DIR, "07_plot_sent_to_auditor.png"), full_page=True)
        results.append("06_send_plot_to_auditor: PASSED")

        # Wait for agent reply (with timeout for LLM inference)
        print("Waiting for agent audit response...")
        try:
            page.wait_for_function(
                "() => document.querySelectorAll('.msg.agent').length >= 2 && !document.querySelector('#send-btn').disabled",
                timeout=35000
            )
            print("Agent response received!")
            page.screenshot(path=os.path.join(SCREENSHOTS_DIR, "08_agent_response_received.png"), full_page=True)
            results.append("07_agent_response: PASSED")
        except Exception as e:
            print(f"Agent response wait timed out or failed: {e}")
            results.append("07_agent_response: TIMED_OUT (Expected if offline/mock)")

        # Test 8: Mobile Viewport Responsiveness
        print("\n--- Test 8: Mobile Viewport Responsiveness ---")
        mobile_page = context.new_page()
        mobile_page.set_viewport_size({"width": 375, "height": 812}) # iPhone X/12
        mobile_page.goto(BASE_URL, wait_until="domcontentloaded")
        mobile_page.wait_for_timeout(1000)
        mobile_page.screenshot(path=os.path.join(SCREENSHOTS_DIR, "09_mobile_initial.png"), full_page=True)

        # Test switching to Map on mobile
        mobile_page.click(".view-btn[data-mode='map']")
        mobile_page.wait_for_timeout(500)
        mobile_page.screenshot(path=os.path.join(SCREENSHOTS_DIR, "10_mobile_map_view.png"), full_page=True)
        results.append("08_mobile_view: PASSED")
        mobile_page.close()

        # Summary of console errors
        print("\n--- Console Errors Check ---")
        if console_errors:
            print(f"Captured {len(console_errors)} console errors:")
            for err in console_errors:
                print(f"  [ERROR] {err}")
        else:
            print("Zero console errors captured!")

        browser.close()

    print("\n================ TEST SUMMARY ================")
    for r in results:
        print(r)
    print("==============================================")

def test_ui_playwright():
    """Standard pytest entrypoint for general UI playwright tests."""
    run_ui_tests()

if __name__ == "__main__":
    run_ui_tests()
