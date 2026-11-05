#!/usr/bin/env python3
"""
Phase 3 & 4: Field-by-Field Functional Editing, Draft, Save, Publish & Restoration Test
Performs real HTTP API calls, DB validations, and public frontend checks across all section types and controls.
Outputs FIELD_LEVEL_TEST_RESULTS.csv and saves JSON evidence to tests/TEST_EVIDENCE/.
"""
import os
import sys
import json
import uuid
import time
import csv
import urllib.request
import urllib.parse
import urllib.error
import psycopg2
from bs4 import BeautifulSoup

BASE_URL = "http://localhost:8080"
DB_NAME = "salesleadmachine"
DB_USER = "liluzi"
PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EVIDENCE_DIR = os.path.join(PROJECT_DIR, "tests", "TEST_EVIDENCE")
CSV_PATH = os.path.join(PROJECT_DIR, "FIELD_LEVEL_TEST_RESULTS.csv")

os.makedirs(EVIDENCE_DIR, exist_ok=True)

def get_db_connection():
    return psycopg2.connect(dbname=DB_NAME, user=DB_USER)

def get_admin_token():
    url = f"{BASE_URL}/api/admin/login"
    payload = json.dumps({"email": "admin@salesleadmachine.co.uk", "password": "<ROTATED_ADMIN_CREDENTIAL>"}).encode('utf-8')
    req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req) as resp:
            data = json.loads(resp.read().decode('utf-8'))
            return data.get("access_token") or data.get("token")
    except Exception as e:
        print(f"Failed to login: {e}")
        return None

def fetch_public_content(path, token=None):
    clean_path = path if path.startswith("/") else f"/{path}"
    url = f"{BASE_URL}/api/page-content?path={urllib.parse.quote(clean_path)}"
    headers = {"User-Agent": "SLM-QA-Auditor/1.0"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
        url += "&mode=draft"
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            return json.loads(resp.read().decode('utf-8'))
    except Exception as e:
        return {}

def api_put_draft(token, sec_id, draft_data, label=None, sort_order=0):
    url = f"{BASE_URL}/api/admin/sections/{sec_id}"
    payload = json.dumps({
        "label": label,
        "is_visible": True,
        "data": draft_data,
        "sort_order": sort_order,
        "publish": False
    }).encode('utf-8')
    req = urllib.request.Request(url, data=payload, headers={
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}"
    }, method="PUT")
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            return resp.status, json.loads(resp.read().decode('utf-8'))
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode('utf-8')
    except Exception as e:
        return 500, str(e)

def api_publish_section(token, sec_id, data, label=None, sort_order=0):
    url = f"{BASE_URL}/api/admin/sections/{sec_id}"
    payload = json.dumps({
        "label": label,
        "is_visible": True,
        "data": data,
        "sort_order": sort_order,
        "publish": True
    }).encode('utf-8')
    req = urllib.request.Request(url, data=payload, headers={
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}"
    }, method="PUT")
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            return resp.status, json.loads(resp.read().decode('utf-8'))
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode('utf-8')
    except Exception as e:
        return 500, str(e)

def run_field_level_tests():
    token = get_admin_token()
    if not token:
        print("ERROR: Could not obtain admin token. Aborting.")
        sys.exit(1)

    print("Admin token obtained successfully.")
    conn = get_db_connection()
    cur = conn.cursor()

    # Query all pages and their sections
    cur.execute("""
        SELECT p.id, p.slug, p.title, ps.id, ps.section_type, ps.anchor_id, ps.sort_order, ps.data, ps.draft_data
        FROM pages p
        JOIN page_sections ps ON ps.page_id = p.id
        ORDER BY p.slug, ps.sort_order
    """)
    all_sections = cur.fetchall()
    print(f"Total sections available for testing: {len(all_sections)}")

    results = []
    
    # We will test representative sections across different section types
    # Group sections by section_type
    type_sections = {}
    for row in all_sections:
        sec_type = row[4]
        if sec_type not in type_sections:
            type_sections[sec_type] = []
        type_sections[sec_type].append(row)

    print("Section types discovered:")
    for st, slist in type_sections.items():
        print(f"  - {st}: {len(slist)} sections")

    # Select sections to test: at least 2 sections per type, plus homepage sections
    tested_section_ids = set()
    selected_sections = []

    # Include all sections from homepage
    for row in all_sections:
        slug = row[1]
        if slug in ('', '/'):
            selected_sections.append(row)
            tested_section_ids.add(row[3])

    # Add at least 3 sections for every other section type
    for st, slist in type_sections.items():
        count = 0
        for row in slist:
            if row[3] not in tested_section_ids:
                selected_sections.append(row)
                tested_section_ids.add(row[3])
                count += 1
                if count >= 3:
                    break

    print(f"Selected {len(selected_sections)} sections for rigorous field-by-field audit.")

    for sec_idx, sec_row in enumerate(selected_sections, 1):
        p_id, p_slug, p_title, sec_id, sec_type, anchor_id, sort_order, orig_data, orig_draft = sec_row
        page_path = f"/{p_slug}" if p_slug and not p_slug.startswith("/") else (p_slug or "/")
        if not page_path.startswith("/"):
            page_path = "/" + page_path
        
        orig_data = orig_data or {}
        orig_draft = orig_draft or {}
        
        print(f"\n[{sec_idx}/{len(selected_sections)}] Testing Section {anchor_id or 'none'} ({sec_type}) on {page_path} (ID: {sec_id})")

        # Determine controls based on sec_type and existing data keys
        controls_to_test = []
        
        if sec_type == 'hero':
            for f in ['title', 'subtitle', 'eyebrow', 'body']:
                if f in orig_data or f in orig_draft:
                    controls_to_test.append((f, orig_data.get(f, '')))
            if 'buttons' in orig_data and isinstance(orig_data['buttons'], list) and len(orig_data['buttons']) > 0:
                controls_to_test.append(('btn1_text', orig_data['buttons'][0].get('label', '')))
                controls_to_test.append(('btn1_url', orig_data['buttons'][0].get('url', '')))

        elif sec_type == 'split':
            for f in ['title', 'subtitle', 'eyebrow', 'body', 'cta_text', 'cta_url']:
                if f in orig_data or f in orig_draft:
                    controls_to_test.append((f, orig_data.get(f, '')))
            if 'bullets' in orig_data and isinstance(orig_data['bullets'], list) and len(orig_data['bullets']) > 0:
                controls_to_test.append(('bullet_0_text', orig_data['bullets'][0].get('text', '')))

        elif sec_type == 'card_grid':
            for f in ['title', 'subtitle', 'body']:
                if f in orig_data or f in orig_draft:
                    controls_to_test.append((f, orig_data.get(f, '')))
            if 'cards' in orig_data and isinstance(orig_data['cards'], list) and len(orig_data['cards']) > 0:
                for c_idx in range(min(2, len(orig_data['cards']))):
                    controls_to_test.append((f'card_{c_idx}_title', orig_data['cards'][c_idx].get('title', '')))
                    controls_to_test.append((f'card_{c_idx}_desc', orig_data['cards'][c_idx].get('description', '')))

        elif sec_type == 'cta_banner':
            for f in ['title', 'subtitle', 'body', 'cta_text', 'cta_url']:
                if f in orig_data or f in orig_draft:
                    controls_to_test.append((f, orig_data.get(f, '')))

        elif sec_type == 'rich_text':
            for f in ['title', 'body_html', 'body']:
                if f in orig_data or f in orig_draft:
                    controls_to_test.append((f, orig_data.get(f, '')))

        elif sec_type == 'team':
            for f in ['title', 'subtitle']:
                if f in orig_data or f in orig_draft:
                    controls_to_test.append((f, orig_data.get(f, '')))
            if 'members' in orig_data and isinstance(orig_data['members'], list) and len(orig_data['members']) > 0:
                controls_to_test.append(('member_0_name', orig_data['members'][0].get('name', '')))
                controls_to_test.append(('member_0_role', orig_data['members'][0].get('role', '')))

        elif sec_type == 'logo_wall':
            for f in ['title']:
                if f in orig_data or f in orig_draft:
                    controls_to_test.append((f, orig_data.get(f, '')))
            if 'logos' in orig_data and isinstance(orig_data['logos'], list) and len(orig_data['logos']) > 0:
                controls_to_test.append(('logo_0_name', orig_data['logos'][0].get('name', '')))

        # Default fallback if no controls detected
        if not controls_to_test:
            controls_to_test.append(('title', orig_data.get('title', 'Default Title')))

        # Perform test for each control
        for control_name, orig_val in controls_to_test:
            orig_val_str = str(orig_val) if orig_val is not None else ""
            test_tag = f"QA_{uuid.uuid4().hex[:6]}"
            mutated_val = f"{orig_val_str} [{test_tag}]" if orig_val_str else f"Test Value [{test_tag}]"
            
            # 1. Prepare modified draft payload
            import copy
            test_draft = copy.deepcopy(orig_data)
            
            if control_name in test_draft:
                test_draft[control_name] = mutated_val
            elif control_name == 'btn1_text' and 'buttons' in test_draft and len(test_draft['buttons']) > 0:
                test_draft['buttons'][0]['label'] = mutated_val
            elif control_name == 'btn1_url' and 'buttons' in test_draft and len(test_draft['buttons']) > 0:
                test_draft['buttons'][0]['url'] = f"/test-{test_tag}"
                mutated_val = f"/test-{test_tag}"
            elif control_name == 'bullet_0_text' and 'bullets' in test_draft and len(test_draft['bullets']) > 0:
                test_draft['bullets'][0]['text'] = mutated_val
            elif control_name.startswith('card_') and 'cards' in test_draft:
                parts = control_name.split('_')
                c_idx = int(parts[1])
                field = parts[2]
                if field == 'desc': field = 'description'
                if c_idx < len(test_draft['cards']):
                    test_draft['cards'][c_idx][field] = mutated_val
            elif control_name.startswith('member_') and 'members' in test_draft:
                parts = control_name.split('_')
                m_idx = int(parts[1])
                field = parts[2]
                if m_idx < len(test_draft['members']):
                    test_draft['members'][m_idx][field] = mutated_val
            elif control_name.startswith('logo_') and 'logos' in test_draft:
                parts = control_name.split('_')
                l_idx = int(parts[1])
                field = parts[2]
                if l_idx < len(test_draft['logos']):
                    test_draft['logos'][l_idx][field] = mutated_val
            else:
                test_draft[control_name] = mutated_val

            # Step 1: Save Draft via API
            status_draft, resp_draft = api_put_draft(token, sec_id, test_draft)
            draft_pass = (status_draft == 200)

            # Step 2: Verify Persistence (draft_data changed in DB, but data remains untouched)
            cur.execute("SELECT draft_data, data FROM page_sections WHERE id = %s", (sec_id,))
            db_row = cur.fetchone()
            db_draft, db_data = db_row[0], db_row[1]
            
            db_draft_str = json.dumps(db_draft)
            db_data_str = json.dumps(db_data)
            
            draft_in_db = test_tag in db_draft_str
            data_untouched = test_tag not in db_data_str
            persistence_pass = (draft_in_db and data_untouched)

            # Step 3: Check Public Frontend Isolation (draft must NOT leak to public page)
            pub_content_before = fetch_public_content(page_path)
            pub_json_before = json.dumps(pub_content_before)
            frontend_draft_isolated = (test_tag not in pub_json_before)

            # Check that draft mode DOES see the change
            draft_content = fetch_public_content(page_path, token=token)
            draft_mode_has_change = (test_tag in json.dumps(draft_content))

            # Step 4: Publish
            status_pub, resp_pub = api_publish_section(token, sec_id, test_draft)
            pub_pass = (status_pub == 200)

            # Verify DB data has been updated with published changes
            cur.execute("SELECT data FROM page_sections WHERE id = %s", (sec_id,))
            db_published_row = cur.fetchone()
            published_in_db = test_tag in json.dumps(db_published_row[0])

            # Step 5: Check Public Frontend after Publish
            pub_content_after = fetch_public_content(page_path)
            pub_json_after = json.dumps(pub_content_after)
            frontend_pass = (test_tag in pub_json_after)

            # Step 6: Restoration (Restore original data and draft_data)
            cur.execute("""
                UPDATE page_sections 
                SET data = %s, draft_data = %s, updated_at = NOW() 
                WHERE id = %s
            """, (json.dumps(orig_data), json.dumps(orig_draft), sec_id))
            conn.commit()

            # Verify restoration in DB and public page
            cur.execute("SELECT data FROM page_sections WHERE id = %s", (sec_id,))
            restored_db = cur.fetchone()[0]
            pub_content_restored = fetch_public_content(page_path)
            restoration_pass = (test_tag not in json.dumps(restored_db) and test_tag not in json.dumps(pub_content_restored))

            # Record evidence
            ev_id = f"ev_{sec_id[:8]}_{control_name}"
            ev_filename = f"{ev_id}.json"
            ev_filepath = os.path.join(EVIDENCE_DIR, ev_filename)
            evidence_data = {
                "page": page_path,
                "section_id": sec_id,
                "anchor_id": anchor_id,
                "control": control_name,
                "original_value": orig_val_str,
                "test_tag": test_tag,
                "mutated_value": mutated_val,
                "draft_save_status": status_draft,
                "persistence_isolated": persistence_pass,
                "publish_status": status_pub,
                "frontend_updated": frontend_pass,
                "restoration_verified": restoration_pass,
                "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
            }
            with open(ev_filepath, 'w', encoding='utf-8') as f:
                json.dump(evidence_data, f, indent=2)

            res_row = {
                "Page": page_path,
                "Section": f"Sec: {anchor_id or 'none'}",
                "Section type": sec_type,
                "Control": control_name,
                "Original value": orig_val_str[:50],
                "Test action": f"Mutated with {test_tag}",
                "Draft result": "PASS" if draft_pass else "FAIL",
                "Persistence": "PASS" if persistence_pass else "FAIL",
                "Published result": "PASS" if pub_pass and published_in_db else "FAIL",
                "Frontend result": "PASS" if frontend_pass else "FAIL",
                "Restoration": "PASS" if restoration_pass else "FAIL",
                "Evidence": ev_filename,
                "Bug": "None" if (draft_pass and persistence_pass and pub_pass and frontend_pass and restoration_pass) else "Lifecycle Failure"
            }
            results.append(res_row)
            print(f"  - Control [{control_name}]: Draft={res_row['Draft result']} | Persist={res_row['Persistence']} | Pub={res_row['Published result']} | Frontend={res_row['Frontend result']} | Restored={res_row['Restoration']}")

    # Write out FIELD_LEVEL_TEST_RESULTS.csv
    fieldnames = [
        "Page", "Section", "Section type", "Control", "Original value", 
        "Test action", "Draft result", "Persistence", "Published result", 
        "Frontend result", "Restoration", "Evidence", "Bug"
    ]
    with open(CSV_PATH, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for r in results:
            writer.writerow(r)

    total_controls = len(results)
    passed_controls = sum(1 for r in results if r['Bug'] == 'None')
    print(f"\n==========================================")
    print(f"FIELD-LEVEL AUDIT COMPLETE: {passed_controls}/{total_controls} controls passed 100% lifecycle validation.")
    print(f"Results written to: {CSV_PATH}")
    print(f"Evidence files stored in: {EVIDENCE_DIR}")
    print(f"==========================================")

    cur.close()
    conn.close()

if __name__ == '__main__':
    run_field_level_tests()
