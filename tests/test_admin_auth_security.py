#!/usr/bin/env python3
"""
Comprehensive Security Verification Test Suite: Admin Authentication
Tests strict password verification, username alias normalization, rejection of
common fallback passwords, protected route guards, and fail-secure error handling.
"""

import os
import sys
import json
import unittest
import urllib.request
import urllib.error

# Ensure test_config and repository modules are importable
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from test_config import (
    BASE_URL,
    ADMIN_EMAIL,
    ADMIN_PASSWORD,
    assert_safe_test_environment,
    get_db_connection
)

assert_safe_test_environment()


class TestAdminAuthSecurity(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        assert_safe_test_environment()
        if not ADMIN_PASSWORD:
            raise RuntimeError("TEST_ADMIN_PASSWORD environment variable must be set for security regression tests.")

    def _post_login(self, email_or_alias: str, password: str):
        url = f"{BASE_URL}/api/admin/login"
        payload = json.dumps({"email": email_or_alias, "password": password}).encode("utf-8")
        req = urllib.request.Request(
            url,
            data=payload,
            headers={"Content-Type": "application/json"}
        )
        try:
            with urllib.request.urlopen(req) as resp:
                return resp.status, json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            body = e.read().decode("utf-8")
            try:
                data = json.loads(body)
            except Exception:
                data = {"raw": body}
            return e.code, data

    def test_01_valid_login_with_admin_alias(self):
        """1. Correct configured credentials work with 'admin' alias."""
        status, data = self._post_login("admin", ADMIN_PASSWORD)
        self.assertEqual(status, 200, f"Expected 200 OK for 'admin' alias, got {status}: {data}")
        self.assertTrue(data.get("success"), "Response should indicate success: true")
        self.assertIn("token", data, "Response must include a JWT authentication token")
        self.assertEqual(data.get("user", {}).get("role"), "admin", "User role must be admin")
        self.assertEqual(data.get("user", {}).get("email"), "admin@salesleadmachine.co.uk")

    def test_02_valid_login_with_full_email(self):
        """2. Correct configured credentials work with canonical admin email."""
        status, data = self._post_login(ADMIN_EMAIL, ADMIN_PASSWORD)
        self.assertEqual(status, 200, f"Expected 200 OK for full email, got {status}: {data}")
        self.assertTrue(data.get("success"), "Response should indicate success: true")
        self.assertIn("token", data, "Response must include a JWT authentication token")
        self.assertEqual(data.get("user", {}).get("role"), "admin", "User role must be admin")

    def test_03_incorrect_password_rejected(self):
        """3. Incorrect passwords are strictly rejected with 401."""
        status, data = self._post_login("admin", "DefinitelyWrongPassword!999")
        self.assertEqual(status, 401, f"Expected 401 Unauthorized for incorrect password, got {status}")
        self.assertEqual(data.get("detail"), "Invalid admin credentials")

        status, data = self._post_login(ADMIN_EMAIL, "AnotherWrongPassword#888")
        self.assertEqual(status, 401, f"Expected 401 Unauthorized for incorrect password, got {status}")
        self.assertEqual(data.get("detail"), "Invalid admin credentials")

    def test_04_common_fallback_passwords_strictly_rejected(self):
        """4. Common fallback passwords are NOT accepted."""
        insecure_passwords = [
            "admin",
            "admin123",
            "Admin@123",
            "Admin123!",
            "password",
            "123456",
            "root",
            "salesleadmachine",
            "SLM_Admin_8b0SpEACDD-hWfa0oy1DS-yDevigE2nH!"  # Rotated old credential
        ]

        for insecure_pw in insecure_passwords:
            # Skip if accidentally identical to the new real rotated password
            if insecure_pw == ADMIN_PASSWORD:
                continue

            # Test with username alias
            status, data = self._post_login("admin", insecure_pw)
            self.assertEqual(
                status, 401,
                f"SECURITY FLAW: Insecure password '{insecure_pw}' was accepted for user 'admin'!"
            )
            self.assertEqual(data.get("detail"), "Invalid admin credentials")

            # Test with full canonical email
            status, data = self._post_login(ADMIN_EMAIL, insecure_pw)
            self.assertEqual(
                status, 401,
                f"SECURITY FLAW: Insecure password '{insecure_pw}' was accepted for user '{ADMIN_EMAIL}'!"
            )
            self.assertEqual(data.get("detail"), "Invalid admin credentials")

    def test_05_missing_credentials_fail_securely(self):
        """5. Missing username or password fails securely with 401."""
        test_cases = [
            ("", ADMIN_PASSWORD),
            ("admin", ""),
            ("", ""),
            ("   ", "   "),
        ]
        for user_id, pw in test_cases:
            status, data = self._post_login(user_id, pw)
            self.assertEqual(status, 401, f"Expected 401 for empty credentials, got {status}: {data}")
            self.assertEqual(data.get("detail"), "Invalid admin credentials")

    def test_06_protected_admin_routes_reject_unauthenticated(self):
        """6. Protected routes remain inaccessible without valid JWT bearer token."""
        protected_endpoints = [
            ("GET", "/api/admin/settings"),
            ("GET", "/api/admin/team"),
            ("GET", "/api/admin/logos"),
            ("POST", "/api/admin/media/upload"),
            ("PUT", "/api/admin/settings/general"),
        ]

        for method, endpoint in protected_endpoints:
            url = f"{BASE_URL}{endpoint}"
            req = urllib.request.Request(url, method=method)
            try:
                with urllib.request.urlopen(req) as resp:
                    self.fail(f"SECURITY FLAW: Protected route {endpoint} returned {resp.status} without auth token!")
            except urllib.error.HTTPError as e:
                self.assertEqual(
                    e.code, 401,
                    f"Protected route {endpoint} must return 401 Unauthorized, got {e.code}"
                )

    def test_07_tampered_jwt_token_rejected(self):
        """7. Modified or forged JWT tokens are rejected."""
        # Get a real token first
        status, data = self._post_login("admin", ADMIN_PASSWORD)
        self.assertEqual(status, 200)
        real_token = data["token"]

        # Tamper signature (flip last 4 characters)
        tampered_token = real_token[:-4] + "WXYZ"

        req = urllib.request.Request(
            f"{BASE_URL}/api/admin/settings",
            headers={"Authorization": f"Bearer {tampered_token}"}
        )
        try:
            with urllib.request.urlopen(req) as resp:
                self.fail("SECURITY FLAW: Tampered JWT token was accepted!")
        except urllib.error.HTTPError as e:
            self.assertEqual(e.code, 401, f"Tampered token must return 401, got {e.code}")

    def test_08_no_credentials_leaked_in_error_payloads(self):
        """8. Authentication error responses never leak stack traces or internal configuration."""
        status, data = self._post_login("unknown_user_test", "some_password")
        self.assertEqual(status, 401)
        data_str = json.dumps(data)
        self.assertNotIn("password_hash", data_str)
        self.assertNotIn("Traceback", data_str)
        self.assertNotIn("PostgreSQL", data_str)
        self.assertNotIn("SELECT", data_str)
        self.assertEqual(data.get("detail"), "Invalid admin credentials")


if __name__ == "__main__":
    unittest.main()
