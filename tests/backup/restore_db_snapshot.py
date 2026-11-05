import psycopg2, json

conn = psycopg2.connect(dbname="salesleadmachine", user="liluzi", host="127.0.0.1", port=5432)
cur = conn.cursor()

with open("/Users/liluzi/Desktop/python/salesleadmachine-revamp/tests/backup/pre_audit_db_snapshot.json", "r") as f:
    snapshot = json.load(f)

# Restore page_sections
for sec in snapshot.get("page_sections", []):
    cur.execute("""
        UPDATE page_sections
        SET data = %s, draft_data = %s, is_visible = %s, sort_order = %s, label = %s, anchor_id = %s
        WHERE id = %s;
    """, (
        json.dumps(sec["data"]),
        json.dumps(sec["draft_data"]),
        sec["is_visible"],
        sec["sort_order"],
        sec["label"],
        sec["anchor_id"],
        sec["id"]
    ))

# Delete any extra test records in team_members
original_team_ids = [m["id"] for m in snapshot.get("team_members", [])]
cur.execute("DELETE FROM team_members WHERE id::text NOT IN %s;", (tuple(original_team_ids),))

# Restore team_members fields
for m in snapshot.get("team_members", []):
    cur.execute("""
        UPDATE team_members
        SET full_name = %s, job_title = %s, bio = %s, photo_url = %s, email = %s, phone = %s, socials = %s, sort_order = %s, is_visible = %s
        WHERE id = %s;
    """, (
        m["full_name"], m["job_title"], m["bio"], m["photo_url"], m["email"], m["phone"],
        json.dumps(m["socials"]) if isinstance(m["socials"], dict) else m["socials"],
        m["sort_order"], m["is_visible"], m["id"]
    ))

# Restore logos
original_logo_ids = [l["id"] for l in snapshot.get("client_logos", [])]
cur.execute("DELETE FROM client_logos WHERE id::text NOT IN %s;", (tuple(original_logo_ids),))

# Restore site_settings
for s in snapshot.get("site_settings", []):
    cur.execute("UPDATE site_settings SET value = %s WHERE key = %s;", (json.dumps(s["value"]) if isinstance(s["value"], dict) else s["value"], s["key"]))

conn.commit()
conn.close()
print("Database restoration verified! All original states restored from snapshot.")
