import os
from dotenv import load_dotenv

# Resolve repository base directory
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
load_dotenv(os.path.join(BASE_DIR, ".env"))

BASE_URL = os.environ.get("TEST_BASE_URL", f"http://localhost:{os.environ.get('PORT', '8080')}")

ADMIN_EMAIL = os.environ.get("TEST_ADMIN_EMAIL", "admin@salesleadmachine.co.uk")
ADMIN_PASSWORD = os.environ.get("TEST_ADMIN_PASSWORD")

USER_EMAIL = os.environ.get("TEST_USER_EMAIL", "regular_user@salesleadmachine.co.uk")
USER_PASSWORD = os.environ.get("TEST_USER_PASSWORD")

PGHOST = os.environ.get("PGHOST", "127.0.0.1")
PGPORT = int(os.environ.get("PGPORT", "5432"))
PGDATABASE = os.environ.get("PGDATABASE", "salesleadmachine")
PGUSER = os.environ.get("PGUSER", os.environ.get("USER", "postgres"))
PGPASSWORD = os.environ.get("PGPASSWORD", "")

def get_db_connection():
    import psycopg2
    return psycopg2.connect(
        host=PGHOST,
        port=PGPORT,
        dbname=PGDATABASE,
        user=PGUSER,
        password=PGPASSWORD or None
    )

def get_admin_jwt():
    import urllib.request, json
    if not ADMIN_PASSWORD:
        raise RuntimeError("TEST_ADMIN_PASSWORD environment variable is not configured.")
    req = urllib.request.Request(
        f"{BASE_URL}/api/admin/login",
        data=json.dumps({"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD}).encode("utf-8"),
        headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(req) as resp:
        data = json.loads(resp.read().decode("utf-8"))
        if not data.get("success"):
            raise RuntimeError(f"Admin login failed: {data}")
        return data.get("token")
