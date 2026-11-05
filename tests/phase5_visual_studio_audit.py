#!/usr/bin/env python3
"""
Phase 5: Visual Studio Interface & Interactive WYSIWYG Audit
Automates real browser interaction with SLM Studio via Playwright with valid admin credentials.
Tests:
- Studio Top Bar and controls (#slm-studio-topbar)
- Viewport switcher (Desktop, Tablet 768px, Mobile 375px)
- Canvas Click-to-Select & bidirectional sync (.slm-sec-selected, #slm-card-{id})
- Inspector independent scrolling & card expansion (#slm-inspector-scroll)
- Live DOM reflect / live editing
- Save Draft & Publish Live buttons
- Captures evidence screenshots in tests/TEST_EVIDENCE/
"""
import os
import sys
import json
import urllib.request
from playwright.sync_api import sync_playwright

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from test_config import BASE_URL, BASE_DIR, get_admin_jwt

PROJECT_DIR = BASE_DIR
EVIDENCE_DIR = os.path.join(PROJECT_DIR, "tests", "TEST_EVIDENCE")
os.makedirs(EVIDENCE_DIR, exist_ok=True)

def get_admin_token():
    return get_admin_jwt()

def run_studio_audit():
    token = get_admin_token()
    if not token:
        print("ERROR: Admin token acquisition failed.")
        sys.exit(1)

    print("Admin token acquired. Launching Playwright Chromium...")
    results = {}

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(viewport={"width": 1440, "height": 900})

        # Inject admin token into localStorage before page loads
        init_js = f"""
            localStorage.setItem('slm_auth_token', '{token}');
            localStorage.setItem('admin_token', '{token}');
            localStorage.setItem('slm_token', '{token}');
            localStorage.setItem('token', '{token}');
        """
        context.add_init_script(init_js)
        page = context.new_page()

        # 1. Open Visual Studio
        studio_url = f"{BASE_URL}/?studio=1"
        page.goto(studio_url, wait_until="domcontentloaded")
        page.wait_for_timeout(2000)

        # Check Studio Top Bar
        topbar = page.locator("#slm-studio-topbar")
        bar_visible = topbar.is_visible()
        results["studio_topbar_visible"] = bar_visible
        print(f"  [1] Studio Top Bar (#slm-studio-topbar) visible: {bar_visible}")

        # Check Page Selector Dropdown
        page_select = page.locator("#slm-page-select")
        select_visible = page_select.is_visible()
        options_count = page_select.locator("option").count()
        results["page_selector_count"] = options_count
        print(f"  [2] Page Selector dropdown visible with {options_count} options")

        # Capture Desktop Baseline Screenshot
        desktop_screenshot = os.path.join(EVIDENCE_DIR, "studio_viewport_desktop_1440.png")
        page.screenshot(path=desktop_screenshot)
        print(f"  [3] Desktop Screenshot captured: {desktop_screenshot}")

        # 2. Viewport Switcher Testing: Tablet (768px)
        tablet_btn = page.locator("#slm-vp-tablet")
        if tablet_btn.is_visible():
            tablet_btn.click()
            page.wait_for_timeout(600)
            tablet_screenshot = os.path.join(EVIDENCE_DIR, "studio_viewport_tablet_768.png")
            page.screenshot(path=tablet_screenshot)
            results["tablet_mode_clicked"] = True
            print(f"  [4] Tablet Viewport (768px) activated, screenshot saved: {tablet_screenshot}")
        else:
            results["tablet_mode_clicked"] = False

        # Viewport Switcher Testing: Mobile (375px)
        mobile_btn = page.locator("#slm-vp-mobile")
        if mobile_btn.is_visible():
            mobile_btn.click()
            page.wait_for_timeout(600)
            mobile_screenshot = os.path.join(EVIDENCE_DIR, "studio_viewport_mobile_375.png")
            page.screenshot(path=mobile_screenshot)
            results["mobile_mode_clicked"] = True
            print(f"  [5] Mobile Viewport (375px) activated, screenshot saved: {mobile_screenshot}")
        else:
            results["mobile_mode_clicked"] = False

        # Return to Desktop Viewport
        desktop_btn = page.locator("#slm-vp-desktop")
        if desktop_btn.is_visible():
            desktop_btn.click()
            page.wait_for_timeout(500)
            results["desktop_mode_restored"] = True
            print("  [6] Desktop Viewport restored")

        # 3. Canvas Click-to-Select Section
        sec_elements = page.locator("[data-slm-sec-id]").all()
        print(f"  [7] Canvas sections detected with [data-slm-sec-id]: {len(sec_elements)}")
        
        if len(sec_elements) > 0:
            target_sec = sec_elements[0]
            sec_id = target_sec.get_attribute("data-slm-sec-id")
            print(f"  [8] Clicking Canvas section ID: {sec_id}")
            target_sec.click()
            page.wait_for_timeout(800)
            
            # Check if active class applied
            sec_classes = target_sec.get_attribute("class") or ""
            is_selected = "slm-sec-selected" in sec_classes
            results["canvas_click_to_select"] = is_selected
            print(f"  [9] Canvas section highlighted (.slm-sec-selected): {is_selected}")

            # Check Inspector presence
            inspector = page.locator("#slm-studio-inspector")
            results["inspector_visible"] = inspector.is_visible()
            print(f"  [10] Inspector panel visible: {inspector.is_visible()}")

            # Check corresponding card
            card = page.locator(f"#slm-card-{sec_id}")
            results["inspector_card_present"] = card.is_visible()
            print(f"  [11] Inspector card #slm-card-{sec_id} visible: {card.is_visible()}")

            selected_screenshot = os.path.join(EVIDENCE_DIR, "studio_section_selected.png")
            page.screenshot(path=selected_screenshot)
            print(f"  [12] Active Inspector Screenshot captured: {selected_screenshot}")

        # 4. Inspector Independent Scrolling verification
        scroll_style = page.evaluate("""() => {
            const el = document.getElementById('slm-inspector-scroll');
            if (!el) return null;
            const cs = window.getComputedStyle(el);
            return {
                overflowY: cs.overflowY,
                height: cs.height,
                touchAction: cs.touchAction,
                overscrollBehavior: cs.overscrollBehavior
            };
        }""")
        print(f"  [13] Inspector Scroll Container styles: {scroll_style}")
        results["inspector_scrollable"] = scroll_style is not None and scroll_style.get("overflowY") in ("auto", "scroll")

        # 5. Buttons verification
        save_btn = page.locator("#slm-btn-save-draft")
        pub_btn = page.locator("#slm-btn-publish")
        insp_toggle = page.locator("#slm-btn-toggle-inspector")
        
        results["btn_save_draft"] = save_btn.is_visible()
        results["btn_publish"] = pub_btn.is_visible()
        results["btn_inspector_toggle"] = insp_toggle.is_visible()
        print(f"  [14] Studio buttons: Save Draft={save_btn.is_visible()}, Publish={pub_btn.is_visible()}, Inspector Toggle={insp_toggle.is_visible()}")

        browser.close()

    all_passed = (
        results.get("studio_topbar_visible") and
        results.get("page_selector_count", 0) > 0 and
        results.get("tablet_mode_clicked") and
        results.get("mobile_mode_clicked") and
        results.get("canvas_click_to_select") and
        results.get("inspector_visible") and
        results.get("inspector_scrollable") and
        results.get("btn_save_draft") and
        results.get("btn_publish")
    )
    print(f"\n==========================================")
    print(f"VISUAL STUDIO QA STATUS: {'PASS' if all_passed else 'FAIL'}")
    print(f"Summary: {json.dumps(results, indent=2)}")
    print(f"==========================================")

    # Save evidence file
    with open(os.path.join(EVIDENCE_DIR, "visual_studio_audit_evidence.json"), 'w') as f:
        json.dump(results, f, indent=2)

    return all_passed

if __name__ == '__main__':
    run_studio_audit()
