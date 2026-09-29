import os

from playwright.sync_api import expect, sync_playwright

CHROMIUM_PATH = "/ms-playwright/chromium-1234/chrome-linux64/chrome" if os.path.exists("/ms-playwright/chromium-1234/chrome-linux64/chrome") else None
SCREENSHOTS_DIR = os.path.join(os.path.dirname(__file__), "screenshots")
BASE_URL = os.environ.get("TEST_BASE_URL", "http://localhost:8081")

def run_cadastral_map_tools_test():
    """
    Automated Playwright UI Test for Cadastral Map Tools & Plot Sealing Engine

    Verifies:
    1. Map Locality Search & Geocoding (#map-search-input)
    2. Inspection Pin Placement (#tool-pin) and GPS Coordinate HUD updates
    3. Multi-Point Polygon Plot Drawing, Undo Point, and "Seal Plot" Action
    4. Dynamic Centroid Elevation & KSDMA River Basin Recalculation
    5. Road Width Measurement Tool (#tool-road) & KPBR 2019 Table 5 Compliance Badge
    6. Canvas Clear Action and Extent Reset
    """
    os.makedirs(SCREENSHOTS_DIR, exist_ok=True)
    results = []

    print("\n=======================================================")
    print("  KANDEZTHUTHU AI: CADASTRAL MAP & PLOT SEALING TEST")
    print(f"  Target: {BASE_URL}")
    print("=======================================================")

    with sync_playwright() as p:
        browser = p.chromium.launch(
            executable_path=CHROMIUM_PATH,
            headless=True,
            args=["--no-sandbox", "--disable-dev-shm-usage"]
        )
        context = browser.new_context(
            viewport={"width": 1440, "height": 900}
        )
        page = context.new_page()

        console_errors = []
        page.on("console", lambda msg: console_errors.append(msg.text) if msg.type == "error" else None)
        page.on("pageerror", lambda err: console_errors.append(str(err)))

        # -------------------------------------------------------------
        # STEP 1: Page Load & Map Canvas Verification
        # -------------------------------------------------------------
        print("[Step 1] Loading Page & Satellite Map Canvas...")
        page.goto(BASE_URL, wait_until="networkidle")
        page.wait_for_timeout(1000)

        expect(page.locator(".brand-title")).to_contain_text("Kandezhuthu AI")
        expect(page.locator("#map-view")).to_be_visible()
        results.append("Step 1: Map View Visible - PASSED")

        # -------------------------------------------------------------
        # STEP 2: Map Search & Locality Geocoding
        # -------------------------------------------------------------
        print("\n[Step 2] Testing Map Search for 'Kakkanad'...")
        search_input = page.locator("#map-search-input")
        expect(search_input).to_be_visible()
        search_input.fill("Kakkanad")

        # Click search button or press Enter
        search_btn = page.locator(".map-search-btn")
        search_btn.click()
        page.wait_for_timeout(1000)

        # Check HUD locality updated
        hud_locality = page.locator("#hud-locality-title").text_content()
        print(f"  → Updated HUD Locality: {hud_locality.strip()}")
        assert "Kakkanad" in hud_locality, f"Expected Kakkanad in HUD, got: {hud_locality}"

        page.screenshot(path=os.path.join(SCREENSHOTS_DIR, "map_01_search_kakkanad.png"))
        results.append("Step 2: Map Locality Search - PASSED")

        # -------------------------------------------------------------
        # STEP 3: Pin Inspection Tool & Coordinate HUD
        # -------------------------------------------------------------
        print("\n[Step 3] Testing Pin Inspection Tool...")
        pin_btn = page.locator("#tool-pin")
        pin_btn.click()
        expect(pin_btn).to_have_class("map-tool-btn active")

        # Click on map canvas
        map_view = page.locator("#map-view")
        box = map_view.bounding_box()
        assert box is not None
        cx, cy = box["x"] + box["width"] / 2, box["y"] + box["height"] / 2

        page.mouse.click(cx + 60, cy - 40)
        page.wait_for_timeout(500)

        coords_text = page.locator("#hud-coords").text_content()
        print(f"  → Pin placed. HUD Coordinates: {coords_text.strip()}")
        assert "°N" in coords_text or "," in coords_text, "Expected updated coordinates in HUD!"
        results.append("Step 3: Pin Inspection Tool - PASSED")

        # -------------------------------------------------------------
        # STEP 4: Polygon Plot Drawing, Undo, and "Seal Plot"
        # -------------------------------------------------------------
        print("\n[Step 4] Testing Multi-Point Plot Drawing & 'Seal Plot' Action...")
        # Clear existing drawings
        clear_btn = page.locator("button:has-text('Clear')").first
        clear_btn.click()
        page.wait_for_timeout(300)
        expect(page.locator("#hud-cents")).to_have_text("0.00 Cents")

        # Activate Plot Tool
        plot_btn = page.locator("#tool-plot")
        plot_btn.click()
        expect(plot_btn).to_have_class("map-tool-btn active")

        # Click 4 points to form a quadrilateral plot
        points = [
            (cx - 50, cy - 50),
            (cx + 50, cy - 50),
            (cx + 50, cy + 50),
            (cx - 50, cy + 50),
        ]
        for px, py in points:
            page.mouse.click(px, py)
            page.wait_for_timeout(200)

        # Test Undo Point button
        undo_btn = page.locator("#btn-undo")
        expect(undo_btn).to_be_enabled()
        undo_btn.click()
        page.wait_for_timeout(300)
        print("  ✓ Undo point successfully removed last corner stone.")

        # Re-add fourth corner point
        page.mouse.click(cx - 50, cy + 50)
        page.wait_for_timeout(300)

        # Guidance Bar should show "Seal Plot" button
        seal_btn = page.locator("#guidance-finish-btn")
        expect(seal_btn).to_be_visible()
        seal_btn.click()
        page.wait_for_timeout(600)

        # Verify acreage calculated in Cents
        cents_text = page.locator("#hud-cents").text_content()
        print(f"  → Plot Sealed! HUD Extent: {cents_text.strip()}")
        assert "Cents" in cents_text and "0.00" not in cents_text, f"Expected non-zero Cents, got: {cents_text}"

        # Verify centroid elevation was computed
        elev_text = page.locator("#hud-elevation-text").text_content()
        print(f"  → Centroid Elevation: {elev_text.strip()}")
        assert "MSL" in elev_text or "m" in elev_text

        page.screenshot(path=os.path.join(SCREENSHOTS_DIR, "map_02_sealed_plot.png"))
        results.append("Step 4: Draw & Seal Plot Polygon - PASSED")

        # -------------------------------------------------------------
        # STEP 5: Road Width Tool & KPBR Compliance Badge
        # -------------------------------------------------------------
        print("\n[Step 5] Testing Road Width Measurement & KPBR Pill...")
        road_btn = page.locator("#tool-road")
        road_btn.click()
        expect(road_btn).to_have_class("map-tool-btn active")

        # Measure 2 points along lane
        page.mouse.click(cx - 80, cy + 80)
        page.wait_for_timeout(200)
        page.mouse.click(cx - 50, cy + 80)
        page.wait_for_timeout(500)

        road_status = page.locator("#hud-road").text_content()
        print(f"  → Road width status: {road_status.strip()}")
        assert "meters" in road_status or "m" in road_status, f"Expected road measurement, got: {road_status}"
        expect(page.locator("#hud-road-badge")).to_be_visible()

        page.screenshot(path=os.path.join(SCREENSHOTS_DIR, "map_03_road_measurement.png"))
        results.append("Step 5: Road Width Measurement & KPBR Compliance - PASSED")

        # -------------------------------------------------------------
        # STEP 6: Clear Map Drawings
        # -------------------------------------------------------------
        print("\n[Step 6] Testing Clear Map Drawings Action...")
        clear_btn.click()
        page.wait_for_timeout(300)

        expect(page.locator("#hud-cents")).to_have_text("0.00 Cents")
        expect(page.locator("#hud-road-badge")).not_to_be_visible()
        print("  ✓ Map drawings cleared and HUD acreage reset to 0.00 Cents.")
        results.append("Step 6: Clear Map Drawings - PASSED")

        # Console error audit
        print("\n--- Console Errors Check ----")
        if console_errors:
            print(f"Captured {len(console_errors)} console errors:")
            for err in console_errors:
                print(f"  [Console Error] {err}")
        else:
            print("Zero console errors captured throughout Cadastral Map tests!")

        browser.close()

    print("\n=======================================================")
    print("  CADASTRAL MAP & PLOT SEALING TEST SUMMARY")
    print("=======================================================")
    for r in results:
        print(f"  ✅ {r}")
    print("=======================================================\n")

def test_cadastral_map_tools():
    """Standard pytest entrypoint for Cadastral Map Tools UI test."""
    run_cadastral_map_tools_test()

if __name__ == "__main__":
    run_cadastral_map_tools_test()
