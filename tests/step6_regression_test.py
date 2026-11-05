import os
import sys
import asyncio
import json
import csv
import urllib.request
import urllib.error
from playwright.async_api import async_playwright

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from test_config import BASE_URL, BASE_DIR, get_admin_jwt, get_db_connection

CSV_PATH = os.path.join(BASE_DIR, "RECONCILED_ROUTE_INVENTORY.csv")

def publish_page_api(page_id, token):
    req = urllib.request.Request(
        f"{BASE_URL}/api/admin/pages/{page_id}/publish",
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
    print("STEP 6: COMPREHENSIVE PLATFORM REGRESSION TEST (STRICT ENFORCEMENT)")
    print("=" * 70)

    # 1. Load Step 6 routes from verified reconciled inventory
    routes = []
    with open(CSV_PATH, "r") as f:
        reader = csv.DictReader(f)
        for r in reader:
            if r["Include_In_Step6_Regression"] == "True":
                routes.append(r["Exact_URL"])

    print(f"Loaded {len(routes)} routes marked for Step 6 regression testing.\n")
    assert len(routes) == 38, f"Expected 38 routes in Step 6 regression, found {len(routes)}"

    # 2. HTTP Status Parity Check (Fail immediately if even one route fails)
    print("--- 1. HTTP Status & Availability (38 Routes) ---")
    route_status_records = {}
    for r in routes:
        url = f"{BASE_URL}{r}"
        try:
            req = urllib.request.urlopen(url)
            status = req.status
            route_status_records[r] = status
        except urllib.error.HTTPError as e:
            route_status_records[r] = e.code
            raise AssertionError(f"Expected route '{r}' failed with HTTP {e.code} (expected 200)")
        except Exception as e:
            route_status_records[r] = "ERR"
            raise AssertionError(f"Expected route '{r}' raised exception: {e}")

        # Strict requirement: every expected route must return HTTP 200
        assert route_status_records[r] == 200, f"Route '{r}' returned {route_status_records[r]}, expected 200"

    print(f"Status Parity: All {len(routes)}/{len(routes)} routes verified at HTTP 200 OK.")

    # 3. Genuine HTTP 404 & Soft-404 Prevention Check
    print("\n--- 2. Genuine HTTP 404 Verification (Anti-Soft-404) ---")
    unexpected_routes = [
        "/this-page-does-not-exist-at-all-404/",
        "/random-invalid-page-xyz",
        "/api/nonexistent-endpoint",
        "/company-nonexistent-subpage"
    ]
    for unexp in unexpected_routes:
        unexp_url = f"{BASE_URL}{unexp}"
        try:
            resp = urllib.request.urlopen(unexp_url)
            raise AssertionError(f"Security/Routing Violation: Unexpected route '{unexp}' returned HTTP {resp.status} instead of 404!")
        except urllib.error.HTTPError as e:
            assert e.code == 404, f"Route '{unexp}' returned HTTP {e.code}, expected 404"
            body = e.read().decode('utf-8', errors='ignore')
            # Verify body is not the homepage HTML masquerading as 404
            assert "Sales Lead Machine" not in body or "API endpoint not found" in body or "Not Found" in body, \
                f"Soft-404 detected on '{unexp}': Served homepage content on error route!"
            print(f"  [PASS] Unexpected route '{unexp}' returned genuine HTTP 404.")

    # 4. Headless Browser Visual & DOM Inspection
    print("\n--- 3. Heading Hierarchy, Button Parity & Viewport Verification ---")
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)

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
            await page.goto(f"{BASE_URL}{tp['url']}", wait_until="networkidle")
            await page.wait_for_timeout(1000)

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

            assert res.get('eyebrow') == tp['expected_eyebrow'], f"Eyebrow mismatch on {tp['url']}"
            assert res.get('title') == tp['expected_title'], f"Title mismatch on {tp['url']}"
            assert tp['expected_btn'] in res.get('btn', ''), f"Button mismatch on {tp['url']}"
            print("  [PASS] Matches live production screenshot verbatim!")

        # Multi-device responsive rendering test
        viewports = [
            ("Desktop", {"width": 1280, "height": 800}),
            ("Tablet", {"width": 768, "height": 1024}),
            ("Mobile", {"width": 375, "height": 812})
        ]

        for vp_name, vp_dims in viewports:
            vp_context = await browser.new_context(viewport=vp_dims, device_scale_factor=1)
            vp_page = await vp_context.new_page()
            await vp_page.goto(f"{BASE_URL}/for-business-services/", wait_until="networkidle")
            overflow = await vp_page.evaluate('''() => {
                return {
                    scrollWidth: document.documentElement.scrollWidth,
                    clientWidth: document.documentElement.clientWidth,
                    hasOverflow: document.documentElement.scrollWidth > document.documentElement.clientWidth
                };
            }''')
            assert not overflow['hasOverflow'], f"Horizontal overflow detected at {vp_name}"
            await vp_context.close()
        print("  [PASS] Responsive layout clean across desktop, tablet, and mobile.\n")

        await context.close()
        await browser.close()

    # 5. CMS Editing, Draft Isolation, Publishing & Clean Restoration Test
    print("--- 4. CMS Lifecycle & Guaranteed Clean Restoration ---")
    admin_token = get_admin_jwt()
    print("  -> Admin authenticated via environment credentials, JWT obtained.")

    conn = get_db_connection()
    conn.autocommit = True
    cur = conn.cursor()

    cur.execute("SELECT id, page_id, anchor_id, data, draft_data FROM page_sections WHERE anchor_id = '0b9f330';")
    sec_row = cur.fetchone()
    assert sec_row is not None, "Section 0b9f330 not found in database"
    sec_pk, page_id, sid, live_data, orig_draft_data = sec_row

    orig_title = live_data.get("title", "")
    test_token = " [CMS-REGRESSION-VERIFIED-2026]"
    draft_modified_title = orig_title + test_token

    try:
        # A. Apply modification ONLY to draft_data in PostgreSQL
        new_draft = dict(live_data)
        new_draft["title"] = draft_modified_title
        cur.execute("UPDATE page_sections SET draft_data = %s WHERE id = %s;", (json.dumps(new_draft), sec_pk))

        # B. Verify Public Page Isolation
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            ctx = await browser.new_context(viewport={"width": 1280, "height": 800})
            page = await ctx.new_page()

            # Anonymous visitor (no token)
            await page.goto(f"{BASE_URL}/", wait_until="networkidle")
            await page.wait_for_timeout(1000)
            public_rendered = await page.evaluate(f'''() => {{
                const el = document.querySelector(".elementor-element-{sid} .ekit-heading--title");
                return el ? el.innerText.trim() : "";
            }}''')
            assert test_token not in public_rendered, "Draft leak: Test token appeared on public page!"
            print("  [PASS] Draft Isolation verified: Public page unchanged.")

            # Draft mode preview with token in localStorage
            await page.evaluate(f'''() => {{
                localStorage.setItem("slm_auth_token", "{admin_token}");
            }}''')
            await page.goto(f"{BASE_URL}/?mode=draft", wait_until="networkidle")
            await page.wait_for_timeout(1000)
            draft_rendered = await page.evaluate(f'''() => {{
                const el = document.querySelector(".elementor-element-{sid} .ekit-heading--title");
                return el ? el.innerText.trim() : "";
            }}''')
            assert test_token in draft_rendered, "Draft preview failed: Test token not visible in ?mode=draft!"
            print("  [PASS] Draft Preview verified: Changes visible in draft mode.")

            # C. Publish changes via CMS Admin API
            publish_res = publish_page_api(page_id, admin_token)

            # Public page (anonymous context, no localStorage token)
            anon_ctx = await browser.new_context(viewport={"width": 1280, "height": 800})
            anon_page = await anon_ctx.new_page()
            await anon_page.goto(f"{BASE_URL}/", wait_until="networkidle")
            await anon_page.wait_for_timeout(1000)
            published_rendered = await anon_page.evaluate(f'''() => {{
                const el = document.querySelector(".elementor-element-{sid} .ekit-heading--title");
                return el ? el.innerText.trim() : "";
            }}''')
            assert test_token in published_rendered, "Publish verification failed: Public page missing published content!"
            print("  [PASS] Publish Functionality verified: Live page updated for anonymous visitors.")
            await anon_ctx.close()

            await ctx.close()
            await browser.close()

    finally:
        # Strict requirement: Guaranteed restoration even if intermediate test fails
        cur.execute(
            "UPDATE page_sections SET data = %s, draft_data = %s WHERE id = %s;",
            (json.dumps(live_data), json.dumps(orig_draft_data), sec_pk)
        )
        cur.execute("UPDATE pages SET updated_at = now() WHERE id = %s;", (page_id,))
        conn.close()

        # Verify restoration on public page
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            ctx = await browser.new_context(viewport={"width": 1280, "height": 800})
            page = await ctx.new_page()
            await page.goto(f"{BASE_URL}/", wait_until="networkidle")
            await page.wait_for_timeout(1000)
            restored_rendered = await page.evaluate(f'''() => {{
                const el = document.querySelector(".elementor-element-{sid} .ekit-heading--title");
                return el ? el.innerText.trim() : "";
            }}''')
            assert test_token not in restored_rendered, "Restoration failed: Token still present!"
            assert restored_rendered == public_rendered, "Restoration failed: Content does not match pre-test baseline!"
            print("  [PASS] Clean Restoration verified: Live site restored to exact original state.")
            await ctx.close()
            await browser.close()

    print("=" * 70)
    print("STEP 6 REGRESSION TESTING: ALL CHECKS PASSED PERFECTLY")
    print("=" * 70)

if __name__ == "__main__":
    asyncio.run(run_step6_regression())
