import os, sys, json, csv, time, urllib.request
from playwright.sync_api import sync_playwright
import psycopg2

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from test_config import BASE_URL, BASE_DIR, get_admin_jwt, get_db_connection

EVIDENCE_DIR = os.path.join(BASE_DIR, "tests", "TEST_EVIDENCE")
CSV_PATH = os.path.join(BASE_DIR, "SECTION_MAPPING_AUDIT.csv")

# 1. Authenticate to get valid Admin JWT
token = get_admin_jwt()

# 2. Connect to PostgreSQL
conn = get_db_connection()
cur = conn.cursor()

cur.execute("SELECT id, slug, full_path, title FROM pages ORDER BY sort_order ASC, title ASC;")
pages = cur.fetchall()

mapping_records = []
total_sections_checked = 0
mapping_failures = 0

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    context = browser.new_context(viewport={"width": 1400, "height": 900})
    page = context.new_page()

    # Pre-set localStorage with valid auth token
    page.goto(f"{BASE_URL}/admin/")
    page.evaluate(f"localStorage.setItem('slm_auth_token', '{token}')")

    for p_idx, (p_id, slug, full_path, p_title) in enumerate(pages):
        clean_path = full_path if full_path.startswith("/") else f"/{full_path}"
        if not clean_path.endswith("/") and clean_path != "/":
            clean_path = f"{clean_path}/"
        
        studio_url = f"{BASE_URL}{clean_path}?studio=true"

        # Fetch DB sections for this page
        cur.execute("""
            SELECT id, section_type, label, anchor_id, sort_order, data
            FROM page_sections
            WHERE page_id = %s
            ORDER BY sort_order ASC;
        """, (p_id,))
        db_sections = cur.fetchall()

        try:
            page.goto(studio_url, wait_until="domcontentloaded", timeout=8000)
            page.wait_for_timeout(400)
            # Check if Studio topbar loaded
            has_topbar = page.locator("#slm-studio-topbar").is_visible()
            has_inspector = page.locator("#slm-studio-inspector").is_visible()
        except Exception as e:
            has_topbar = False
            has_inspector = False

        print(f"\n[{p_idx+1}/{len(pages)}] Page '{p_title}' ({clean_path}) -> Studio Topbar: {has_topbar}, Inspector: {has_inspector}, DB Sections: {len(db_sections)}")

        # Check mapping of each section
        for s_idx, (s_id, s_type, s_label, s_anchor, s_order, s_data) in enumerate(db_sections):
            total_sections_checked += 1
            sec_id_str = str(s_id)
            
            # Check Canvas element tagged by cms-hydrate.js
            canvas_el = page.locator(f'[data-slm-sec-id="{sec_id_str}"]')
            canvas_found = canvas_el.count() > 0
            
            # Check Inspector Card
            card_el = page.locator(f"#slm-card-{sec_id_str}")
            card_found = card_el.count() > 0

            # Test Click-to-Select
            click_success = False
            is_selected = False
            if canvas_found and card_found:
                try:
                    canvas_el.first.click(timeout=1500)
                    page.wait_for_timeout(100)
                    is_selected = "slm-sec-selected" in (canvas_el.first.get_attribute("class") or "")
                    body_el = page.locator(f"#slm-body-{sec_id_str}")
                    click_success = is_selected or body_el.is_visible()
                except Exception as ex:
                    click_success = False

            # Verify Anchor ID consistency
            actual_dom_data_id = canvas_el.first.get_attribute("data-id") if canvas_found else ""
            anchor_match = (actual_dom_data_id == s_anchor) if s_anchor else True

            status = "PASS"
            failure_reason = ""
            if not canvas_found:
                status = "FAIL"
                failure_reason = "Section element not found on Canvas"
                mapping_failures += 1
            elif not card_found:
                status = "FAIL"
                failure_reason = "Section editor card not found in Inspector"
                mapping_failures += 1
            elif not click_success:
                status = "WARNING"
                failure_reason = "Click-to-Select did not activate card visually"

            rec = {
                "Page_Title": p_title,
                "Page_Path": clean_path,
                "Section_Order": s_order,
                "Section_Label": s_label or s_type,
                "Section_Type": s_type,
                "Section_UUID": sec_id_str,
                "DB_Anchor_ID": s_anchor or "",
                "DOM_Data_ID": actual_dom_data_id or "",
                "Canvas_Found": "YES" if canvas_found else "NO",
                "Inspector_Found": "YES" if card_found else "NO",
                "Click_Selectable": "YES" if click_success else "NO",
                "Mapping_Status": status,
                "Notes": failure_reason
            }
            mapping_records.append(rec)
            print(f"   Sec #{s_order} [{s_type}] '{s_label}' -> Canvas: {rec['Canvas_Found']}, Insp: {rec['Inspector_Found']}, AnchorMatch: {anchor_match} -> {status}")

    browser.close()

conn.close()

# Write to CSV
with open(CSV_PATH, "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=[
        "Page_Title", "Page_Path", "Section_Order", "Section_Label", "Section_Type",
        "Section_UUID", "DB_Anchor_ID", "DOM_Data_ID", "Canvas_Found", "Inspector_Found",
        "Click_Selectable", "Mapping_Status", "Notes"
    ])
    writer.writeheader()
    writer.writerows(mapping_records)

print(f"\nPhase 2 Complete! Total sections mapped: {total_sections_checked}, Failures: {mapping_failures}. Saved to {CSV_PATH}")
