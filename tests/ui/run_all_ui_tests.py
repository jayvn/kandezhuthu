#!/usr/bin/env python3
"""
Kandezhuthu AI - Master Playwright UI Test Suite Runner

Orchestrates and executes all automated UI end-to-end tests:
1. General UI & View Switcher (test_ui_playwright.py)
2. Topographic Elevation & Flood Risk Engine (test_elevation_flood_ui.py)
3. Realistic Buyer Journey Persona (test_realistic_buyer_journey.py)
4. Multimodal Title Deed & SRO EC OCR Pipeline (test_ocr_document_pipeline.py)
5. 30-Year Prior Title Lineage (Munnadharam) Visualizer (test_munnadharam_lineage_ui.py)
6. Publication-Grade Advocate PDF Legal Dossier Export (test_pdf_dossier_export.py)
7. Cadastral Map Tools, Geocoding & Plot Sealing (test_cadastral_map_tools.py)
8. Bilingual UI Switcher & 3-Step Guided Workflow (test_bilingual_workflow_ui.py)
"""

import argparse
import os
import sys
import time

from tests.ui.test_bilingual_workflow_ui import run_bilingual_workflow_test
from tests.ui.test_cadastral_map_tools import run_cadastral_map_tools_test
from tests.ui.test_elevation_flood_ui import run_elevation_flood_ui_test
from tests.ui.test_munnadharam_lineage_ui import run_munnadharam_lineage_test
from tests.ui.test_ocr_document_pipeline import run_ocr_document_pipeline_test
from tests.ui.test_pdf_dossier_export import run_pdf_dossier_export_test
from tests.ui.test_realistic_buyer_journey import run_realistic_buyer_journey_test
from tests.ui.test_ui_playwright import run_ui_tests

SUITES = {
    "general": ("General UI & Split View Switcher", run_ui_tests),
    "elevation": ("Plot Elevation & Flood Risk Engine", run_elevation_flood_ui_test),
    "journey": ("Realistic Buyer Journey Persona", run_realistic_buyer_journey_test),
    "ocr": ("Multimodal Deed & SRO EC OCR Pipeline", run_ocr_document_pipeline_test),
    "lineage": ("30-Year Munnadharam Title Lineage", run_munnadharam_lineage_test),
    "pdf": ("Advocate Legal Dossier PDF Export", run_pdf_dossier_export_test),
    "map": ("Cadastral Map Tools & Plot Sealing", run_cadastral_map_tools_test),
    "workflow": ("Bilingual UI & Guided Workflow", run_bilingual_workflow_test),
}

def main():
    parser = argparse.ArgumentParser(description="Kandezhuthu AI Playwright UI Test Runner")
    parser.add_argument(
        "--suite",
        choices=[*list(SUITES.keys()), "all"],
        default="all",
        help="Specify which UI test suite to run (default: all)"
    )
    args = parser.parse_args()

    selected_suites = SUITES if args.suite == "all" else {args.suite: SUITES[args.suite]}

    print("\n" + "=" * 70)
    print("  KANDEZTHUTHU AI: AUTOMATED PLAYWRIGHT TEST SUITE RUNNER")
    print(f"  Target Environment: {os.environ.get('TEST_BASE_URL', 'http://localhost:8081')}")
    print(f"  Suites to Execute: {len(selected_suites)}")
    print("=" * 70 + "\n")

    report = []
    total_start = time.time()

    for key, (name, runner_fn) in selected_suites.items():
        print(f"\n▶ STARTING SUITE [{key.upper()}]: {name}")
        suite_start = time.time()
        try:
            runner_fn()
            duration = time.time() - suite_start
            report.append((name, "PASSED", f"{duration:.2f}s"))
            print(f"✔ SUITE [{key.upper()}] PASSED ({duration:.2f}s)\n")
        except Exception as e:
            duration = time.time() - suite_start
            report.append((name, f"FAILED: {e}", f"{duration:.2f}s"))
            print(f"✖ SUITE [{key.upper()}] FAILED ({duration:.2f}s): {e}\n")

    total_duration = time.time() - total_start

    print("\n" + "=" * 70)
    print("  KANDEZTHUTHU AI PLAYWRIGHT TEST EXECUTION REPORT")
    print("=" * 70)
    passed_count = sum(1 for _, status, _ in report if status == "PASSED")
    for name, status, dur in report:
        icon = "✅" if status == "PASSED" else "❌"
        print(f"  {icon} {name:<42} | {status:<15} | {dur}")
    print("-" * 70)
    print(f"  Total Duration: {total_duration:.2f}s | Passed: {passed_count}/{len(report)}")
    print("=" * 70 + "\n")

    if passed_count < len(report):
        sys.exit(1)

if __name__ == "__main__":
    main()
