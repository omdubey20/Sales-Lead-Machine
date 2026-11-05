"""
Unit tests for the Step 6D environment safeguard guardrail (assert_safe_test_environment).
Proves that localhost and authorized staging pass, while production domains and public IP targets are strictly aborted.
"""

import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from test_config import assert_safe_test_environment

class TestEnvironmentGuard(unittest.TestCase):

    def test_localhost_http_allowed(self):
        """Verify standard localhost targets are permitted."""
        self.assertTrue(assert_safe_test_environment("http://localhost:8080", db_host="127.0.0.1"))

    def test_ipv4_loopback_allowed(self):
        """Verify 127.0.0.1 loopback is permitted."""
        self.assertTrue(assert_safe_test_environment("http://127.0.0.1:8080", db_host="localhost"))

    def test_ipv6_loopback_allowed(self):
        """Verify IPv6 loopback is permitted."""
        self.assertTrue(assert_safe_test_environment("http://[::1]:8080", db_host="127.0.0.1"))

    def test_local_domain_suffix_allowed(self):
        """Verify .local and .test domains are permitted."""
        self.assertTrue(assert_safe_test_environment("http://staging.app.local:3000", db_host="localhost"))
        self.assertTrue(assert_safe_test_environment("http://ci.dev.test:8000", db_host="localhost"))

    def test_production_apex_domain_rejected(self):
        """Verify salesleadmachine.co.uk is rejected."""
        with self.assertRaises(RuntimeError) as ctx:
            assert_safe_test_environment("https://salesleadmachine.co.uk")
        self.assertIn("[SECURITY ABORT]", str(ctx.exception))
        self.assertIn("production host", str(ctx.exception))

    def test_production_subdomains_rejected(self):
        """Verify subdomains of production are rejected."""
        for sub in ["www.salesleadmachine.co.uk", "api.salesleadmachine.co.uk", "app.salesleadmachine.co.uk"]:
            with self.assertRaises(RuntimeError) as ctx:
                assert_safe_test_environment(f"https://{sub}")
            self.assertIn("[SECURITY ABORT]", str(ctx.exception))

    def test_public_ip_target_rejected(self):
        """Verify public IPv4 targets are rejected."""
        with self.assertRaises(RuntimeError) as ctx:
            assert_safe_test_environment("http://93.184.216.34:8080")
        self.assertIn("[SECURITY ABORT]", str(ctx.exception))
        self.assertIn("public IP address", str(ctx.exception))

    def test_unregistered_untrusted_hostname_rejected(self):
        """Verify arbitrary external hostnames are rejected without explicit registration."""
        with self.assertRaises(RuntimeError) as ctx:
            assert_safe_test_environment("https://random-external-site.com")
        self.assertIn("[SECURITY ABORT]", str(ctx.exception))

    def test_invalid_scheme_rejected(self):
        """Verify non-http/https schemes are rejected."""
        with self.assertRaises(RuntimeError) as ctx:
            assert_safe_test_environment("ftp://localhost:21")
        self.assertIn("Invalid or missing URL scheme", str(ctx.exception))

    def test_production_database_host_rejected(self):
        """Verify database host pointing to production is rejected."""
        with self.assertRaises(RuntimeError) as ctx:
            assert_safe_test_environment("http://localhost:8080", db_host="db.salesleadmachine.co.uk")
        self.assertIn("[SECURITY ABORT]", str(ctx.exception))
        self.assertIn("Test database host", str(ctx.exception))

    def test_public_ip_database_rejected(self):
        """Verify public IP database host is rejected."""
        with self.assertRaises(RuntimeError) as ctx:
            assert_safe_test_environment("http://localhost:8080", db_host="198.51.100.10")
        self.assertIn("[SECURITY ABORT]", str(ctx.exception))

    def test_explicit_staging_registration_allowed(self):
        """Verify hosts listed in ALLOWED_STAGING_HOSTS are permitted."""
        os.environ["ALLOWED_STAGING_HOSTS"] = "staging-internal.slm.corp,10.0.50.15"
        try:
            self.assertTrue(assert_safe_test_environment("https://staging-internal.slm.corp:8443", db_host="10.0.50.15"))
        finally:
            os.environ.pop("ALLOWED_STAGING_HOSTS", None)

if __name__ == "__main__":
    unittest.main()

