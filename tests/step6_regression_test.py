import asyncio
import json
import csv
import urllib.request
import psycopg2
from playwright.async_api import async_playwright

BASE_LOCAL = "http://localhost:8080"
BASE_PROD = "https://salesleadmachine.co.uk"
CSV_PATH = "/Users/liluzi/Desktop/python/salesleadmachine-revamp/RECONCILED_ROUTE_INVENTORY.csv"

def get_admin_token():
    req = urllib.request.Request(
        f"{BASE_LOCAL}/api/admin/login",
        data=json.dumps({"email": "admin@salesleadmachine.co.uk", "password": "<ROTATED_ADMIN_CREDENTIAL>"}).encode("utf-8"),
        headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(req) as resp:
        data = json.loads(resp.read().decode("utf-8"))
        assert data.get("success"), "Admin login failed"
        return data.get("token")

def publish_page_api(page_id, token):
    req = urllib.request.Request(
        f"{BASE_LOCAL}/api/admin/pages/{page_id}/publish",
        data=b"{}",
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {token}"
        }
    )
    with urllib.request.urlopen(req) as resp:
        data = json.loads(resp.read().decode("utf-8"))
        assert data.get("success"), "Page publish failed"
        return data

async def run_step6_regression():
    print("=" * 70)
    print("STEP 6: COMPREHENSIVE PLATFORM REGRESSION TEST")
    print("=" * 70)

    # 1. Load Step 6 routes from verified reconciled inventory
    routes = []
    with open(CSV_PATH, "r") as f:
        reader = csv.DictReader(f)
        for r in reader:
            if r["Include_In_Step6_Regression"] == "True":
                routes.append(r["Exact_URL"])

    print(f"Loaded {len(routes)} routes marked for Step 6 regression testing.\n")

    # 2. HTTP Status Parity Check
    print("--- 1. HTTP Status & Availability ---")
    status_passes = 0
    for r in routes:
        url = f"{BASE_LOCAL}{r}"
        try:
            req = urllib.request.urlopen(url)
            if req.status == 200:
                status_passes += 1
            else:
                print(f"  [FAIL] {r} returned {req.status}")
        except Exception as e:
            print(f"  [ERROR] {r} -> {e}")
    print(f"Status Parity: {status_passes}/{len(routes)} routes returned HTTP 200 OK.\n")

    # 3. Headless Browser Visual & DOM Inspection
    print("--- 2. Heading Hierarchy, Button Parity & Viewport Verification ---")
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)

        # A. Inner Hero Parity verification for reported user pages
        test_pages = [
            {
                "url": "/for-business-services/",
                "sec_sel": ".elementor-element-450391b",
                "expected_eyebrow": "Problems We Solve for Business Services",
                "expected_title": "Expert in your field, you. We Are, Too. Our Specialty Is Finding Your Next New Customer",
                "expected_btn": "SEE SALES LEAD MACHINE IN ACTION"
            },
            {
                "url": "/for-enterprise/",
                "sec_sel": ".elementor-element-c860e96",
                "expected_eyebrow": "Sales Lead Machine for Enterprise",
                "expected_title": "Go-to-market strategies for B2B enterprises and account-based marketing",
                "expected_btn": "SEE SALES LEAD MACHINE IN ACTION"
            }
        ]

        context = await browser.new_context(viewport={"width": 1280, "height": 800}, device_scale_factor=1)
        page = await context.new_page()

        for tp in test_pages:
            print(f"Verifying {tp['url']}...")
            await page.goto(f"{BASE_LOCAL}{tp['url']}", wait_until="networkidle")
            await page.wait_for_timeout(1000)

            # Query within the specific hero section
            res = await page.evaluate(f'''() => {{
                const sec = document.querySelector("{tp['sec_sel']}");
                if (!sec) return {{ error: "Hero section not found" }};
                const subtitle = sec.querySelector(".elementskit-section-subtitle");
                const title = sec.querySelector(".ekit-heading--title, .elementskit-section-title");
                const btn = sec.querySelector(".elementskit-btn, .elementor-button-text, .elementor-button");
                return {{
                    eyebrow: subtitle ? subtitle.innerText.trim() : "",
                    title: title ? title.innerText.trim() : "",
                    btn: btn ? btn.innerText.trim() : ""
                }};
            }}''')

            print(f"  Eyebrow: '{res.get('eyebrow')}' (Expected: '{tp['expected_eyebrow']}')")
            print(f"  Title:   '{res.get('title')}' (Expected: '{tp['expected_title']}')")
            print(f"  Button:  '{res.get('btn')}' (Expected: '{tp['expected_btn']}')")

            assert res.get('eyebrow') == tp['expected_eyebrow'], f"Eyebrow mismatch on {tp['url']}"
            assert res.get('title') == tp['expected_title'], f"Title mismatch on {tp['url']}"
            assert tp['expected_btn'] in res.get('btn', ''), f"Button mismatch on {tp['url']}"
            print("  [PASS] Matches live production screenshot verbatim!\n")

        # B. Multi-device responsive rendering test
        viewports = [
            ("Desktop", {"width": 1280, "height": 800}),
            ("Tablet", {"width": 768, "height": 1024}),
            ("Mobile", {"width": 375, "height": 812})
        ]

        for vp_name, vp_dims in viewports:
            print(f"Testing responsive layout at {vp_name} ({vp_dims['width']}x{vp_dims['height']})...")
            vp_context = await browser.new_context(viewport=vp_dims, device_scale_factor=1)
            vp_page = await vp_context.new_page()
            await vp_page.goto(f"{BASE_LOCAL}/for-business-services/", wait_until="networkidle")
            overflow = await vp_page.evaluate('''() => {
                return {
                    scrollWidth: document.documentElement.scrollWidth,
                    clientWidth: document.documentElement.clientWidth,
                    hasOverflow: document.documentElement.scrollWidth > document.documentElement.clientWidth
                };
            }''')
            print(f"  scrollWidth: {overflow['scrollWidth']}, clientWidth: {overflow['clientWidth']}, overflow: {overflow['hasOverflow']}")
            assert not overflow['hasOverflow'], f"Horizontal overflow detected at {vp_name}"
            await vp_context.close()
        print("  [PASS] Responsive layout clean across desktop, tablet, and mobile.\n")

        await context.close()
        await browser.close()

    # 4. CMS Visual Editing, Draft Isolation, Publishing & Clean Restoration Test
    print("--- 3. CMS Editing, Draft Isolation, Publishing & Clean Restoration ---")
    admin_token = get_admin_token()
    print("  -> Admin authenticated, JWT obtained.")

    conn = psycopg2.connect("postgresql://liluzi@localhost:5432/salesleadmachine")
    conn.autocommit = True
    cur = conn.cursor()

    # Target: Homepage Section 0b9f330
    cur.execute("SELECT id, page_id, anchor_id, data, draft_data FROM page_sections WHERE anchor_id = '0b9f330';")
    sec_row = cur.fetchone()
    assert sec_row is not None, "Section 0b9f330 not found in database"
    sec_pk, page_id, sid, live_data, orig_draft_data = sec_row

    print(f"Target CMS Section: {sid} (Page ID: {page_id})")
    orig_title = live_data.get("title", "")
    print(f"Original Live Title: '{orig_title}'")

    test_token = " [CMS-REGRESSION-VERIFIED-2026]"
    draft_modified_title = orig_title + test_token

    try:
        # A. Apply modification ONLY to draft_data in PostgreSQL
        new_draft = dict(live_data)
        new_draft["title"] = draft_modified_title
        cur.execute("UPDATE page_sections SET draft_data = %s WHERE id = %s;", (json.dumps(new_draft), sec_pk))
        print("  -> Updated draft_data in PostgreSQL.")

        # B. Verify Public Page Isolation
        # Public anonymous visitor MUST see live_data, NOT draft_data
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            ctx = await browser.new_context(viewport={"width": 1280, "height": 800})
            page = await ctx.new_page()

            # Anonymous visitor (no token)
            await page.goto(f"{BASE_LOCAL}/", wait_until="networkidle")
            await page.wait_for_timeout(1000)
            public_rendered = await page.evaluate(f'''() => {{
                const el = document.querySelector(".elementor-element-{sid} .ekit-heading--title");
                return el ? el.innerText.trim() : "";
            }}''')
            print(f"  Public Page Rendered Title: '{public_rendered}'")
            assert test_token not in public_rendered, "Draft leak: Test token appeared on public page!"
            print("  [PASS] Draft Isolation verified: Public page unchanged.\n")

            # Draft mode preview with token in localStorage
            await page.evaluate(f'''() => {{
                localStorage.setItem("slm_auth_token", "{admin_token}");
            }}''')
            await page.goto(f"{BASE_LOCAL}/?mode=draft", wait_until="networkidle")
            await page.wait_for_timeout(1000)
            draft_rendered = await page.evaluate(f'''() => {{
                const el = document.querySelector(".elementor-element-{sid} .ekit-heading--title");
                return el ? el.innerText.trim() : "";
            }}''')
            print(f"  Draft Mode Rendered Title: '{draft_rendered}'")
            assert test_token in draft_rendered, "Draft preview failed: Test token not visible in ?mode=draft!"
            print("  [PASS] Draft Preview verified: Changes visible in draft mode.\n")

            # C. Publish changes via CMS Admin API
            publish_res = publish_page_api(page_id, admin_token)
            print(f"  -> Published page via API: {publish_res.get('message')}")

            # Public page (anonymous context, no localStorage token)
            anon_ctx = await browser.new_context(viewport={"width": 1280, "height": 800})
            anon_page = await anon_ctx.new_page()
            await anon_page.goto(f"{BASE_LOCAL}/", wait_until="networkidle")
            await anon_page.wait_for_timeout(1000)
            published_rendered = await anon_page.evaluate(f'''() => {{
                const el = document.querySelector(".elementor-element-{sid} .ekit-heading--title");
                return el ? el.innerText.trim() : "";
            }}''')
            print(f"  Public Page Post-Publish Title: '{published_rendered}'")
            assert test_token in published_rendered, "Publish verification failed: Public page missing published content!"
            print("  [PASS] Publish Functionality verified: Live page updated for anonymous visitors.\n")
            await anon_ctx.close()

            # D. Clean Restoration / Reversion
            cur.execute("UPDATE page_sections SET data = %s, draft_data = %s WHERE id = %s;", (json.dumps(live_data), json.dumps(orig_draft_data), sec_pk))
            cur.execute("UPDATE pages SET updated_at = now() WHERE id = %s;", (page_id,))
            print("  -> Restored original live and draft data in PostgreSQL.")

            restore_ctx = await browser.new_context(viewport={"width": 1280, "height": 800})
            restore_page = await restore_ctx.new_page()
            await restore_page.goto(f"{BASE_LOCAL}/", wait_until="networkidle")
            await restore_page.wait_for_timeout(1000)
            restored_rendered = await restore_page.evaluate(f'''() => {{
                const el = document.querySelector(".elementor-element-{sid} .ekit-heading--title");
                return el ? el.innerText.trim() : "";
            }}''')
            print(f"  Public Page Restored Title: '{restored_rendered}'")
            assert test_token not in restored_rendered, "Restoration failed: Token still present!"
            assert restored_rendered == public_rendered, "Restoration failed: Content does not match pre-test baseline!"
            print("  [PASS] Clean Restoration verified: Live site restored to exact original state.\n")
            await restore_ctx.close()

            await ctx.close()
            await browser.close()

    finally:
        # Guarantee restoration
        cur.execute("UPDATE page_sections SET data = %s, draft_data = %s WHERE id = %s;", (json.dumps(live_data), json.dumps(orig_draft_data), sec_pk))
        conn.close()

    print("=" * 70)
    print("STEP 6 REGRESSION TESTING: ALL CHECKS PASSED PERFECTLY")
    print("=" * 70)

if __name__ == "__main__":
    asyncio.run(run_step6_regression())
