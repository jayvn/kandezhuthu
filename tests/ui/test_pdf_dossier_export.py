import os

from playwright.sync_api import expect, sync_playwright

CHROMIUM_PATH = "/ms-playwright/chromium-1234/chrome-linux64/chrome" if os.path.exists("/ms-playwright/chromium-1234/chrome-linux64/chrome") else None
SCREENSHOTS_DIR = os.path.join(os.path.dirname(__file__), "screenshots")
BASE_URL = os.environ.get("TEST_BASE_URL", "http://localhost:8081")

def run_pdf_dossier_export_test():
    """
    Automated Playwright UI Test for Advocate Legal Dossier PDF Export Engine

    Verifies:
    1. Browser download interception across distinct UI trigger surfaces
    2. HUD Surface: exportPlotDossier() -> kandezhuthu_plot_dossier_*.pdf
    3. Timeline Surface: exportDossierPDF() -> kandezhuthu_legal_audit_*.pdf
    4. Deed OCR Surface: exportCurrentDeedDossier() -> kandezhuthu_deed_dossier_*.pdf
    5. Verifies non-zero byte size (> 1KB) and authentic %PDF- header magic bytes
    """
    os.makedirs(SCREENSHOTS_DIR, exist_ok=True)
    results = []

    print("\n=======================================================")
    print("  KANDEZTHUTHU AI: ADVOCATE PDF DOSSIER EXPORT UI TEST")
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
            accept_downloads=True
        )
        page = context.new_page()

        console_errors = []
        page.on("console", lambda msg: console_errors.append(msg.text) if msg.type == "error" else None)
        page.on("pageerror", lambda err: console_errors.append(str(err)))

        # -------------------------------------------------------------
        # STEP 1: Page Load & Initial State
        # -------------------------------------------------------------
        print("[Step 1] Loading Page & Preparing PDF Interception...")
        page.goto(BASE_URL, wait_until="domcontentloaded")
        page.wait_for_timeout(1200)

        expect(page.locator(".brand-title")).to_contain_text("Kandezhuthu AI")
        results.append("Step 1: Page Load & Setup - PASSED")

        # -------------------------------------------------------------
        # STEP 2: Surface 1 - HUD Plot Dossier Download
        # -------------------------------------------------------------
        print("\n[Step 2] Testing HUD Plot Dossier PDF Export...")
        plot_export_btn = page.locator("button:has-text('Export Dossier'), #btn-export-dossier, button:has-text('Dossier')").first
        expect(plot_export_btn).to_be_visible()

        with page.expect_download(timeout=15000) as download_info:
            plot_export_btn.click()

        download = download_info.value
        filename = download.suggested_filename
        print(f"  → Download intercepted: {filename}")
        assert filename.startswith("kandezhuthu_plot_dossier_") and filename.endswith(".pdf")

        # Save and verify PDF content
        saved_path = os.path.join(SCREENSHOTS_DIR, "test_plot_dossier.pdf")
        download.save_as(saved_path)
        file_size = os.path.getsize(saved_path)
        print(f"  → Saved plot dossier PDF size: {file_size} bytes")
        assert file_size > 1000, f"PDF file suspiciously small: {file_size} bytes"

        with open(saved_path, "rb") as f:
            header = f.read(5)
            assert header == b"%PDF-", f"Invalid PDF magic header: {header}"

        print("  ✓ HUD Plot Dossier successfully verified with genuine %PDF- header.")
        results.append("Step 2: HUD Plot Dossier PDF Export - PASSED")

        # -------------------------------------------------------------
        # STEP 3: Surface 2 - Munnadharam Timeline Dossier Download
        # -------------------------------------------------------------
        print("\n[Step 3] Testing Munnadharam Timeline Dossier PDF Export...")
        timeline_btn = page.locator("#btn-timeline-export")
        if timeline_btn.count() == 0:
            timeline_btn = page.locator("button:has-text('Ownership Timeline')").first

        timeline_btn.click()
        page.wait_for_timeout(800)
        expect(page.locator(".timeline-card")).to_be_visible()

        timeline_dossier_btn = page.locator(".timeline-card").last.locator("button:has-text('Download Advocate PDF')")
        expect(timeline_dossier_btn).to_be_visible()

        with page.expect_download(timeout=15000) as download_info:
            timeline_dossier_btn.click()

        download = download_info.value
        filename = download.suggested_filename
        print(f"  → Download intercepted: {filename}")
        assert filename.startswith("kandezhuthu_legal_audit_") and filename.endswith(".pdf")

        saved_path = os.path.join(SCREENSHOTS_DIR, "test_timeline_dossier.pdf")
        download.save_as(saved_path)
        file_size = os.path.getsize(saved_path)
        print(f"  → Saved timeline dossier PDF size: {file_size} bytes")
        assert file_size > 1000, f"PDF file suspiciously small: {file_size} bytes"

        with open(saved_path, "rb") as f:
            header = f.read(5)
            assert header == b"%PDF-", f"Invalid PDF magic header: {header}"

        print("  ✓ Timeline Advocate Dossier verified with authentic PDF structure.")
        results.append("Step 3: Munnadharam Timeline PDF Export - PASSED")

        # -------------------------------------------------------------
        # STEP 4: Surface 3 - Extracted Deed Audit Card Dossier Download
        # -------------------------------------------------------------
        print("\n[Step 4] Testing Extracted Deed Scorecard Dossier PDF Export...")
        # Trigger Sample Deed OCR
        deed_sample_btn = page.locator(".layman-card.card-deed, button:has-text('Sale Deed')").first
        deed_sample_btn.click()

        # Wait for deed card
        page.wait_for_selector(".deed-audit-card", timeout=20000)
        page.wait_for_timeout(1000)

        deed_dossier_btn = page.locator(".dossier-download-btn").last
        expect(deed_dossier_btn).to_be_visible()

        with page.expect_download(timeout=15000) as download_info:
            deed_dossier_btn.click()

        download = download_info.value
        filename = download.suggested_filename
        print(f"  → Download intercepted: {filename}")
        assert filename.startswith("kandezhuthu_deed_dossier_") and filename.endswith(".pdf")

        saved_path = os.path.join(SCREENSHOTS_DIR, "test_deed_dossier.pdf")
        download.save_as(saved_path)
        file_size = os.path.getsize(saved_path)
        print(f"  → Saved deed dossier PDF size: {file_size} bytes")
        assert file_size > 1000, f"PDF file suspiciously small: {file_size} bytes"

        with open(saved_path, "rb") as f:
            header = f.read(5)
            assert header == b"%PDF-", f"Invalid PDF magic header: {header}"

        print("  ✓ Deed Audit Card Dossier verified with genuine ReportLab PDF bytes.")
        page.screenshot(path=os.path.join(SCREENSHOTS_DIR, "dossier_export_complete.png"))
        results.append("Step 4: Deed Audit Card PDF Export - PASSED")

        # Console error audit
        print("\n--- Console Errors Check ----")
        if console_errors:
            print(f"Captured {len(console_errors)} console errors:")
            for err in console_errors:
                print(f"  [Console Error] {err}")
        else:
            print("Zero console errors captured throughout PDF Dossier Export tests!")

        browser.close()

    print("\n=======================================================")
    print("  ADVOCATE PDF DOSSIER EXPORT UI TEST SUMMARY")
    print("=======================================================")
    for r in results:
        print(f"  ✅ {r}")
    print("=======================================================\n")

def test_pdf_dossier_export():
    """Standard pytest entrypoint for Advocate PDF Dossier Export UI test."""
    run_pdf_dossier_export_test()

if __name__ == "__main__":
    run_pdf_dossier_export_test()
