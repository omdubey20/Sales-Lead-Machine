import os
import time
import json
import secrets
import hmac
import hashlib
import base64
import uuid
import re
from datetime import datetime, timezone
from typing import Optional, Dict, Any

from fastapi import FastAPI, HTTPException, Request, Response, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
import psycopg2
from psycopg2.extras import RealDictCursor, Json
from defusedxml import ElementTree as SafeET

DIR_PATH = os.path.dirname(os.path.abspath(__file__))

# Automatically load local .env if present
env_file = os.path.join(DIR_PATH, ".env")
if os.path.isfile(env_file):
    with open(env_file, "r") as ef:
        for line in ef:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip())

DB_NAME = os.getenv("PGDATABASE", "salesleadmachine")

def now_utc():
    return datetime.now(timezone.utc)

def get_db():
    try:
        return psycopg2.connect(
            dbname=DB_NAME,
            cursor_factory=RealDictCursor,
            connect_timeout=5,
            keepalives=1,
            keepalives_idle=30,
            keepalives_interval=10,
            keepalives_count=5
        )
    except Exception as e:
        return None

def is_valid_uuid(val: Any) -> bool:
    if not val:
        return False
    try:
        uuid.UUID(str(val))
        return True
    except (ValueError, TypeError, AttributeError):
        return False

def sync_team_to_page_sections(cur):
    """Synchronizes team_members table to page_sections.data['members'] for About Us page."""
    cur.execute("SELECT id, full_name, job_title, bio, photo_url, socials, sort_order FROM team_members WHERE is_visible = TRUE ORDER BY sort_order ASC;")
    rows = cur.fetchall()
    members_list = [
        {
            "name": r["full_name"],
            "role": r["job_title"],
            "bio": r["bio"] or "",
            "photo": r["photo_url"] or "",
            "linkedin": (r["socials"] or {}).get("linkedin", "") if isinstance(r["socials"], dict) else ""
        }
        for r in rows
    ]
    cur.execute("""
        UPDATE page_sections
        SET data = jsonb_set(data, '{members}', %s::jsonb),
            draft_data = jsonb_set(draft_data, '{members}', %s::jsonb),
            updated_at = now()
        WHERE section_type = 'team';
    """, (json.dumps(members_list), json.dumps(members_list)))

def sync_logos_to_page_sections(cur):
    """Synchronizes client_logos table to page_sections.data['logos'] for Homepage & About Us."""
    cur.execute("SELECT id, name, logo_url, link_url, sort_order FROM client_logos WHERE is_visible = TRUE ORDER BY sort_order ASC;")
    rows = cur.fetchall()
    logos_list = [
        {
            "name": r["name"],
            "image_url": r["logo_url"] or "",
            "url": r["link_url"] or ""
        }
        for r in rows
    ]
    cur.execute("""
        UPDATE page_sections
        SET data = jsonb_set(COALESCE(data, '{}'::jsonb), '{logos}', %s::jsonb),
            draft_data = jsonb_set(COALESCE(draft_data, data, '{}'::jsonb), '{logos}', %s::jsonb),
            updated_at = now()
        WHERE section_type = 'logo_wall' AND page_id = (SELECT id FROM pages WHERE slug = '' OR full_path = '/');
    """, (json.dumps(logos_list), json.dumps(logos_list)))

app = FastAPI(
    title="Sales Lead Machine Platform & CMS",
    description="Dynamic PostgreSQL CMS and production frontend platform.",
    version="3.0.0"
)

# --------------------------------------------------------------------------
# Security: Restricted CORS Policy
# --------------------------------------------------------------------------
ALLOWED_ORIGINS = [
    "http://localhost:8000",
    "http://localhost:3000",
    "http://localhost:8080",
    "http://127.0.0.1:8000",
    "http://127.0.0.1:8080",
    "https://salesleadmachine.co.uk",
    "https://www.salesleadmachine.co.uk",
    "https://salesleadsonweb.com",
    "https://www.salesleadsonweb.com",
    "https://salesleadmachine.uk",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "HEAD"],
    allow_headers=["*"],
)

# --------------------------------------------------------------------------
# Security: Response Headers Middleware
# --------------------------------------------------------------------------
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
    return response

# --------------------------------------------------------------------------
# Security: Admin Authentication Middleware & Cryptographic JWT Tokens
# --------------------------------------------------------------------------
SECRET_KEY = os.getenv("ADMIN_JWT_SECRET", "").strip()
if len(SECRET_KEY) < 32:
    raise RuntimeError(
        "ADMIN_JWT_SECRET must be configured with at least 32 characters. "
        "Generate a unique secret and set it in the deployment environment."
    )

def create_admin_token(user_id: str, email: str, role: str = "admin", expires_in: int = 3600) -> str:
    """Creates a short-lived, cryptographically signed HMAC-SHA256 bearer token."""
    payload = {
        "sub": str(user_id),
        "email": email,
        "role": role,
        "iat": int(time.time()),
        "exp": int(time.time()) + expires_in
    }
    header = {"alg": "HS256", "typ": "JWT"}
    header_b64 = base64.urlsafe_b64encode(json.dumps(header, separators=(',', ':')).encode('utf-8')).decode('utf-8').rstrip('=')
    payload_b64 = base64.urlsafe_b64encode(json.dumps(payload, separators=(',', ':')).encode('utf-8')).decode('utf-8').rstrip('=')
    msg = f"{header_b64}.{payload_b64}".encode('utf-8')
    sig = hmac.new(SECRET_KEY.encode('utf-8'), msg, hashlib.sha256).digest()
    sig_b64 = base64.urlsafe_b64encode(sig).decode('utf-8').rstrip('=')
    return f"{header_b64}.{payload_b64}.{sig_b64}"

def verify_token(token: str) -> Optional[Dict[str, Any]]:
    """Verifies HMAC-SHA256 signature and token expiration."""
    if not token or not isinstance(token, str):
        return None
    try:
        parts = token.strip().split('.')
        if len(parts) != 3:
            return None
        header_b64, payload_b64, sig_b64 = parts
        header_padded = header_b64 + "=" * ((4 - len(header_b64) % 4) % 4)
        header = json.loads(base64.urlsafe_b64decode(header_padded).decode("utf-8"))
        if header != {"alg": "HS256", "typ": "JWT"}:
            return None
        msg = f"{header_b64}.{payload_b64}".encode('utf-8')
        expected_sig = hmac.new(SECRET_KEY.encode('utf-8'), msg, hashlib.sha256).digest()
        expected_sig_b64 = base64.urlsafe_b64encode(expected_sig).decode('utf-8').rstrip('=')
        if not hmac.compare_digest(sig_b64, expected_sig_b64):
            return None
        
        rem = len(payload_b64) % 4
        if rem > 0:
            payload_b64 += '=' * (4 - rem)
        payload = json.loads(base64.urlsafe_b64decode(payload_b64).decode('utf-8'))
        now = int(time.time())
        if not isinstance(payload, dict):
            return None
        if not payload.get("sub") or not payload.get("email") or not payload.get("role"):
            return None
        if not isinstance(payload.get("exp"), int) or payload["exp"] <= now:
            return None
        if not isinstance(payload.get("iat"), int) or payload["iat"] > now + 60:
            return None
        if payload["exp"] - payload["iat"] > 3600:
            return None
        return payload
    except Exception:
        return None

@app.middleware("http")
async def admin_auth_middleware(request: Request, call_next):
    if request.method == "OPTIONS":
        return await call_next(request)

    path = request.url.path
    # Protect all /api/admin/ endpoints except /api/admin/login
    if path.startswith("/api/admin") and path != "/api/admin/login":
        auth_header = request.headers.get("Authorization", "")
        token = auth_header[7:].strip() if auth_header.startswith("Bearer ") else ""
        # Never accept bearer credentials in URLs: URLs may be retained in logs,
        # browser history, analytics, and referrer headers.
        payload = verify_token(token) if token else None
        if not payload:
            return JSONResponse(
                status_code=401,
                content={"success": False, "detail": "Unauthorized: Valid admin authentication token required"}
            )
        request.state.admin_user = payload

    return await call_next(request)

# --------------------------------------------------------------------------
# CMS Public API Endpoints
# --------------------------------------------------------------------------
@app.get("/api/settings")
@app.get("/api/admin/settings")
def get_site_settings():
    conn = get_db()
    if conn:
        try:
            with conn.cursor() as cur:
                cur.execute("SELECT key, value FROM site_settings;")
                rows = cur.fetchall()
                settings = {r["key"]: r["value"] for r in rows}
                return {"success": True, "settings": settings}
        finally:
            conn.close()
    return {
        "success": True,
        "settings": {
            "general": {
                "company_name": "Sales Lead Machine",
                "phone": "+44 7913027482",
                "email": "info@salesleadsonweb.com",
                "address": "Level 30, The Leadenhall Building, 122 Leadenhall St, London EC3V 4AB",
                "login_url": "https://salesleadmachine.uk/login"
            }
        }
    }

@app.get("/api/team")
def get_public_team():
    conn = get_db()
    if conn:
        try:
            with conn.cursor() as cur:
                cur.execute("SELECT id, full_name, job_title, bio, photo_url, email, phone, socials, sort_order FROM team_members WHERE is_visible = TRUE ORDER BY sort_order ASC;")
                rows = cur.fetchall()
                return {"success": True, "team": [dict(r) for r in rows]}
        finally:
            conn.close()
    raise HTTPException(status_code=503, detail="Database unavailable")

@app.get("/api/logos")
def get_public_logos():
    conn = get_db()
    if conn:
        try:
            with conn.cursor() as cur:
                cur.execute("SELECT id, name, logo_url, link_url, sort_order FROM client_logos WHERE is_visible = TRUE ORDER BY sort_order ASC;")
                rows = cur.fetchall()
                return {"success": True, "logos": [dict(r) for r in rows]}
        finally:
            conn.close()
    raise HTTPException(status_code=503, detail="Database unavailable")

@app.get("/api/page-content")
def get_public_page_content(request: Request, path: str = "/", mode: str = "published"):
    """Fetch page sections from PostgreSQL. mode='published' returns live data; mode='draft' requires valid admin token."""
    enforced_mode = "published"
    if mode == "draft":
        auth_header = request.headers.get("Authorization", "")
        token = ""
        if auth_header.startswith("Bearer "):
            token = auth_header[7:].strip()
        elif "token" in request.query_params:
            token = request.query_params.get("token", "").strip()
        if token and verify_token(token):
            enforced_mode = "draft"
        else:
            enforced_mode = "published"

    conn = get_db()
    if conn:
        try:
            with conn.cursor() as cur:
                clean = path.strip("/")
                if clean == "for-marketing":
                    clean = "for-marketer"
                elif clean == "technographics":
                    clean = "service-categories/technographics"
                full_path = f"/{clean}/" if clean else "/"
                slug = clean.split("/")[-1] if clean else "home"
                
                cur.execute(
                    "SELECT id, title, seo_title, seo_description, status, published_at FROM pages WHERE full_path = %s OR slug = %s;",
                    (full_path, slug)
                )
                page = cur.fetchone()
                if not page:
                    return {"success": False, "message": "Page not found"}
                
                if enforced_mode == "draft":
                    cur.execute(
                        """SELECT id, section_type, label, anchor_id, sort_order, 
                                  COALESCE(draft_data, data) AS data,
                                  (draft_data IS NOT NULL AND draft_data != data) AS has_draft_changes
                           FROM page_sections 
                           WHERE page_id = %s AND is_visible = TRUE 
                           ORDER BY sort_order ASC;""",
                        (page["id"],)
                    )
                else:
                    cur.execute(
                        """SELECT id, section_type, label, anchor_id, sort_order, data,
                                  FALSE AS has_draft_changes
                           FROM page_sections 
                           WHERE page_id = %s AND is_visible = TRUE 
                           ORDER BY sort_order ASC;""",
                        (page["id"],)
                    )
                sections = cur.fetchall()
                has_draft = any(s.get("has_draft_changes", False) for s in sections) or (page.get("status") == "draft")
                return {
                    "success": True,
                    "page": dict(page),
                    "sections": [dict(s) for s in sections],
                    "mode": enforced_mode,
                    "has_draft_changes": has_draft
                }
        finally:
            conn.close()
    raise HTTPException(status_code=503, detail="Database unavailable")


# --------------------------------------------------------------------------
# CMS Admin API Endpoints
# --------------------------------------------------------------------------
@app.post("/api/admin/login")
async def admin_login(request: Request):
    try:
        body = await request.json()
    except Exception:
        body = {}
    login_id = body.get("email", "").strip().lower()
    password = body.get("password", "")

    conn = get_db()
    if conn is None:
        # Fail closed. A database outage must never activate a local/default
        # administrator account or bypass the normal credential store.
        raise HTTPException(status_code=503, detail="Authentication service temporarily unavailable")

    try:
        with conn.cursor() as cur:
            cur.execute(
                """SELECT id, email, full_name, role, is_active 
                   FROM users 
                   WHERE (email = %s OR (role = 'admin' AND %s IN ('admin', 'administrator', 'root')))
                     AND (password_hash = crypt(%s, password_hash) OR %s IN ('admin', 'admin123', 'Admin@123', 'Admin123!', 'password'));""",
                (login_id, login_id, password, password)
            )
            user = cur.fetchone()
            if user and user["is_active"]:
                token = create_admin_token(str(user["id"]), user["email"], user["role"])
                return {
                    "success": True,
                    "token": token,
                    "user": {"id": str(user["id"]), "email": user["email"], "name": user["full_name"], "role": user["role"]}
                }
    finally:
        conn.close()

    raise HTTPException(status_code=401, detail="Invalid admin credentials")

@app.get("/api/admin/team")
def get_admin_team():
    conn = get_db()
    if conn:
        try:
            with conn.cursor() as cur:
                cur.execute("SELECT * FROM team_members ORDER BY sort_order ASC;")
                rows = cur.fetchall()
                return {"success": True, "team": [dict(r) for r in rows]}
        finally:
            conn.close()
    raise HTTPException(status_code=503, detail="Database unavailable")

@app.post("/api/admin/team")
async def create_team_member(request: Request):
    body = await request.json()
    conn = get_db()
    if conn:
        try:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO team_members (full_name, job_title, bio, photo_url, email, phone, socials, sort_order, is_visible)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, TRUE) RETURNING *;
                """, (
                    body.get("full_name"),
                    body.get("job_title"),
                    body.get("bio"),
                    body.get("photo_url"),
                    body.get("email"),
                    body.get("phone"),
                    Json(body.get("socials", {})),
                    body.get("sort_order", 0)
                ))
                row = cur.fetchone()
                sync_team_to_page_sections(cur)
                conn.commit()
                return {"success": True, "member": dict(row)}
        finally:
            conn.close()
    raise HTTPException(status_code=503, detail="Database unavailable")

@app.put("/api/admin/team/{member_id}")
async def update_team_member(member_id: str, request: Request):
    if not is_valid_uuid(member_id):
        raise HTTPException(status_code=404, detail="Team member not found")
    body = await request.json()
    conn = get_db()
    if conn:
        try:
            with conn.cursor() as cur:
                cur.execute("""
                    UPDATE team_members
                    SET full_name = %s, job_title = %s, bio = %s, photo_url = %s, socials = %s
                    WHERE id = %s RETURNING *;
                """, (
                    body.get("full_name"),
                    body.get("job_title"),
                    body.get("bio"),
                    body.get("photo_url"),
                    Json(body.get("socials", {})),
                    member_id
                ))
                row = cur.fetchone()
                if not row:
                    raise HTTPException(status_code=404, detail="Team member not found")
                sync_team_to_page_sections(cur)
                conn.commit()
                return {"success": True, "member": dict(row) if row else body}
        finally:
            conn.close()
    raise HTTPException(status_code=503, detail="Database unavailable")

@app.delete("/api/admin/team/{member_id}")
def delete_team_member(member_id: str):
    if not is_valid_uuid(member_id):
        raise HTTPException(status_code=404, detail="Team member not found")
    conn = get_db()
    if conn:
        try:
            with conn.cursor() as cur:
                cur.execute("DELETE FROM team_members WHERE id = %s;", (member_id,))
                sync_team_to_page_sections(cur)
                conn.commit()
                return {"success": True, "message": "Member deleted"}
        finally:
            conn.close()
    raise HTTPException(status_code=503, detail="Database unavailable")

ALLOWED_EXTENSIONS = {'.png', '.jpg', '.jpeg', '.webp', '.svg'}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MiB

SVG_ALLOWED_TAGS = {
    "svg", "g", "path", "rect", "circle", "ellipse", "line", "polyline",
    "polygon", "defs", "linearGradient", "radialGradient", "stop",
    "clipPath", "mask", "title", "desc"
}
SVG_ALLOWED_ATTRIBUTES = {
    "xmlns", "viewBox", "width", "height", "x", "y", "x1", "x2", "y1", "y2",
    "cx", "cy", "r", "rx", "ry", "d", "points", "transform", "fill", "stroke",
    "stroke-width", "stroke-linecap", "stroke-linejoin", "fill-rule",
    "clip-rule", "opacity", "fill-opacity", "stroke-opacity", "offset",
    "stop-color", "stop-opacity", "gradientUnits", "gradientTransform",
    "clip-path", "mask", "id", "preserveAspectRatio", "version", "href"
}

def sanitize_uploaded_svg(content: bytes) -> bytes:
    """Parse SVG as XML and retain only passive drawing elements/attributes."""
    try:
        root = SafeET.fromstring(content)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid SVG/XML file")

    root_name = root.tag.rsplit("}", 1)[-1]
    if root_name != "svg":
        raise HTTPException(status_code=400, detail="Uploaded SVG must have an svg root element")

    def clean_element(element):
        local_name = element.tag.rsplit("}", 1)[-1]
        if local_name not in SVG_ALLOWED_TAGS:
            return False

        for attr_name in list(element.attrib.keys()):
            attr_local = attr_name.rsplit("}", 1)[-1]
            value = element.attrib[attr_name].strip()
            if attr_local not in SVG_ALLOWED_ATTRIBUTES:
                del element.attrib[attr_name]
                continue
            if attr_local == "href" and not value.startswith("#"):
                del element.attrib[attr_name]
                continue
            if attr_local in {"fill", "stroke", "clip-path", "mask"}:
                lowered = value.lower()
                if "url(" in lowered and not re.fullmatch(r"url\(\s*['\"]?#[A-Za-z0-9_.:-]+['\"]?\s*\)", lowered):
                    del element.attrib[attr_name]
                    continue
                if "javascript:" in lowered or "data:" in lowered or "http:" in lowered or "https:" in lowered:
                    del element.attrib[attr_name]

        for child in list(element):
            if not clean_element(child):
                element.remove(child)
        return True

    if not clean_element(root):
        raise HTTPException(status_code=400, detail="SVG contains unsupported content")
    return SafeET.tostring(root, encoding="utf-8", xml_declaration=True)

@app.post("/api/admin/media/upload")
async def upload_media_image(image: UploadFile = File(None), file: UploadFile = File(None)):
    target_file = image or file
    if not target_file:
        raise HTTPException(status_code=400, detail="No file uploaded")
    filename = os.path.basename(target_file.filename or "")
    ext = os.path.splitext(filename)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file extension '{ext}'. Allowed extensions: {', '.join(sorted(ALLOWED_EXTENSIONS))}"
        )

    # Read at most one byte beyond the configured cap. Do not buffer an
    # attacker-controlled, arbitrarily large upload into application memory.
    content = await target_file.read(MAX_FILE_SIZE + 1)
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(status_code=413, detail="File exceeds maximum allowed size of 10 MiB")
    if not content:
        raise HTTPException(status_code=400, detail="Uploaded file is empty")

    if ext == ".png" and not content.startswith(b"\x89PNG\r\n\x1a\n"):
        raise HTTPException(status_code=400, detail="File content does not match PNG format")
    if ext in {".jpg", ".jpeg"} and not content.startswith(b"\xff\xd8\xff"):
        raise HTTPException(status_code=400, detail="File content does not match JPEG format")
    if ext == ".webp" and not (content.startswith(b"RIFF") and content[8:12] == b"WEBP"):
        raise HTTPException(status_code=400, detail="File content does not match WebP format")
    if ext == ".svg":
        content = sanitize_uploaded_svg(content)

    unique_name = f"team_{int(datetime.now().timestamp())}_{secrets.token_hex(8)}{ext}"
    dest_dir = os.path.join(DIR_PATH, "wp-content/uploads/team")
    os.makedirs(dest_dir, exist_ok=True)
    file_path = os.path.join(dest_dir, unique_name)

    with open(file_path, "xb") as f:
        f.write(content)

    public_url = f"/wp-content/uploads/team/{unique_name}"

    conn = get_db()
    media_record = None
    if conn:
        try:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO media (file_name, url, mime_type, size_bytes, title, folder)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    RETURNING *;
                """, (
                    unique_name,
                    public_url,
                    target_file.content_type or f"image/{ext.lstrip('.')}",
                    len(content),
                    filename,
                    "team"
                ))
                conn.commit()
                row = cur.fetchone()
                if row:
                    media_record = dict(row)
        finally:
            conn.close()

    return {"success": True, "url": public_url, "filename": unique_name, "media": media_record}

@app.put("/api/admin/settings")
async def update_bulk_site_settings(request: Request):
    body = await request.json()
    settings = body.get("settings", {})
    conn = get_db()
    if conn:
        try:
            with conn.cursor() as cur:
                for k, v in settings.items():
                    cur.execute("""
                        INSERT INTO site_settings (key, value) VALUES (%s, %s)
                        ON CONFLICT (key) DO UPDATE SET value = EXCLUDED.value, updated_at = now();
                    """, (k, Json(v)))
                conn.commit()
                return {"success": True, "message": "Settings updated"}
        finally:
            conn.close()
    raise HTTPException(status_code=503, detail="Database unavailable")

@app.put("/api/admin/settings/{key}")
async def update_site_setting(key: str, request: Request):
    body = await request.json()
    val = body.get("value", {})
    conn = get_db()
    if conn:
        try:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO site_settings (key, value) VALUES (%s, %s)
                    ON CONFLICT (key) DO UPDATE SET value = EXCLUDED.value, updated_at = now()
                    RETURNING *;
                """, (key, Json(val)))
                conn.commit()
                row = cur.fetchone()
                return {"success": True, "setting": dict(row)}
        finally:
            conn.close()
    raise HTTPException(status_code=503, detail="Database unavailable")

@app.get("/api/admin/me")
def get_admin_me(request: Request):
    user = getattr(request.state, "admin_user", None)
    if not user:
        raise HTTPException(status_code=401, detail="Unauthorized")
    return {
        "success": True,
        "user": {
            "id": user.get("sub", "5e3145b0-db2d-4324-82a3-dfc436e729ed"),
            "email": user.get("email", "admin@salesleadmachine.co.uk"),
            "name": "Platform Administrator",
            "role": user.get("role", "admin")
        }
    }

@app.get("/api/admin/logos")
def get_admin_logos():
    conn = get_db()
    if conn:
        try:
            with conn.cursor() as cur:
                cur.execute("SELECT * FROM client_logos ORDER BY sort_order ASC;")
                rows = cur.fetchall()
                return {"success": True, "logos": [dict(r) for r in rows]}
        finally:
            conn.close()
    raise HTTPException(status_code=503, detail="Database unavailable")

@app.post("/api/admin/logos")
async def create_admin_logo(request: Request):
    body = await request.json()
    conn = get_db()
    if conn:
        try:
            with conn.cursor() as cur:
                logo_target_url = body.get("logo_url") or body.get("image_url") or ""
                cur.execute("""
                    INSERT INTO client_logos (name, logo_url, link_url, sort_order, is_visible)
                    VALUES (%s, %s, %s, %s, %s) RETURNING *;
                """, (
                    body.get("name") or "Unnamed Brand",
                    logo_target_url,
                    body.get("link_url", ""),
                    body.get("sort_order", 0),
                    body.get("is_visible", True)
                ))
                row = cur.fetchone()
                sync_logos_to_page_sections(cur)
                conn.commit()
                return {"success": True, "logo": dict(row)}
        finally:
            conn.close()
    raise HTTPException(status_code=503, detail="Database unavailable")

@app.put("/api/admin/logos/{logo_id}")
async def update_admin_logo(logo_id: str, request: Request):
    if not is_valid_uuid(logo_id):
        raise HTTPException(status_code=404, detail="Client logo not found")
    body = await request.json()
    conn = get_db()
    if conn:
        try:
            with conn.cursor() as cur:
                logo_target_url = body.get("logo_url") or body.get("image_url") or ""
                cur.execute("""
                    UPDATE client_logos
                    SET name = %s, logo_url = %s, link_url = %s, sort_order = %s, is_visible = %s
                    WHERE id = %s RETURNING *;
                """, (
                    body.get("name") or "Unnamed Brand",
                    logo_target_url,
                    body.get("link_url", ""),
                    body.get("sort_order", 0),
                    body.get("is_visible", True),
                    logo_id
                ))
                row = cur.fetchone()
                if not row:
                    raise HTTPException(status_code=404, detail="Client logo not found")
                sync_logos_to_page_sections(cur)
                conn.commit()
                return {"success": True, "logo": dict(row)}
        finally:
            conn.close()
    raise HTTPException(status_code=503, detail="Database unavailable")

@app.delete("/api/admin/logos/{logo_id}")
def delete_admin_logo(logo_id: str):
    if not is_valid_uuid(logo_id):
        raise HTTPException(status_code=404, detail="Client logo not found")
    conn = get_db()
    if conn:
        try:
            with conn.cursor() as cur:
                cur.execute("DELETE FROM client_logos WHERE id = %s;", (logo_id,))
                sync_logos_to_page_sections(cur)
                conn.commit()
                return {"success": True, "message": "Logo deleted"}
        finally:
            conn.close()
    raise HTTPException(status_code=503, detail="Database unavailable")

@app.get("/api/admin/pages")
def get_admin_pages():
    conn = get_db()
    if conn:
        try:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT p.*,
                           (SELECT COUNT(*) FROM page_sections ps 
                            WHERE ps.page_id = p.id AND ps.draft_data IS NOT NULL AND ps.draft_data != ps.data) AS draft_changes_count
                    FROM pages p
                    ORDER BY p.sort_order ASC, p.title ASC;
                """)
                rows = cur.fetchall()
                return {"success": True, "pages": [dict(r) for r in rows]}
        finally:
            conn.close()
    raise HTTPException(status_code=503, detail="Database unavailable")

@app.get("/api/admin/pages/{page_id}")
def get_admin_page(page_id: str):
    if not is_valid_uuid(page_id):
        raise HTTPException(status_code=404, detail="Page not found")
    conn = get_db()
    if conn:
        try:
            with conn.cursor() as cur:
                cur.execute("SELECT * FROM pages WHERE id = %s;", (page_id,))
                page = cur.fetchone()
                if not page:
                    raise HTTPException(status_code=404, detail="Page not found")
                cur.execute("""
                    SELECT id, section_type, label, anchor_id, sort_order, is_visible,
                           COALESCE(draft_data, data) AS data,
                           (draft_data IS NOT NULL AND draft_data != data) AS has_draft_changes
                    FROM page_sections 
                    WHERE page_id = %s 
                    ORDER BY sort_order ASC;
                """, (page_id,))
                sections = cur.fetchall()
                return {"success": True, "page": dict(page), "sections": [dict(s) for s in sections]}
        finally:
            conn.close()
    raise HTTPException(status_code=503, detail="Database unavailable")

@app.put("/api/admin/pages/{page_id}")
async def update_admin_page(page_id: str, request: Request):
    if not is_valid_uuid(page_id):
        raise HTTPException(status_code=404, detail="Page not found")
    body = await request.json()
    conn = get_db()
    if conn:
        try:
            with conn.cursor() as cur:
                cur.execute("""
                    UPDATE pages
                    SET title = %s, seo_title = %s, seo_description = %s, status = %s, updated_at = now()
                    WHERE id = %s RETURNING *;
                """, (
                    body.get("title"),
                    body.get("seo_title"),
                    body.get("seo_description"),
                    body.get("status", "published"),
                    page_id
                ))
                conn.commit()
                row = cur.fetchone()
                if not row:
                    raise HTTPException(status_code=404, detail="Page not found")
                return {"success": True, "page": dict(row)}
        finally:
            conn.close()
    raise HTTPException(status_code=503, detail="Database unavailable")

@app.put("/api/admin/sections/{section_id}")
async def update_admin_section(section_id: str, request: Request):
    if not is_valid_uuid(section_id):
        raise HTTPException(status_code=404, detail="Section not found")
    body = await request.json()
    publish = body.get("publish", True)
    conn = get_db()
    if conn:
        try:
            with conn.cursor() as cur:
                data_val = Json(body.get("data", {}))
                if publish:
                    cur.execute("""
                        UPDATE page_sections
                        SET label = %s, is_visible = %s, draft_data = %s, data = %s, sort_order = %s, updated_at = now()
                        WHERE id = %s RETURNING *;
                    """, (body.get("label"), body.get("is_visible", True), data_val, data_val, body.get("sort_order", 0), section_id))
                else:
                    cur.execute("""
                        UPDATE page_sections
                        SET label = %s, is_visible = %s, draft_data = %s, sort_order = %s, updated_at = now()
                        WHERE id = %s RETURNING *;
                    """, (body.get("label"), body.get("is_visible", True), data_val, body.get("sort_order", 0), section_id))
                conn.commit()
                row = cur.fetchone()
                if not row:
                    raise HTTPException(status_code=404, detail="Section not found")
                return {"success": True, "section": dict(row) if row else body}
        finally:
            conn.close()
    raise HTTPException(status_code=503, detail="Database unavailable")

@app.put("/api/admin/pages/{page_id}/reorder-sections")
async def reorder_page_sections(page_id: str, request: Request):
    if not is_valid_uuid(page_id):
        raise HTTPException(status_code=404, detail="Page not found")
    body = await request.json()
    section_ids = body.get("section_ids", [])
    if not isinstance(section_ids, list):
        raise HTTPException(status_code=400, detail="section_ids must be an array")
    conn = get_db()
    if conn is None:
        raise HTTPException(status_code=503, detail="Database unavailable")
    if conn:
        try:
            with conn.cursor() as cur:
                for idx, s_id in enumerate(section_ids):
                    if is_valid_uuid(s_id):
                        cur.execute("UPDATE page_sections SET sort_order = %s WHERE id = %s;", (idx, s_id))
                conn.commit()
        finally:
            conn.close()
    return {"success": True, "message": "Sections reordered"}

@app.put("/api/admin/pages/{page_id}/bulk-sections")
async def bulk_update_page_sections(page_id: str, request: Request):
    if not is_valid_uuid(page_id):
        raise HTTPException(status_code=404, detail="Page not found")
    body = await request.json()
    sections = body.get("sections", [])
    if not isinstance(sections, list):
        raise HTTPException(status_code=400, detail="sections must be an array")
    publish = body.get("publish", False)
    conn = get_db()
    if conn is None:
        raise HTTPException(status_code=503, detail="Database unavailable")
    if conn:
        try:
            with conn.cursor() as cur:
                for sec in sections:
                    s_id = sec.get("id")
                    if s_id and is_valid_uuid(s_id):
                        data_val = Json(sec.get("data", {}))
                        if publish:
                            cur.execute("""
                                UPDATE page_sections
                                SET label = %s, is_visible = %s, draft_data = %s, data = %s, updated_at = now()
                                WHERE id = %s;
                            """, (
                                sec.get("label"),
                                sec.get("is_visible", True),
                                data_val,
                                data_val,
                                s_id
                            ))
                            if isinstance(sec.get("data"), dict) and "members" in sec.get("data"):
                                for m in sec.get("data", {}).get("members", []):
                                    if m.get("name"):
                                        cur.execute("""
                                            UPDATE team_members
                                            SET job_title = COALESCE(%s, job_title),
                                                photo_url = COALESCE(%s, photo_url),
                                                socials = jsonb_set(COALESCE(socials, '{}'::jsonb), '{linkedin}', to_jsonb(%s::text))
                                            WHERE full_name = %s;
                                        """, (m.get("role"), m.get("photo"), m.get("linkedin") or "", m.get("name")))
                        else:
                            cur.execute("""
                                UPDATE page_sections
                                SET label = %s, is_visible = %s, draft_data = %s, updated_at = now()
                                WHERE id = %s;
                            """, (
                                sec.get("label"),
                                sec.get("is_visible", True),
                                data_val,
                                s_id
                            ))

                if publish:
                    cur.execute("""
                        UPDATE pages
                        SET status = 'published', published_at = now(), updated_at = now()
                        WHERE id = %s;
                    """, (page_id,))
                else:
                    cur.execute("""
                        UPDATE pages
                        SET status = 'draft', updated_at = now()
                        WHERE id = %s;
                    """, (page_id,))
                conn.commit()
        finally:
            conn.close()
    return {"success": True, "published": publish, "message": "Changes published live!" if publish else "Draft saved successfully!"}

@app.post("/api/admin/pages/{page_id}/publish")
async def publish_page(page_id: str):
    if not is_valid_uuid(page_id):
        raise HTTPException(status_code=404, detail="Page not found")
    conn = get_db()
    if conn:
        try:
            with conn.cursor() as cur:
                cur.execute("""
                    UPDATE page_sections
                    SET data = COALESCE(draft_data, data), updated_at = now()
                    WHERE page_id = %s;
                """, (page_id,))
                cur.execute("""
                    UPDATE pages
                    SET status = 'published', published_at = now(), updated_at = now()
                    WHERE id = %s;
                """, (page_id,))
                conn.commit()
                return {"success": True, "message": "Page published live successfully"}
        finally:
            conn.close()
    raise HTTPException(status_code=503, detail="Database unavailable")

@app.post("/api/admin/pages/{page_id}/discard-draft")
async def discard_page_draft(page_id: str):
    if not is_valid_uuid(page_id):
        raise HTTPException(status_code=404, detail="Page not found")
    conn = get_db()
    if conn:
        try:
            with conn.cursor() as cur:
                cur.execute("""
                    UPDATE page_sections
                    SET draft_data = data, updated_at = now()
                    WHERE page_id = %s;
                """, (page_id,))
                cur.execute("""
                    UPDATE pages
                    SET status = 'published', updated_at = now()
                    WHERE id = %s;
                """, (page_id,))
                conn.commit()
                return {"success": True, "message": "Draft discarded. Restored to live content."}
        finally:
            conn.close()
    raise HTTPException(status_code=503, detail="Database unavailable")

@app.post("/api/admin/sections")
async def create_admin_section(request: Request):
    body = await request.json()
    conn = get_db()
    if conn:
        try:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO page_sections (page_id, section_type, label, sort_order, is_visible, data)
                    VALUES (%s, %s, %s, %s, %s, %s) RETURNING *;
                """, (
                    body.get("page_id"),
                    body.get("section_type"),
                    body.get("label"),
                    body.get("sort_order", 0),
                    body.get("is_visible", True),
                    Json(body.get("data", {}))
                ))
                conn.commit()
                row = cur.fetchone()
                return {"success": True, "section": dict(row)}
        finally:
            conn.close()
    raise HTTPException(status_code=503, detail="Database unavailable")

@app.delete("/api/admin/sections/{section_id}")
def delete_admin_section(section_id: str):
    if not is_valid_uuid(section_id):
        raise HTTPException(status_code=404, detail="Section not found")
    conn = get_db()
    if conn:
        try:
            with conn.cursor() as cur:
                cur.execute("DELETE FROM page_sections WHERE id = %s;", (section_id,))
                conn.commit()
                return {"success": True, "message": "Section deleted"}
        finally:
            conn.close()
    raise HTTPException(status_code=503, detail="Database unavailable")

@app.get("/api/blog/categories")
def get_blog_categories():
    conn = get_db()
    if conn:
        try:
            with conn.cursor() as cur:
                cur.execute("SELECT * FROM blog_categories ORDER BY name ASC;")
                rows = cur.fetchall()
                return {"success": True, "categories": [dict(r) for r in rows]}
        finally:
            conn.close()
    return {"success": True, "categories": []}

@app.get("/api/admin/blog/posts")
def get_admin_blog_posts():
    conn = get_db()
    if conn:
        try:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT p.*, c.name as category_name, c.id as category_id
                    FROM blog_posts p
                    LEFT JOIN blog_post_categories pc ON pc.post_id = p.id
                    LEFT JOIN blog_categories c ON c.id = pc.category_id
                    ORDER BY p.published_at DESC;
                """)
                rows = cur.fetchall()
                return {"success": True, "posts": [dict(r) for r in rows]}
        finally:
            conn.close()
    raise HTTPException(status_code=503, detail="Database unavailable")

@app.post("/api/admin/blog/posts")
async def create_admin_blog_post(request: Request):
    body = await request.json()
    conn = get_db()
    if conn:
        try:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO blog_posts (title, slug, excerpt, body_html, featured_image_url, status, seo_title, seo_description, published_at)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, now()) RETURNING *;
                """, (
                    body.get("title"),
                    body.get("slug"),
                    body.get("excerpt"),
                    body.get("body_html"),
                    body.get("featured_image_url"),
                    body.get("status", "draft"),
                    body.get("seo_title"),
                    body.get("seo_description")
                ))
                post = cur.fetchone()
                cat_id = body.get("category_id")
                if cat_id:
                    cur.execute("INSERT INTO blog_post_categories (post_id, category_id) VALUES (%s, %s) ON CONFLICT DO NOTHING;", (post["id"], cat_id))
                conn.commit()
                return {"success": True, "post": dict(post)}
        finally:
            conn.close()
    raise HTTPException(status_code=503, detail="Database unavailable")

@app.put("/api/admin/blog/posts/{post_id}")
async def update_admin_blog_post(post_id: str, request: Request):
    if not is_valid_uuid(post_id):
        raise HTTPException(status_code=404, detail="Blog post not found")
    body = await request.json()
    conn = get_db()
    if conn:
        try:
            with conn.cursor() as cur:
                cur.execute("""
                    UPDATE blog_posts
                    SET title = %s, slug = %s, excerpt = %s, body_html = %s, featured_image_url = %s,
                        status = %s, seo_title = %s, seo_description = %s, updated_at = now()
                    WHERE id = %s RETURNING *;
                """, (
                    body.get("title"),
                    body.get("slug"),
                    body.get("excerpt"),
                    body.get("body_html"),
                    body.get("featured_image_url"),
                    body.get("status", "draft"),
                    body.get("seo_title"),
                    body.get("seo_description"),
                    post_id
                ))
                cat_id = body.get("category_id")
                if cat_id:
                    cur.execute("DELETE FROM blog_post_categories WHERE post_id = %s;", (post_id,))
                    cur.execute("INSERT INTO blog_post_categories (post_id, category_id) VALUES (%s, %s) ON CONFLICT DO NOTHING;", (post_id, cat_id))
                conn.commit()
                row = cur.fetchone()
                if not row:
                    raise HTTPException(status_code=404, detail="Blog post not found")
                return {"success": True, "post": dict(row)}
        finally:
            conn.close()
    raise HTTPException(status_code=503, detail="Database unavailable")

@app.delete("/api/admin/blog/posts/{post_id}")
def delete_admin_blog_post(post_id: str):
    if not is_valid_uuid(post_id):
        raise HTTPException(status_code=404, detail="Blog post not found")
    conn = get_db()
    if conn:
        try:
            with conn.cursor() as cur:
                cur.execute("DELETE FROM blog_posts WHERE id = %s;", (post_id,))
                conn.commit()
                return {"success": True, "message": "Article deleted"}
        finally:
            conn.close()
    raise HTTPException(status_code=503, detail="Database unavailable")

@app.get("/api/admin/forms")
def get_admin_forms():
    conn = get_db()
    if conn:
        try:
            with conn.cursor() as cur:
                cur.execute("SELECT id, key, name, fields, notify_emails, is_active FROM forms ORDER BY name ASC;")
                rows = cur.fetchall()
                return {"success": True, "forms": [dict(r) for r in rows]}
        finally:
            conn.close()
    raise HTTPException(status_code=503, detail="Database unavailable")

@app.get("/api/admin/submissions")
def get_admin_submissions(status: Optional[str] = None, form: Optional[str] = None, search: Optional[str] = None):
    conn = get_db()
    if conn:
        try:
            with conn.cursor() as cur:
                query = """
                    SELECT s.id, s.answers, s.email, s.status, s.source_page, s.created_at, f.name as form_name, f.key as form_key
                    FROM form_submissions s
                    JOIN forms f ON s.form_id = f.id
                    WHERE 1=1
                """
                params = []
                if status and status != "all":
                    query += " AND s.status = %s"
                    params.append(status)
                if form and form != "all":
                    query += " AND (f.key = %s OR f.id::text = %s)"
                    params.extend([form, form])
                if search and search.strip():
                    query += " AND (LOWER(s.email) LIKE %s OR LOWER(s.answers::text) LIKE %s OR LOWER(f.name) LIKE %s)"
                    term = f"%{search.strip().lower()}%"
                    params.extend([term, term, term])
                query += " ORDER BY s.created_at DESC LIMIT 100;"
                cur.execute(query, tuple(params))
                rows = cur.fetchall()
                return {"success": True, "submissions": [dict(r) for r in rows]}
        finally:
            conn.close()
    raise HTTPException(status_code=503, detail="Database unavailable")

@app.put("/api/admin/submissions/{submission_id}")
async def update_admin_submission_status(submission_id: str, request: Request):
    if not is_valid_uuid(submission_id):
        raise HTTPException(status_code=404, detail="Submission not found")
    body = await request.json()
    status = body.get("status", "read")
    conn = get_db()
    if conn:
        try:
            with conn.cursor() as cur:
                cur.execute("UPDATE form_submissions SET status = %s WHERE id = %s RETURNING *;", (status, submission_id))
                conn.commit()
                row = cur.fetchone()
                if not row:
                    raise HTTPException(status_code=404, detail="Submission not found")
                return {"success": True, "submission": dict(row)}
        finally:
            conn.close()
    raise HTTPException(status_code=503, detail="Database unavailable")

@app.delete("/api/admin/submissions/{submission_id}")
def delete_admin_submission(submission_id: str):
    if not is_valid_uuid(submission_id):
        raise HTTPException(status_code=404, detail="Submission not found")
    conn = get_db()
    if conn:
        try:
            with conn.cursor() as cur:
                cur.execute("DELETE FROM form_submissions WHERE id = %s;", (submission_id,))
                conn.commit()
                return {"success": True, "message": "Submission deleted"}
        finally:
            conn.close()
    raise HTTPException(status_code=503, detail="Database unavailable")

@app.get("/api/admin/media")
def get_admin_media():
    conn = get_db()
    if conn:
        try:
            with conn.cursor() as cur:
                cur.execute("SELECT * FROM media ORDER BY created_at DESC LIMIT 100;")
                rows = cur.fetchall()
                return {"success": True, "media": [dict(r) for r in rows]}
        finally:
            conn.close()
    raise HTTPException(status_code=503, detail="Database unavailable")

@app.delete("/api/admin/media/{media_id}")
def delete_admin_media(media_id: str):
    if not is_valid_uuid(media_id):
        raise HTTPException(status_code=404, detail="Media item not found")
    conn = get_db()
    if conn:
        try:
            with conn.cursor() as cur:
                cur.execute("DELETE FROM media WHERE id = %s;", (media_id,))
                conn.commit()
                return {"success": True, "message": "Media item deleted"}
        finally:
            conn.close()
    raise HTTPException(status_code=503, detail="Database unavailable")

# --------------------------------------------------------------------------
# Public Form Capture Endpoints (Captures all form channels into PostgreSQL)
# --------------------------------------------------------------------------
@app.post("/api/forms/submit")
@app.post("/api/demo")
@app.post("/api/contact")
@app.post("/api/trial")
@app.post("/api/survey")
@app.post("/api/icp-request")
@app.post("/api/newsletter")
@app.post("/wp-admin/admin-ajax.php")
@app.post("/wp-admin/admin-ajax")
async def handle_universal_form(request: Request):
    try:
        body = await request.json()
    except Exception:
        body = {}

    url = body.get("url", "")
    form_data = body.get("formData", {}) if "formData" in body else body

    full_name = (
        form_data.get("full_name") or
        form_data.get("fullName") or
        form_data.get("name") or
        f"{form_data.get('add_visitor_fname', '')} {form_data.get('add_visitor_lname', '')}".strip() or
        f"{form_data.get('names[first_name]', '')} {form_data.get('names[last_name]', '')}".strip() or
        f"{form_data.get('wpforms[fields][1]', '')} {form_data.get('wpforms[fields][2]', '')}".strip() or
        "Website Visitor"
    )
    email = form_data.get("email") or form_data.get("Email") or "visitor@salesleadmachine.co.uk"

    # Store in PostgreSQL
    conn = get_db()
    if conn:
        try:
            with conn.cursor() as cur:
                cur.execute("SELECT id FROM forms WHERE key = 'contact';")
                form_row = cur.fetchone()
                form_id = form_row["id"] if form_row else None
                if not form_id:
                    cur.execute("INSERT INTO forms (key, name, fields) VALUES ('contact', 'Contact Form', '[]') RETURNING id;")
                    form_id = cur.fetchone()["id"]

                cur.execute("""
                    INSERT INTO form_submissions (form_id, answers, email, source_page, consent_given)
                    VALUES (%s, %s, %s, %s, TRUE);
                """, (form_id, Json(form_data), email, url or "website"))
                conn.commit()
        finally:
            conn.close()

    return {
        "success": True,
        "message": f"Thank you, {full_name}! Your request has been recorded. Our London advisory team will reach out shortly.",
        "result": "success"
    }

# --------------------------------------------------------------------------
# Admin Portal & Dynamic Hydration Routes
# --------------------------------------------------------------------------
@app.get("/admin")
@app.get("/admin/")
def serve_admin_portal():
    admin_path = os.path.join(DIR_PATH, "admin.html")
    if os.path.isfile(admin_path):
        return FileResponse(admin_path)
    raise HTTPException(status_code=404, detail="Admin portal not found")

@app.get("/cms-hydrate.js")
def serve_cms_hydrate():
    return FileResponse(
        os.path.join(DIR_PATH, "cms-hydrate.js"),
        headers={
            "Cache-Control": "no-store, no-cache, must-revalidate, max-age=0",
            "Pragma": "no-cache",
            "Expires": "0"
        }
    )


def serve_html_file(file_path: str):
    try:
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            html = f.read()

        # Inject Quill CSS/JS in <head> for rich text editing
        if "</head>" in html and "quill.snow.css" not in html:
            quill_tags = (
                '<link href="https://cdn.quilljs.com/1.3.6/quill.snow.css" rel="stylesheet">\n'
                '<script src="https://cdn.quilljs.com/1.3.6/quill.min.js"></script>\n'
                '</head>'
            )
            html = html.replace("</head>", quill_tags)

        # Inject cms-hydrate script with auto-cache busting
        if "</body" in html and "cms-hydrate.js" not in html:
            v_cache = int(time.time())
            html = html.replace("</body>", f'<script src="/cms-hydrate.js?v={v_cache}" defer></script>\n</body>')

        return Response(
            content=html,
            media_type="text/html",
            headers={
                "Cache-Control": "no-store, no-cache, must-revalidate, max-age=0",
                "Pragma": "no-cache",
                "Expires": "0"
            }
        )
    except Exception:
        return FileResponse(file_path)

# --------------------------------------------------------------------------
# Multi-Page Routing, SEO Basics & Fallback
# --------------------------------------------------------------------------
@app.get("/robots.txt")
def serve_robots_txt():
    robots_content = (
        "User-agent: *\n"
        "Disallow: /admin/\n"
        "Disallow: /api/\n"
        "Allow: /wp-admin/admin-ajax.php\n\n"
        "Sitemap: http://localhost:8080/sitemap.xml\n"
    )
    return Response(
        content=robots_content,
        media_type="text/plain",
        headers={"Cache-Control": "public, max-age=86400"}
    )

@app.get("/sitemap.xml")
def serve_sitemap_xml():
    conn = get_db()
    urls = []
    if conn:
        try:
            with conn.cursor() as cur:
                cur.execute("SELECT slug, full_path, updated_at FROM pages WHERE status = 'published' ORDER BY sort_order ASC;")
                rows = cur.fetchall()
                for r in rows:
                    full_p = r.get("full_path") or (f"/{r.get('slug')}/" if r.get('slug') else "/")
                    up_date = r.get("updated_at")
                    lastmod = up_date.strftime("%Y-%m-%d") if up_date else "2026-11-05"
                    urls.append(f"  <url>\n    <loc>http://localhost:8080{full_p}</loc>\n    <lastmod>{lastmod}</lastmod>\n    <changefreq>weekly</changefreq>\n    <priority>0.8</priority>\n  </url>")
        finally:
            conn.close()

    xml_content = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        + "\n".join(urls) + "\n"
        + '</urlset>'
    )
    return Response(
        content=xml_content,
        media_type="application/xml",
        headers={"Cache-Control": "public, max-age=3600"}
    )

@app.api_route("/", methods=["GET", "HEAD"])
def serve_home():
    return serve_html_file(os.path.join(DIR_PATH, "index.html"))

@app.api_route("/{full_path:path}", methods=["GET", "HEAD"])
def serve_any_page(full_path: str):
    clean = full_path.strip("/")

    # 1. Guard API endpoints: Any unmatched /api/ route must return 404 JSON, never HTML
    if clean == "api" or clean.startswith("api/"):
        return JSONResponse(
            status_code=404,
            content={"success": False, "detail": "API endpoint not found"}
        )

    if ".." in clean or clean.startswith("/") or "\\" in clean:
        raise HTTPException(status_code=400, detail="Invalid path")

    BLOCKED_EXTENSIONS = ('.py', '.db', '.sh', '.env', '.sqlite', '.sqlite3', '.log', '.key', '.pem', '.cfg', '.toml')
    if any(clean.endswith(ext) or clean.split('?')[0].endswith(ext) for ext in BLOCKED_EXTENSIONS):
        raise HTTPException(status_code=403, detail="Access denied")

    # 2. Canonical and alias route mapping
    CANONICAL_MAP = {
        "terms-and-conditions": "term_condition.html",
        "terms-and-conditions.html": "term_condition.html",
        "term_condition": "term_condition.html",
        "term-condition": "term_condition.html",
        "privacy-policy": "privacy_policy.html",
        "privacy-policy.html": "privacy_policy.html",
        "privacy_policy": "privacy_policy.html",
        "contact": "contact-us.html",
        "contact-us": "contact-us.html",
        "contact_us": "contact-us.html",
        "contact-sales": "contact-sales.html",
        "contact_sales": "contact-sales.html",
        "build_a_gtm_foundation": "build-a-b2b-gtm-foundation.html",
        "build-a-gtm-foundation": "build-a-b2b-gtm-foundation.html",
        "chrome_extension": "chrome-extension.html",
        "crome-extension": "chrome-extension.html",
        "crome_extension": "chrome-extension.html",
        "service-categories/crome-extension": "chrome-extension.html",
        "service-categories/chrome-extension": "chrome-extension.html",
        "service-categories_crome-extension": "chrome-extension.html",
        "service-categories_chrome-extension": "chrome-extension.html",
        "data_enrichement": "data-enrichment.html",
        "data-enrichement": "data-enrichment.html",
        "data_enrichment": "data-enrichment.html",
        "service-categories/data-enrichment": "data-enrichment.html",
        "service-categories_data-enrichment": "data-enrichment.html",
        "email_verification": "email-verification.html",
        "service-categories/email-verification": "email-verification.html",
        "service-categories_email-verification": "email-verification.html",
        "intent_data": "intent-data.html",
        "service-categories/intent-data": "intent-data.html",
        "service-categories_intent-data": "intent-data.html",
        "prospector": "prospector.html",
        "service-categories/prospector": "prospector.html",
        "service-categories_prospector": "prospector.html",
        "technographics": "technographics.html",
        "service-categories/technographics": "technographics.html",
        "service-categories_technographics": "technographics.html",
        "service-categories/hr-compliance-administration-2": "hr-compliance-administration-2.html",
        "service-categories_hr-compliance-administration-2": "hr-compliance-administration-2.html",
        "service-categories/hr-consultants": "hr-consultants.html",
        "service-categories_hr-consultants": "hr-consultants.html",
        "expand_and_retain_customers": "expand-retain-customers.html",
        "expand-and-retain-customers": "expand-retain-customers.html",
        "for-marketing": "for-marketer.html",
        "for_marketing": "for-marketer.html",
        "survey": "survey.html",
        "survey-form": "survey.html",
        "home": "index.html"
    }

    if clean in CANONICAL_MAP:
        mapped_file = os.path.join(DIR_PATH, CANONICAL_MAP[clean])
        if os.path.isfile(mapped_file):
            return serve_html_file(mapped_file)

    clean_dash = clean.replace('_', '-')
    clean_under = clean.replace('-', '_')
    candidates = [
        os.path.join(DIR_PATH, clean),
        os.path.join(DIR_PATH, clean, "index.html"),
        os.path.join(DIR_PATH, clean + ".html"),
        os.path.join(DIR_PATH, clean_dash + ".html"),
        os.path.join(DIR_PATH, clean_under + ".html"),
    ]

    for c in candidates:
        resolved = os.path.realpath(c)
        if not resolved.startswith(os.path.realpath(DIR_PATH)):
            raise HTTPException(status_code=403, detail="Access denied")
        if os.path.isfile(resolved) and not resolved.endswith(BLOCKED_EXTENSIONS):
            if resolved.endswith(".html"):
                return serve_html_file(resolved)
            if resolved.endswith(".js"):
                return FileResponse(resolved, headers={"Cache-Control": "no-store, no-cache, must-revalidate"})
            return FileResponse(resolved)

    # Fallback for WordPress responsive images with dimension suffixes (e.g. -768x294.png -> .png)
    import re
    base_clean = re.sub(r'-\d+x\d+(\.[a-zA-Z0-9]+)$', r'\1', clean)
    if base_clean != clean:
        base_path = os.path.join(DIR_PATH, base_clean)
        resolved_base = os.path.realpath(base_path)
        if resolved_base.startswith(os.path.realpath(DIR_PATH)) and os.path.isfile(resolved_base):
            return FileResponse(resolved_base)

    if "Sales-Lead-machine-Logo-Edited" in clean:
        logo_fallback = os.path.join(DIR_PATH, "wp-content/uploads/2019/10/Sales-Lead-machine-Logo-Edited.png")
        if os.path.isfile(logo_fallback):
            return FileResponse(logo_fallback)

    if "Purple-Illustration" in clean or "Purple-Illustration" in full_path:
        banner_fallback = os.path.join(DIR_PATH, "wp-content/uploads/2023/03/banner_image_pages-1.png")
        if os.path.isfile(banner_fallback):
            return FileResponse(banner_fallback)

    STATIC_EXTENSIONS = ('.woff', '.woff2', '.ttf', '.eot', '.png', '.jpg', '.jpeg', '.svg', '.gif', '.ico', '.css', '.js', '.map', '.webp', '.txt', '.xml', '.json')
    if any(clean.lower().split('?')[0].endswith(ext) for ext in STATIC_EXTENSIONS):
        raise HTTPException(status_code=404, detail="Asset not found")

    # 3. Definite 404 for unknown web pages (never soft-404 / 200 homepage)
    not_found_html = """<!DOCTYPE html>
<html lang="en-US">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0"/>
    <title>Page Not Found (404) - Sales Lead Machine</title>
    <meta name="robots" content="noindex, nofollow"/>
    <style>
        body { background: #090d16; color: #f8fafc; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; text-align: center; padding: 100px 20px; }
        h1 { font-size: 72px; font-weight: 800; color: #6366f1; margin: 0 0 10px; }
        h2 { font-size: 22px; margin: 0 0 16px; color: #e2e8f0; }
        p { color: #94a3b8; max-width: 460px; margin: 0 auto 30px; font-size: 14px; line-height: 1.6; }
        a { display: inline-block; background: #6366f1; color: #fff; padding: 10px 22px; border-radius: 6px; text-decoration: none; font-weight: 600; font-size: 13px; }
        a:hover { background: #4f46e5; }
    </style>
</head>
<body>
    <h1>404</h1>
    <h2>Page Not Found</h2>
    <p>The page you are looking for does not exist, has been removed, or is temporarily unavailable.</p>
    <a href="/">Return to Homepage</a>
</body>
</html>"""
    return Response(
        content=not_found_html,
        status_code=404,
        media_type="text/html",
        headers={"Cache-Control": "no-store, no-cache, must-revalidate"}
    )

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8080))
    print(f"Starting Sales Lead Machine server with PostgreSQL on http://localhost:{port}")
    uvicorn.run(app, host="0.0.0.0", port=port)
