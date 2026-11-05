import os, sys, json, csv, time, urllib.request
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright
import psycopg2

BASE_URL = "http://localhost:8080"
EVIDENCE_DIR = "/Users/liluzi/Desktop/python/salesleadmachine-revamp/tests/TEST_EVIDENCE"
CSV_PATH = "/Users/liluzi/Desktop/python/salesleadmachine-revamp/PAGE_BY_PAGE_AUDIT.csv"

# 1. Discover all routes from PostgreSQL pages table
conn = psycopg2.connect(dbname="salesleadmachine", user="liluzi", host="127.0.0.1", port=5432)
cur = conn.cursor()
cur.execute("SELECT id, slug, full_path, title, page_type, status FROM pages ORDER BY sort_order ASC, title ASC;")
db_pages = cur.fetchall()

# Discover HTML files on disk
html_files = [f for f in os.listdir("/Users/liluzi/Desktop/python/salesleadmachine-revamp") if f.endswith(".html") and f != "admin.html"]

routes_to_test = []
seen_paths = set()

for row in db_pages:
    pid, slug, full_path, title, page_type, status = row
    p = full_path if full_path.startswith("/") else f"/{full_path}"
    if not p.endswith("/") and p != "/":
        p = f"{p}/"
    if p not in seen_paths:
        seen_paths.add(p)
        routes_to_test.append({
            "path": p,
            "title": title,
            "page_id": str(pid),
            "slug": slug,
            "source": "db_pages"
        })

# Add any aliases / additional discovered routes
extra_candidates = [
    "/service-categories/prospector/",
    "/service-categories/data-enrichment/",
    "/service-categories/email-verification/",
    "/service-categories/crome-extension/",
    "/service-categories/technographics/",
    "/service-categories/intent-data/",
    "/privacy/",
    "/terms/"
]
for ep in extra_candidates:
    if ep not in seen_paths:
        seen_paths.add(ep)
        routes_to_test.append({
            "path": ep,
            "title": ep.strip("/"),
            "page_id": "",
            "slug": ep.strip("/"),
            "source": "discovered_alias"
        })

print(f"Total discovered routes to audit: {len(routes_to_test)}")

inventory_results = []

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    context = browser.new_context(viewport={"width": 1280, "height": 800})
    page = context.new_page()

    for idx, r in enumerate(routes_to_test):
        path = r["path"]
        url = f"{BASE_URL}{path}"
        t0 = time.time()
        status_code = None
        error_msg = ""
        try:
            resp = page.goto(url, wait_until="domcontentloaded", timeout=10000)
            page.wait_for_timeout(300)
            status_code = resp.status if resp else 200
            load_time_ms = round((time.time() - t0) * 1000, 2)
        except Exception as e:
            status_code = 0
            load_time_ms = round((time.time() - t0) * 1000, 2)
            error_msg = str(e)

        actual_title = page.title()
        
        # Scroll top to bottom
        page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        page.wait_for_timeout(300)
        page.evaluate("window.scrollTo(0, 0)")
        page.wait_for_timeout(200)

        # Screenshot for visual baseline
        safe_name = path.replace("/", "_").strip("_") or "home"
        screenshot_path = os.path.join(EVIDENCE_DIR, f"page_{safe_name}.png")
        page.screenshot(path=screenshot_path, full_page=False)

        # Inspect DOM sections
        content_html = page.content()
        soup = BeautifulSoup(content_html, "html.parser")
        page_root = soup.find("div", {"data-elementor-type": "wp-page"}) or soup.find(class_="elementor-2911") or soup.find("main") or soup.body
        top_sections = page_root.find_all(lambda tag: tag.name == "section" and "elementor-top-section" in tag.get("class", [])) if page_root else []

        section_summary = []
        for s_idx, sec in enumerate(top_sections):
            data_id = sec.get("data-id") or "no-id"
            h = sec.find(["h1", "h2", "h3", "h4"])
            heading_txt = (h.get_text(strip=True)[:50] if h else "No heading").replace(",", ";")
            section_summary.append(f"#{s_idx+1}[{data_id}:{heading_txt}]")

        has_hydrate = "cms-hydrate.js" in content_html
        has_form_bridge = "form-bridge.js" in content_html

        rec = {
            "Route": path,
            "HTTP_Status": status_code,
            "Load_Time_ms": load_time_ms,
            "Page_Title": actual_title.replace(",", ";"),
            "Section_Count": len(top_sections),
            "Sections_List": " | ".join(section_summary),
            "Has_CMS_Hydrate": "YES" if has_hydrate else "NO",
            "Has_Form_Bridge": "YES" if has_form_bridge else "NO",
            "Screenshot": os.path.basename(screenshot_path),
            "Audit_Status": "PASS" if status_code == 200 and len(top_sections) > 0 and has_hydrate else "FAIL"
        }
        inventory_results.append(rec)
        print(f"[{idx+1}/{len(routes_to_test)}] {path} -> HTTP {status_code} ({load_time_ms}ms) | {len(top_sections)} sections | Hydrate: {rec['Has_CMS_Hydrate']} | {rec['Audit_Status']}")

    browser.close()

conn.close()

# Write to CSV
with open(CSV_PATH, "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=[
        "Route", "HTTP_Status", "Load_Time_ms", "Page_Title", "Section_Count",
        "Sections_List", "Has_CMS_Hydrate", "Has_Form_Bridge", "Screenshot", "Audit_Status"
    ])
    writer.writeheader()
    writer.writerows(inventory_results)

print(f"\nPhase 1 Complete! Total pages inventoried: {len(inventory_results)}. Saved to {CSV_PATH}")
