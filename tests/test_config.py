import os
import sys
import ipaddress
import urllib.parse
from dotenv import load_dotenv

# Resolve repository base directory
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
load_dotenv(os.path.join(BASE_DIR, ".env"))

BASE_URL = os.environ.get("TEST_BASE_URL", f"http://localhost:{os.environ.get('PORT', '8080')}")

# ==============================================================================
# STEP 6D: TEST ENVIRONMENT SAFEGUARDS, HOSTNAME DENYLIST & IP VALIDATION
# ==============================================================================
PRODUCTION_DENYLIST = [
    "salesleadmachine.co.uk",
    "www.salesleadmachine.co.uk",
    "api.salesleadmachine.co.uk",
    "app.salesleadmachine.co.uk"
]

ALLOWED_LOCAL_HOSTS = {
    "localhost",
    "127.0.0.1",
    "::1",
    "0.0.0.0",
    "testserver"
}

PGHOST = os.environ.get("PGHOST", "127.0.0.1")
PGPORT = int(os.environ.get("PGPORT", "5432"))
PGDATABASE = os.environ.get("PGDATABASE", "salesleadmachine")
PGUSER = os.environ.get("PGUSER", os.environ.get("USER", "postgres"))
PGPASSWORD = os.environ.get("PGPASSWORD", "")

def assert_safe_test_environment(target_url: str = None, db_host: str = None, db_name: str = None):
    """
    Validate target URL, scheme, hostname, IP address and database destination
    to guarantee test suites never execute destructive operations against production.
    """
    url_to_check = target_url or BASE_URL
    parsed = urllib.parse.urlparse(url_to_check)

    # 1. Scheme Validation
    if parsed.scheme not in ("http", "https"):
        raise RuntimeError(
            f"[SECURITY ABORT] Invalid or missing URL scheme in target: '{url_to_check}'. Scheme must be http or https."
        )

    hostname = (parsed.hostname or "").lower().strip()
    if not hostname:
        raise RuntimeError(
            f"[SECURITY ABORT] Target URL missing valid hostname: '{url_to_check}'."
        )

    # 2. Strict Production Denylist
    for prod_host in PRODUCTION_DENYLIST:
        if hostname == prod_host or hostname.endswith("." + prod_host):
            raise RuntimeError(
                f"[SECURITY ABORT] Destructive test suite targeted against production host: '{hostname}'. "
                f"Tests are strictly prohibited on live production infrastructure."
            )

    # 3. Explicit Allowed Hosts and Staging Verification
    allowed_staging = [
        h.strip().lower()
        for h in os.environ.get("ALLOWED_STAGING_HOSTS", "").split(",")
        if h.strip()
    ]

    is_allowed = (
        hostname in ALLOWED_LOCAL_HOSTS or
        hostname.endswith(".local") or
        hostname.endswith(".test") or
        hostname in allowed_staging
    )

    # Check if hostname is an IP address
    try:
        ip = ipaddress.ip_address(hostname)
        if ip.is_loopback:
            is_allowed = True
        elif not ip.is_private:
            raise RuntimeError(
                f"[SECURITY ABORT] Target resolves to public IP address: '{hostname}'. "
                f"Public IP targets are forbidden for destructive testing."
            )
        elif hostname in allowed_staging:
            is_allowed = True
        else:
            raise RuntimeError(
                f"[SECURITY ABORT] Target private IP '{hostname}' not explicitly registered in ALLOWED_STAGING_HOSTS."
            )
    except ValueError:
        # Not a raw IP address; string hostname
        pass

    if not is_allowed:
        raise RuntimeError(
            f"[SECURITY ABORT] Untrusted test target host: '{hostname}'. "
            f"Target host must be localhost, 127.0.0.1, or registered in ALLOWED_STAGING_HOSTS."
        )

    # 4. Database Destination Verification
    target_db_host = (db_host if db_host is not None else PGHOST).strip().lower()
    target_db_name = (db_name if db_name is not None else PGDATABASE).strip().lower()

    # Reject remote production DB hosts
    for prod_host in PRODUCTION_DENYLIST:
        if prod_host in target_db_host:
            raise RuntimeError(
                f"[SECURITY ABORT] Test database host points to production domain: '{target_db_host}'."
            )

    is_db_local = (
        target_db_host in ALLOWED_LOCAL_HOSTS or
        target_db_host == "" or  # Unix domain socket
        target_db_host.startswith("/") or
        target_db_host in allowed_staging
    )

    try:
        db_ip = ipaddress.ip_address(target_db_host)
        if db_ip.is_loopback:
            is_db_local = True
        elif not db_ip.is_private:
            raise RuntimeError(
                f"[SECURITY ABORT] Test database host is a public IP: '{target_db_host}'."
            )
    except ValueError:
        pass

    if not is_db_local:
        raise RuntimeError(
            f"[SECURITY ABORT] Test database host '{target_db_host}' is not a permitted local or staging database host."
        )

    # Reject obviously production database names on remote hosts
    if ("prod" in target_db_name or "production" in target_db_name) and not is_db_local:
        raise RuntimeError(
            f"[SECURITY ABORT] Database name '{target_db_name}' appears to be production."
        )

    return True

# Execute verification on configuration load
assert_safe_test_environment()

ADMIN_EMAIL = os.environ.get("TEST_ADMIN_EMAIL", "admin@salesleadmachine.co.uk")
ADMIN_PASSWORD = os.environ.get("TEST_ADMIN_PASSWORD")

USER_EMAIL = os.environ.get("TEST_USER_EMAIL", "regular_user@salesleadmachine.co.uk")
USER_PASSWORD = os.environ.get("TEST_USER_PASSWORD")

def get_db_connection():
    assert_safe_test_environment()
    import psycopg2
    return psycopg2.connect(
        host=PGHOST,
        port=PGPORT,
        dbname=PGDATABASE,
        user=PGUSER,
        password=PGPASSWORD or None
    )

def get_admin_jwt():
    assert_safe_test_environment()
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
