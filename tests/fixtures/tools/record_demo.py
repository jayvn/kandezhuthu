#!/usr/bin/env python3
"""
Kandezhuthu AI - Automated Reusable Demo Video Generator

Records a high-definition, cinematic demonstration video of Kandezhuthu AI.
Features automated app orchestration, visual cursor tracking, end-to-end user
walkthrough across 10 key statutory & GIS audit capabilities, and automatic
transcoding to MP4, WebM, and animated GIF formats.

Usage:
    uv run python tests/fixtures/tools/record_demo.py
    uv run python tests/fixtures/tools/record_demo.py --port 8081 --format all --pace cinematic
    uv run python tests/fixtures/tools/record_demo.py --keep-server
"""

import argparse
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

REPO_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT))

from app.fixtures import DEMO_ENV
from app.orchestrator import AppOrchestrator

# The recorded journey uses sample deeds and presets, so the server runs in demo mode.
os.environ.update(DEMO_ENV)

DEFAULT_PORT = int(os.environ.get("PORT", "8081"))
OUTPUT_DIR = REPO_ROOT / "artifacts" / "demo_video"
RAW_RECORDINGS_DIR = OUTPUT_DIR / "raw"

CHROMIUM_PATH = (
    "/ms-playwright/chromium-1234/chrome-linux64/chrome"
    if os.path.exists("/ms-playwright/chromium-1234/chrome-linux64/chrome")
    else None
)

CURSOR_HELPER_JS = """
(() => {
  if (document.getElementById('demo-cursor')) return;
  const cursor = document.createElement('div');
  cursor.id = 'demo-cursor';
  cursor.style.position = 'fixed';
  cursor.style.zIndex = '9999999';
  cursor.style.width = '22px';
  cursor.style.height = '22px';
  cursor.style.borderRadius = '50%';
  cursor.style.backgroundColor = 'rgba(239, 68, 68, 0.75)';
  cursor.style.border = '2px solid #ffffff';
  cursor.style.boxShadow = '0 0 10px rgba(0, 0, 0, 0.45)';
  cursor.style.pointerEvents = 'none';
  cursor.style.transition = 'transform 0.12s ease-out, background-color 0.12s ease';
  cursor.style.transform = 'translate(-50%, -50%)';
  cursor.style.left = '-100px';
  cursor.style.top = '-100px';
  document.body.appendChild(cursor);

  window.addEventListener('mousemove', (e) => {
    cursor.style.left = e.clientX + 'px';
    cursor.style.top = e.clientY + 'px';
  });
  window.addEventListener('mousedown', () => {
    cursor.style.backgroundColor = 'rgba(220, 38, 38, 0.95)';
    cursor.style.transform = 'translate(-50%, -50%) scale(0.8)';
  });
  window.addEventListener('mouseup', () => {
    cursor.style.backgroundColor = 'rgba(239, 68, 68, 0.75)';
    cursor.style.transform = 'translate(-50%, -50%) scale(1.0)';
  });
})();
"""


CHAPTER_SCENES = [
    (1, "Bilingual Malayalam & English Interface", "Instant one-click language toggle with pure English mode"),
    (2, "Satellite GIS & Topographic Flood Risk", "Elevation HUD, KSDMA flood exposure & wetland detection"),
    (3, "KPBR 2019 Access Road Measurement", "Kerala Panchayat Building Rules motorable pathway compliance"),
    (4, "Cadastral Plot Boundary Demarcation", "Digital polygon sealing and calibrated cent extent calculation"),
    (5, "Physical Field Inspection Checklist", "5 non-negotiable physical checks (Survey stones, boundary encroachment)"),
    (6, "30-Year Prior Title Lineage Audit", "Automated Munnadharam trace detecting Mary Roy defect & bank mortgage"),
    (7, "Multimodal Gemini 3.8 Flash Vision OCR", "Instant extraction of deed recitals, boundaries & statutory red flags"),
    (8, "English WhatsApp Seller Inquiry Card", "Polite, attorney-grade WhatsApp draft with one-click copy"),
    (9, "Advocate Due Diligence Dossier Export", "Downloadable court-grade legal verification report (PDF)"),
    (10, "Ethical Non-AI Guardrails & Split View", "Clear boundary between document audit and ground realities"),
]


def show_chapter_banner(page, title: str, subtitle: str, step: int | None = None) -> None:
    """Injects an elegant floating banner at top-center of the viewport."""
    if step is None:
        for num, s_title, _ in CHAPTER_SCENES:
            if s_title.strip().lower() == str(title).strip().lower() or str(title).strip().lower() in s_title.strip().lower():
                step = num
                break
    if step is None:
        step = getattr(show_chapter_banner, "_counter", 1)
        show_chapter_banner._counter = step + 1

    js_code = """
    ([stepNum, titleText, subtitleText]) => {
      let banner = document.getElementById('demo-chapter-banner');
      if (!banner) {
        banner = document.createElement('div');
        banner.id = 'demo-chapter-banner';
        document.body.appendChild(banner);
      }
      banner.style.cssText = `
        position: fixed;
        top: 155px;
        right: 24px;
        left: auto;
        transform: none;
        z-index: 999999;
        background: rgba(15, 23, 42, 0.92);
        color: #ffffff;
        padding: 8px 18px;
        border-radius: 20px;
        border: 1px solid rgba(255, 255, 255, 0.15);
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.35);
        backdrop-filter: blur(10px);
        display: flex;
        align-items: center;
        gap: 10px;
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
        pointer-events: none;
        transition: opacity 0.35s ease, transform 0.35s ease;
      `;
      banner.innerHTML = `
        <span style="background:#990f3d; color:#fff; font-size:11px; font-weight:700; padding:2px 8px; border-radius:12px; white-space:nowrap; letter-spacing:0.5px;">SCENE ${stepNum}/10</span>
        <span style="font-weight:700; font-size:13px; color:#ffffff; white-space:nowrap;">${titleText}</span>
        <span style="color:#64748b; font-size:12px; user-select:none;">•</span>
        <span style="color:#94a3b8; font-size:12px; white-space:nowrap;">${subtitleText}</span>
      `;
      banner.style.opacity = '1';
    }
    """
    try:
        page.evaluate(js_code, [str(step), title, subtitle])
    except Exception as e:
        print(f"  [Notice] Chapter banner overlay notice: {e}")


class DemoVideoRecorder:
    """Orchestrates and captures a cinematic user journey through Kandezhuthu AI."""

    def __init__(
        self,
        base_url: str,
        output_dir: Path = OUTPUT_DIR,
        width: int = 1440,
        height: int = 900,
        pace: str = "cinematic",
    ):
        self.base_url = base_url
        self.output_dir = output_dir
        self.raw_dir = output_dir / "raw"
        self.width = width
        self.height = height
        self.pace = pace
        self.screenshots_dir = output_dir / "screenshots"

        # Pace multiplier
        self.multiplier = 1.0 if pace == "cinematic" else (0.6 if pace == "normal" else 0.3)

    def show_chapter_banner(self, page, title: str, subtitle: str, step: int | None = None) -> None:
        """Injects chapter/milestone toast banner overlay into the page."""
        show_chapter_banner(page, title, subtitle, step=step)

    def pause(self, seconds: float) -> None:
        """Paces the recording for human readability."""
        time.sleep(seconds * self.multiplier)

    def smooth_move_and_click(self, page, selector: str, pre_delay: float = 0.4, post_delay: float = 0.8) -> None:
        """Moves cursor smoothly towards an element before clicking."""
        try:
            loc = page.locator(selector).first
            try:
                loc.scroll_into_view_if_needed(timeout=1000)
            except Exception:
                pass
            box = loc.bounding_box()
            if box:
                target_x = box["x"] + box["width"] / 2
                target_y = box["y"] + box["height"] / 2
                page.mouse.move(target_x, target_y, steps=10)
                self.pause(pre_delay)
                page.mouse.down()
                self.pause(0.1)
                page.mouse.up()
                self.pause(post_delay)
            else:
                loc.click(force=True)
                self.pause(post_delay)
        except Exception as e:
            print(f"  [Notice] Click fallback on {selector}: {e}")
            try:
                page.locator(selector).first.click(force=True)
            except Exception:
                pass
            self.pause(post_delay)

    def record_journey(self) -> Path:
        """Executes the full automated demo script and records the session."""
        self.raw_dir.mkdir(parents=True, exist_ok=True)
        self.screenshots_dir.mkdir(parents=True, exist_ok=True)

        print("\n" + "=" * 70)
        print("  🎥 KANDEZTHUTHU AI: RECORDING HIGH-DEFINITION DEMO VIDEO")
        print(f"  Target: {self.base_url}")
        print(f"  Resolution: {self.width}x{self.height} | Pace: {self.pace.upper()}")
        print("=" * 70 + "\n")

        with sync_playwright() as p:
            browser = p.chromium.launch(
                executable_path=CHROMIUM_PATH,
                headless=True,
                args=["--no-sandbox", "--disable-dev-shm-usage", "--disable-gpu"],
            )

            context = browser.new_context(
                viewport={"width": self.width, "height": self.height},
                record_video_dir=str(self.raw_dir),
                record_video_size={"width": self.width, "height": self.height},
                permissions=["clipboard-read", "clipboard-write"],
            )

            page = context.new_page()

            # -------------------------------------------------------------
            # SCENE 1: App Header, Branding & Bilingual UI Toggle
            # -------------------------------------------------------------
            print("[Scene 1/10] Loading Application & Showcasing Malayalam Bilingual Switcher...")
            page.goto(self.base_url, wait_until="networkidle")
            page.evaluate(CURSOR_HELPER_JS)
            self.show_chapter_banner(
                page,
                "Bilingual Malayalam & English Interface",
                "Instant one-click language toggle with pure English mode",
                step=1,
            )
            self.pause(1.5)

            # Move cursor across the brand banner
            page.mouse.move(180, 45, steps=10)
            self.pause(0.8)
            page.screenshot(path=str(self.screenshots_dir / "01_brand_intro.png"))

            # Switch to Malayalam
            print("  → Toggling Language to Malayalam (മലയാളം)...")
            self.smooth_move_and_click(page, "#lang-btn-ml", pre_delay=0.3, post_delay=1.8)

            # Switch back to English for comprehensive statutory auditing
            print("  → Toggling Language back to English...")
            self.smooth_move_and_click(page, "#lang-btn-en", pre_delay=0.3, post_delay=1.0)

            # Showcase FT-styled 4-Step Progressive Disclosure Stepper Bar
            print("  → Highlighting FT-styled 4-Step Progressive Disclosure Stepper Bar...")
            for wf_step_selector in ["#wf-step-1", "#wf-step-2", "#wf-step-3", "#wf-step-4"]:
                box = page.locator(wf_step_selector).bounding_box()
                if box:
                    page.mouse.move(box["x"] + box["width"] / 2, box["y"] + box["height"] / 2, steps=6)
                    self.pause(0.25)
            self.pause(0.4)

            # -------------------------------------------------------------
            # SCENE 2: Satellite GIS Discovery & Topographic Elevation HUD
            # -------------------------------------------------------------
            print("\n[Scene 2/10] Navigating to Workflow Step 3: Satellite GIS & KPBR Survey...")
            self.smooth_move_and_click(page, "#wf-step-3", pre_delay=0.3, post_delay=1.0)
            self.show_chapter_banner(
                page,
                "Satellite GIS & Topographic Flood Risk",
                "Elevation HUD, KSDMA flood exposure & wetland detection",
                step=2,
            )
            self.pause(0.5)

            # Select Kakkanad elevated midlands preset
            print("  → Switching preset to Kakkanad (Elevated Midlands)...")
            preset_select = page.locator("#preset-select")
            preset_select.select_option("kakkanad")
            self.pause(2.0)

            # Select Kuttanad critical wetland alert preset
            print("  → Switching preset to Kuttanad (Wetland / Sub-MSL Alert)...")
            preset_select.select_option("kuttanad")
            self.pause(2.2)
            page.screenshot(path=str(self.screenshots_dir / "02_kuttanad_flood_alert.png"))

            # Switch back to Aluva for complete audit lineage
            print("  → Switching preset back to Aluva (Re-Sy 345/1)...")
            preset_select.select_option("aluva")
            self.pause(2.0)

            # Inspect elevation HUD
            hud_box = page.locator("#hud-elevation").bounding_box()
            if hud_box:
                page.mouse.move(hud_box["x"] + 50, hud_box["y"] + 20, steps=8)
                self.pause(1.2)

            # -------------------------------------------------------------
            # SCENE 3: Road Access Measurement under KPBR 2019
            # -------------------------------------------------------------
            print("\n[Scene 3/10] Measuring Access Road Width under Kerala Panchayat Building Rules...")
            self.show_chapter_banner(
                page,
                "KPBR 2019 Access Road Measurement",
                "Kerala Panchayat Building Rules motorable pathway compliance",
                step=3,
            )
            self.pause(0.5)
            self.smooth_move_and_click(page, "#tool-road", pre_delay=0.2, post_delay=0.8)

            map_box = page.locator("#map-view").bounding_box()
            if map_box:
                cx = map_box["x"] + map_box["width"] / 2
                cy = map_box["y"] + map_box["height"] / 2

                # Measure road cross-section with two distinct clicks
                page.mouse.move(cx - 35, cy + 30, steps=10)
                page.mouse.down()
                self.pause(0.1)
                page.mouse.up()
                self.pause(0.4)

                page.mouse.move(cx - 5, cy + 30, steps=8)
                page.mouse.down()
                self.pause(0.1)
                page.mouse.up()
                self.pause(1.5)
                page.screenshot(path=str(self.screenshots_dir / "03_road_measurement_kpbr.png"))

            # -------------------------------------------------------------
            # SCENE 4: Cadastral Plot Boundary Sealing & Plinth Calculation
            # -------------------------------------------------------------
            print("\n[Scene 4/10] Sealing Cadastral Plot Geometry & Area Extent...")
            self.show_chapter_banner(
                page,
                "Cadastral Plot Boundary Demarcation",
                "Digital polygon sealing and calibrated cent extent calculation",
                step=4,
            )
            self.pause(0.5)
            self.smooth_move_and_click(page, "#tool-plot", pre_delay=0.3, post_delay=0.8)

            if map_box:
                cx = map_box["x"] + map_box["width"] / 2
                cy = map_box["y"] + map_box["height"] / 2

                # Draw a clear 4-corner cadastral plot boundary
                points = [
                    (cx - 50, cy - 40),
                    (cx + 60, cy - 40),
                    (cx + 60, cy + 50),
                    (cx - 50, cy + 50),
                    (cx - 50, cy - 40),  # Close polygon
                ]
                for px, py in points:
                    page.mouse.move(px, py, steps=6)
                    page.mouse.down()
                    self.pause(0.08)
                    page.mouse.up()
                    self.pause(0.25)

                self.pause(1.8)
                page.screenshot(path=str(self.screenshots_dir / "04_cadastral_plot_sealed.png"))

            # -------------------------------------------------------------
            # SCENE 5: Physical Field Inspection Checklist Drawer
            # -------------------------------------------------------------
            print("\n[Scene 5/10] Advancing Stepper to Step 4: Due Diligence & Action...")
            self.smooth_move_and_click(page, "#btn-next-step", pre_delay=0.3, post_delay=1.0)
            self.show_chapter_banner(
                page,
                "Physical Field Inspection Checklist",
                "5 non-negotiable physical checks (Survey stones, boundary encroachment)",
                step=5,
            )
            self.pause(0.5)
            # Ensure checklist panel is open
            chk_panel = page.locator("#checklist-panel")
            if not chk_panel.is_visible():
                self.smooth_move_and_click(page, "#btn-checklist-toggle", pre_delay=0.2, post_delay=0.8)

            # Check off vital non-paper ground reality items
            for chk_id in ["#chk-kallu", "#chk-road", "#chk-wetland", "#chk-ht", "#chk-flood"]:
                try:
                    self.smooth_move_and_click(page, chk_id, pre_delay=0.15, post_delay=0.3)
                except Exception:
                    pass

            self.pause(1.5)
            page.screenshot(path=str(self.screenshots_dir / "05_field_checklist_drawer.png"))

            # Close checklist drawer
            self.smooth_move_and_click(page, "#btn-checklist-toggle", pre_delay=0.2, post_delay=0.6)

            # -------------------------------------------------------------
            # SCENE 6: 30-Year Munnadharam Prior Title Lineage Audit
            # -------------------------------------------------------------
            print("\n[Scene 6/10] Navigating Stepper to Step 2: Prior Title Lineage (*Munnadharam*)...")
            self.smooth_move_and_click(page, "#wf-step-2", pre_delay=0.4, post_delay=1.0)
            self.show_chapter_banner(
                page,
                "30-Year Prior Title Lineage Audit",
                "Automated Munnadharam trace detecting Mary Roy defect & bank mortgage",
                step=6,
            )
            self.pause(0.5)
            self.smooth_move_and_click(page, "#chip-timeline-aluva", pre_delay=0.4, post_delay=2.5)

            # Scroll through timeline in the chat pane to reveal defects
            page.locator("#chat-pane").evaluate("el => el.scrollBy({ top: 350, behavior: 'smooth' })")
            self.pause(2.0)
            page.screenshot(path=str(self.screenshots_dir / "06_lineage_defects_detected.png"))

            # Demonstrate Clean Title Chain comparison
            print("  → Comparing with 100% Clean 39-Year Lineage Chain...")
            self.smooth_move_and_click(page, "#chip-timeline-clean", pre_delay=0.4, post_delay=2.5)
            page.locator("#chat-pane").evaluate("el => el.scrollBy({ top: 300, behavior: 'smooth' })")
            self.pause(1.8)

            # -------------------------------------------------------------
            # SCENE 7: Multimodal Gemini 3.8 Flash Vision OCR
            # -------------------------------------------------------------
            print("\n[Scene 7/10] Navigating Stepper to Step 1: Document Ingest & OCR...")
            self.smooth_move_and_click(page, "#wf-step-1", pre_delay=0.4, post_delay=1.0)
            self.show_chapter_banner(
                page,
                "Multimodal Gemini 3.8 Flash Vision OCR",
                "Instant extraction of deed recitals, boundaries & statutory red flags",
                step=7,
            )
            self.pause(0.5)
            # Click the sample deed card in the quickstart grid
            deed_card = page.locator(".layman-card.card-deed").first
            if deed_card.count() > 0 and deed_card.is_visible():
                self.smooth_move_and_click(page, ".layman-card.card-deed", pre_delay=0.4, post_delay=0.8)
            else:
                self.smooth_move_and_click(page, "#chip-sample-deed", pre_delay=0.4, post_delay=0.8)

            try:
                page.wait_for_selector(".deed-audit-card", timeout=30000)
            except Exception as e:
                print(f"  [Notice] Waiting for deed card: {e}")
            self.pause(2.0)

            audit_card = page.locator(".deed-audit-card").last
            if audit_card.count() > 0:
                try:
                    audit_card.scroll_into_view_if_needed(timeout=2000)
                except Exception:
                    pass

            try:
                page.wait_for_selector(".whatsapp-card", timeout=15000)
            except Exception as e:
                print(f"  [Notice] Waiting for whatsapp card: {e}")

            # Smoothly scroll through the card so viewers can read:
            # 1) Extracted Survey & Boundaries Schedule
            boundary_el = page.locator(".boundary-box").last
            if boundary_el.count() > 0:
                try:
                    boundary_el.scroll_into_view_if_needed(timeout=2000)
                except Exception:
                    page.locator("#chat-pane").evaluate("el => el.scrollBy({ top: 250, behavior: 'smooth' })")
            else:
                page.locator("#chat-pane").evaluate("el => el.scrollBy({ top: 250, behavior: 'smooth' })")
            self.pause(2.0)

            # 2) Statutory Red Flags Detected
            findings_el = page.locator(".findings-box").last
            if findings_el.count() > 0:
                try:
                    findings_el.scroll_into_view_if_needed(timeout=2000)
                except Exception:
                    page.locator("#chat-pane").evaluate("el => el.scrollBy({ top: 250, behavior: 'smooth' })")
            else:
                page.locator("#chat-pane").evaluate("el => el.scrollBy({ top: 250, behavior: 'smooth' })")
            self.pause(2.0)

            page.screenshot(path=str(self.screenshots_dir / "07_multimodal_deed_ocr.png"))

            # -------------------------------------------------------------
            # SCENE 8: English WhatsApp Seller Inquiry Card
            # -------------------------------------------------------------
            print("\n[Scene 8/10] Advancing Stepper to Step 4: Action & WhatsApp Inquiry...")
            self.smooth_move_and_click(page, "#wf-step-4", pre_delay=0.3, post_delay=0.8)
            # Ensure checklist panel is closed if opened so chat is clear
            chk_panel = page.locator("#checklist-panel")
            if chk_panel.is_visible():
                self.smooth_move_and_click(page, "#btn-checklist-toggle", pre_delay=0.2, post_delay=0.5)

            self.show_chapter_banner(
                page,
                "English WhatsApp Seller Inquiry Card",
                "Polite, attorney-grade WhatsApp draft with one-click copy",
                step=8,
            )
            self.pause(0.5)

            # Scroll to reveal the .whatsapp-card
            page.locator("#chat-pane").evaluate("el => el.scrollBy({ top: 300, behavior: 'smooth' })")
            self.pause(1.0)
            wa_card = page.locator(".whatsapp-card").last
            if wa_card.count() > 0:
                try:
                    wa_card.scroll_into_view_if_needed(timeout=2000)
                except Exception:
                    pass

            # Smoothly move cursor to .whatsapp-card .copy-btn, click it!
            copy_btn = page.locator(".whatsapp-card .copy-btn").last
            if copy_btn.count() == 0:
                copy_btn = page.locator(".whatsapp-card button:has-text('Copy')").last

            try:
                if copy_btn.count() > 0:
                    box = copy_btn.bounding_box()
                    if box:
                        page.mouse.move(box["x"] + box["width"] / 2, box["y"] + box["height"] / 2, steps=10)
                        self.pause(0.4)
                        page.mouse.down()
                        self.pause(0.1)
                        page.mouse.up()
                    else:
                        copy_btn.click(force=True)
                else:
                    self.smooth_move_and_click(page, ".whatsapp-card .copy-btn, .copy-btn", pre_delay=0.3, post_delay=0.5)
            except Exception as e:
                print(f"  [Notice] Copy button click: {e}")

            # Pause 1.5 seconds to let the 'Copied!' feedback show on screen!
            self.pause(1.5)
            page.screenshot(path=str(self.screenshots_dir / "08_whatsapp_card_copied.png"))

            # -------------------------------------------------------------
            # SCENE 9: Advocate Legal Due Diligence Dossier Export
            # -------------------------------------------------------------
            print("\n[Scene 9/10] Triggering Advocate Title Vetting Dossier (PDF Export)...")
            self.show_chapter_banner(
                page,
                "Advocate Due Diligence Dossier Export",
                "Downloadable court-grade legal verification report (PDF)",
                step=9,
            )
            self.pause(0.5)
            export_btn = page.locator("#btn-hud-export")
            if export_btn.is_visible():
                self.smooth_move_and_click(page, "#btn-hud-export", pre_delay=0.4, post_delay=2.0)
            else:
                self.smooth_move_and_click(page, "#btn-pdf-export", pre_delay=0.4, post_delay=2.0)
            self.pause(1.5)
            page.screenshot(path=str(self.screenshots_dir / "09_dossier_exported.png"))

            # -------------------------------------------------------------
            # SCENE 10: Ethical Non-AI Guardrails & Final Overview
            # -------------------------------------------------------------
            print("\n[Scene 10/10] Ethical Non-AI Guardrail Disclaimer & Split View Finale...")
            self.show_chapter_banner(
                page,
                "Ethical Non-AI Guardrails & Split View",
                "Clear boundary between document audit and ground realities",
                step=10,
            )
            self.pause(0.5)
            # Scroll to top of chat to show clean split overview
            page.locator("#chat-pane").evaluate("el => el.scrollTo({ top: 0, behavior: 'smooth' })")
            self.pause(1.5)

            # Final smooth cursor sweep across the dual-pane UI
            page.mouse.move(self.width / 2, self.height / 2, steps=15)
            self.pause(2.0)
            page.screenshot(path=str(self.screenshots_dir / "10_final_overview.png"))

            print("  ✔ Demo user journey completed successfully.")

            # Retrieve recorded video file before closing context
            video = page.video
            context.close()
            browser.close()

            if not video:
                raise RuntimeError("Playwright video recording object was not initialized.")

            raw_path = Path(video.path())
            print(f"  ✔ Raw video recorded at: {raw_path}")
            return raw_path


def transcode_video(
    raw_webm_path: Path,
    output_dir: Path,
    stem_name: str = "kandezhuthu_demo",
    formats: str = "all",
) -> dict[str, Path]:
    """Transcodes raw Playwright WebM recording into high-quality MP4, WebM, and GIF."""
    output_dir.mkdir(parents=True, exist_ok=True)
    mp4_path = output_dir / f"{stem_name}.mp4"
    webm_path = output_dir / f"{stem_name}.webm"
    gif_path = output_dir / f"{stem_name}_preview.gif"

    print("\n" + "=" * 70)
    print("  🎞️ TRANSCODING DEMO VIDEO (FFmpeg Pipeline)")
    print("=" * 70)

    results: dict[str, Path] = {}

    # Copy clean WebM
    if formats in ["all", "webm"]:
        shutil.copy2(raw_webm_path, webm_path)
        print(f"  ✔ Saved WebM: {webm_path} ({webm_path.stat().st_size / (1024*1024):.2f} MB)")
        results["webm"] = webm_path

    # Transcode to H.264 MP4 (Universally playable in all browsers and video players)
    if formats in ["all", "mp4", "gif"]:
        print("  → Transcoding to High-Definition MP4 (H.264 / yuv420p)...")
        ffmpeg_cmd = [
            "ffmpeg",
            "-y",
            "-i",
            str(raw_webm_path),
            "-c:v",
            "libx264",
            "-preset",
            "fast",
            "-crf",
            "20",
            "-pix_fmt",
            "yuv420p",
            "-movflags",
            "+faststart",
            str(mp4_path),
        ]
        res = subprocess.run(ffmpeg_cmd, capture_output=True, text=True)
        if res.returncode != 0:
            print(f"  [Warning] FFmpeg MP4 transcoding notice: {res.stderr}")
        else:
            print(f"  ✔ Saved MP4: {mp4_path} ({mp4_path.stat().st_size / (1024*1024):.2f} MB)")
            results["mp4"] = mp4_path

    # Generate lightweight animated preview GIF for documentation / README
    if formats in ["all", "gif"]:
        print("  → Generating Animated Preview GIF (Lanczos palette)...")
        gif_cmd = [
            "ffmpeg",
            "-y",
            "-ss",
            "00:00:02",
            "-to",
            "00:00:22",
            "-i",
            str(mp4_path if mp4_path.exists() else raw_webm_path),
            "-vf",
            "fps=10,scale=720:-1:flags=lanczos,split[s0][s1];[s0]palettegen[p];[s1][p]paletteuse",
            str(gif_path),
        ]
        gif_res = subprocess.run(gif_cmd, capture_output=True, text=True)
        if gif_res.returncode == 0:
            print(f"  ✔ Saved Preview GIF: {gif_path} ({gif_path.stat().st_size / (1024*1024):.2f} MB)")
            results["gif"] = gif_path
        else:
            print(f"  [Warning] GIF generation notice: {gif_res.stderr}")

    return results


def main():
    parser = argparse.ArgumentParser(description="Kandezhuthu AI Reusable Demo Video Generator")
    parser.add_argument("--port", type=int, default=DEFAULT_PORT, help="Port to run/connect to (default: 8081)")
    parser.add_argument("--host", default="127.0.0.1", help="Host to run/connect to (default: 127.0.0.1)")
    parser.add_argument("--pace", choices=["cinematic", "normal", "fast"], default="cinematic", help="Pacing mode")
    parser.add_argument(
        "--format",
        choices=["all", "mp4", "webm", "gif"],
        default="all",
        help="Target media formats: all, mp4, webm, or gif (default: all)",
    )
    parser.add_argument("--output-dir", default=str(OUTPUT_DIR), help="Output directory for generated media")
    parser.add_argument("--keep-server", action="store_true", help="Keep the server running after video completion")

    args = parser.parse_args()
    out_dir = Path(args.output_dir)

    print("\n" + "=" * 70)
    print("  🚀 KANDEZTHUTHU AI: AUTOMATED DEMO ORCHESTRATION PIPELINE")
    print("=" * 70)

    # Step 1: Orchestrate Application
    orchestrator = AppOrchestrator(host=args.host, port=args.port, reuse_existing=True)
    orchestrator.start()

    try:
        # Step 2: Record Demo Video via Playwright
        recorder = DemoVideoRecorder(
            base_url=orchestrator.base_url,
            output_dir=out_dir,
            pace=args.pace,
        )
        raw_video_path = recorder.record_journey()

        # Step 3: Transcode to MP4, WebM, and GIF
        generated = transcode_video(raw_video_path, out_dir, formats=args.format)

        # Step 4: Summary Report
        print("\n" + "=" * 70)
        print("  🎉 DEMO VIDEO GENERATION COMPLETED SUCCESSFULLY")
        print("=" * 70)
        print(f"  📂 Output Directory: {out_dir}")
        for fmt, path in generated.items():
            if path and path.exists():
                size_mb = path.stat().st_size / (1024 * 1024)
                print(f"  📹 {fmt.upper():<5}: {path} ({size_mb:.2f} MB)")
        print(f"  🖼️ Screenshots: {recorder.screenshots_dir} (10 key milestones)")
        print("=" * 70 + "\n")

    finally:
        if not args.keep_server:
            orchestrator.stop()
        else:
            print(f"[Orchestrator] Server kept running at {orchestrator.base_url}")


if __name__ == "__main__":
    main()
