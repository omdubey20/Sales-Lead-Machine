import psycopg2, json, datetime

def default_json(obj):
    if isinstance(obj, (datetime.date, datetime.datetime)):
        return obj.isoformat()
    return str(obj)

conn = psycopg2.connect(dbname="salesleadmachine", user="liluzi", host="127.0.0.1", port=5432)
cur = conn.cursor()

tables = ["pages", "page_sections", "team_members", "client_logos", "site_settings", "users", "media", "form_submissions"]
snapshot = {}

for t in tables:
    cur.execute(f"SELECT * FROM {t};")
    cols = [desc[0] for desc in cur.description]
    rows = cur.fetchall()
    snapshot[t] = [dict(zip(cols, row)) for row in rows]
    print(f"Backed up {len(rows)} rows from table '{t}'")

with open("/Users/liluzi/Desktop/python/salesleadmachine-revamp/tests/backup/pre_audit_db_snapshot.json", "w") as f:
    json.dump(snapshot, f, indent=2, default=default_json)

conn.close()
print("Pre-audit database snapshot successfully saved to tests/backup/pre_audit_db_snapshot.json")
