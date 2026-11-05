import os
from dotenv import load_dotenv

# Resolve repository base directory
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
load_dotenv(os.path.join(BASE_DIR, ".env"))

BASE_URL = os.environ.get("TEST_BASE_URL", f"http://localhost:{os.environ.get('PORT', '8080')}")

# ==============================================================================
# STEP 6C: TEST ENVIRONMENT SAFEGUARDS & PRODUCTION HOSTNAME DENYLIST
# ==============================================================================
PRODUCTION_DENYLIST = [
    "salesleadmachine.co.uk",
    "www.salesleadmachine.co.uk",
    "api.salesleadmachine.co.uk",
    "app.salesleadmachine.co.uk"
]

def assert_safe_test_environment():
    """Ensure test scripts cannot accidentally run against live production environments."""
    for prod_host in PRODUCTION_DENYLIST:
        if prod_host in BASE_URL.lower():
            raise RuntimeError(
                f"[SECURITY ABORT] Destructive test suite targeted against production host: '{BASE_URL}'. "
                f"Tests may only run against localhost, 127.0.0.1, or authorized staging environments."
            )
    if not (("localhost" in BASE_URL) or ("127.0.0.1" in BASE_URL) or ("test" in BASE_URL) or ("staging" in BASE_URL)):
        raise RuntimeError(
            f"[SECURITY ABORT] Untrusted test target URL: '{BASE_URL}'. Target must be localhost or staging."
        )

# Execute verification on configuration load
assert_safe_test_environment()

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

