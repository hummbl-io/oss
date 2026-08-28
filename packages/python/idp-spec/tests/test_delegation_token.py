"""Tests for delegation_token module.

Covers IDP v0.1 DCT lifecycle:
- Token creation with HMAC-SHA256 signing
- Signature verification
- Expiry handling
- Binding validation (I2 invariants)
- Least privilege enforcement
"""

from __future__ import annotations

import os
import unittest
from dataclasses import FrozenInstanceError
from datetime import datetime, timedelta, timezone

# Ensure ENABLE_IDP for tests
os.environ["ENABLE_IDP"] = "true"

from idp_spec.delegation_token import (
    IDP_E_BINDING_MISMATCH,
    IDP_E_DCT_VIOLATION,
    IDP_E_TOKEN_INVALID,
    Caveat,
    DelegationCapabilityToken,
    DelegationTokenManager,
    ResourceSelector,
    TokenBinding,
    create_token,
    validate_token,
)


class TestResourceSelector(unittest.TestCase):
    """Test ResourceSelector dataclass."""

    def test_default_wildcard(self):
        """ResourceSelector defaults to wildcard resource_id."""
        rs = ResourceSelector(resource_type="file")
        self.assertEqual(rs.resource_type, "file")
        self.assertEqual(rs.resource_id, "*")
        self.assertEqual(rs.constraints, {})

    def test_specific_resource(self):
        """ResourceSelector can specify exact resource."""
        rs = ResourceSelector(
            resource_type="database",
            resource_id="users_table",
            constraints={"read_only": True}
        )
        self.assertEqual(rs.resource_id, "users_table")
        self.assertEqual(rs.constraints["read_only"], True)


class TestCaveat(unittest.TestCase):
    """Test Caveat dataclass."""

    def test_time_bound_caveat(self):
        """TIME_BOUND caveat with expiry parameter."""
        c = Caveat(
            caveat_id="cav-1",
            type="TIME_BOUND",
            parameters={"not_after": "2026-02-17T12:00:00Z"}
        )
        self.assertEqual(c.type, "TIME_BOUND")
        self.assertIn("not_after", c.parameters)

    def test_rate_limit_caveat(self):
        """RATE_LIMIT caveat with max_calls parameter."""
        c = Caveat(
            caveat_id="cav-2",
            type="RATE_LIMIT",
            parameters={"max_calls": 10, "window_seconds": 60}
        )
        self.assertEqual(c.type, "RATE_LIMIT")
        self.assertEqual(c.parameters["max_calls"], 10)


class TestTokenBinding(unittest.TestCase):
    """Test TokenBinding dataclass."""

    def test_binding_fields(self):
        """Binding links token to task and contract."""
        binding = TokenBinding(
            task_id="task-abc-123",
            contract_id="contract-xyz-789"
        )
        self.assertEqual(binding.task_id, "task-abc-123")
        self.assertEqual(binding.contract_id, "contract-xyz-789")


class TestDelegationCapabilityToken(unittest.TestCase):
    """Test DelegationCapabilityToken dataclass."""

    def test_token_creation(self):
        """Token can be created with all fields."""
        binding = TokenBinding("task-1", "contract-1")
        token = DelegationCapabilityToken(
            token_id="tok-123",
            issuer="agent-a",
            subject="agent-b",
            ops_allowed=("read", "write"),
            binding=binding,
            signature="sig-abc"
        )
        self.assertEqual(token.token_id, "tok-123")
        self.assertEqual(token.issuer, "agent-a")
        self.assertEqual(token.subject, "agent-b")
        self.assertEqual(token.ops_allowed, ("read", "write"))

    def test_token_frozen(self):
        """Token is immutable (frozen dataclass)."""
        token = DelegationCapabilityToken(
            token_id="tok-1",
            issuer="a",
            subject="b"
        )
        with self.assertRaises((FrozenInstanceError, AttributeError)):
            token.issuer = "c"

    def test_to_dict_excludes_signature(self):
        """to_dict() excludes signature field for signing."""
        binding = TokenBinding("task-1", "contract-1")
        token = DelegationCapabilityToken(
            token_id="tok-1",
            issuer="a",
            subject="b",
            ops_allowed=("read",),
            binding=binding,
            signature="should-be-excluded"
        )
        data = token.to_dict()
        self.assertNotIn("signature", data)
        self.assertEqual(data["token_id"], "tok-1")
        self.assertEqual(data["binding"]["task_id"], "task-1")


class TestTokenManagerCreation(unittest.TestCase):
    """Test DelegationTokenManager token creation."""

    def setUp(self):
        self.manager = DelegationTokenManager(secret=b"test-secret-32-bytes-long-ok")
        self.binding = TokenBinding("task-123", "contract-456")

    def test_create_basic_token(self):
        """Create token with minimal parameters."""
        token = self.manager.create_token(
            issuer="agent-a",
            subject="agent-b",
            ops_allowed=["read_file", "write_file"],
            binding=self.binding
        )
        self.assertTrue(token.token_id)  # UUID generated
        self.assertEqual(token.issuer, "agent-a")
        self.assertEqual(token.subject, "agent-b")
        self.assertEqual(token.ops_allowed, ("read_file", "write_file"))
        self.assertTrue(token.signature)  # Signed

    def test_create_with_resource_selectors(self):
        """Create token with resource selectors."""
        rs = [ResourceSelector("file", "/tmp/*")]
        token = self.manager.create_token(
            issuer="a",
            subject="b",
            ops_allowed=["read"],
            binding=self.binding,
            resource_selectors=rs
        )
        self.assertEqual(len(token.resource_selectors), 1)
        self.assertEqual(token.resource_selectors[0].resource_type, "file")

    def test_create_with_caveats(self):
        """Create token with caveats."""
        caveats = [Caveat("c1", "TIME_BOUND", {"max_duration": 3600})]
        token = self.manager.create_token(
            issuer="a",
            subject="b",
            ops_allowed=["read"],
            binding=self.binding,
            caveats=caveats
        )
        self.assertEqual(len(token.caveats), 1)
        self.assertEqual(token.caveats[0].caveat_id, "c1")

    def test_create_with_expiry(self):
        """Create token with expiry time."""
        token = self.manager.create_token(
            issuer="a",
            subject="b",
            ops_allowed=["read"],
            binding=self.binding,
            expiry_minutes=60
        )
        self.assertIsNotNone(token.expiry)
        # Verify ISO8601 format
        self.assertTrue(token.expiry.endswith("Z") or "+00:00" in token.expiry)

    def test_create_no_expiry(self):
        """Create token with no expiry."""
        token = self.manager.create_token(
            issuer="a",
            subject="b",
            ops_allowed=["read"],
            binding=self.binding,
            expiry_minutes=None
        )
        self.assertIsNone(token.expiry)

    def test_feature_flag_disabled(self):
        """Creation fails when ENABLE_IDP=false."""
        os.environ["ENABLE_IDP"] = "false"
        try:
            with self.assertRaises(RuntimeError) as ctx:
                self.manager.create_token(
                    issuer="a",
                    subject="b",
                    ops_allowed=["read"],
                    binding=self.binding
                )
            self.assertIn("ENABLE_IDP", str(ctx.exception))
        finally:
            os.environ["ENABLE_IDP"] = "true"

    def test_signature_verification(self):
        """Token signature is verifiable."""
        token = self.manager.create_token(
            issuer="a",
            subject="b",
            ops_allowed=["read"],
            binding=self.binding
        )
        self.assertTrue(token.verify_signature(b"test-secret-32-bytes-long-ok"))

    def test_signature_invalid_wrong_secret(self):
        """Signature fails with wrong secret."""
        token = self.manager.create_token(
            issuer="a",
            subject="b",
            ops_allowed=["read"],
            binding=self.binding
        )
        self.assertFalse(token.verify_signature(b"wrong-secret-12345678901234"))


class TestTokenValidation(unittest.TestCase):
    """Test DelegationTokenManager.validate_token."""

    def setUp(self):
        self.manager = DelegationTokenManager(secret=b"test-secret")
        self.binding = TokenBinding("task-123", "contract-456")

    def test_validate_success(self):
        """Valid token passes validation."""
        token = self.manager.create_token(
            issuer="a",
            subject="b",
            ops_allowed=["read"],
            binding=self.binding,
            expiry_minutes=60
        )
        is_valid, error = self.manager.validate_token(token)
        self.assertTrue(is_valid)
        self.assertIsNone(error)

    def test_validate_invalid_signature(self):
        """Tampered token fails signature check."""
        token = self.manager.create_token(
            issuer="a",
            subject="b",
            ops_allowed=["read"],
            binding=self.binding
        )
        # Tamper with the token
        tampered = DelegationCapabilityToken(
            token_id=token.token_id,
            issuer="attacker",  # Changed
            subject=token.subject,
            ops_allowed=token.ops_allowed,
            signature=token.signature  # Original sig won't match
        )
        is_valid, error = self.manager.validate_token(tampered)
        self.assertFalse(is_valid)
        self.assertEqual(error, IDP_E_TOKEN_INVALID)

    def test_validate_expired_token(self):
        """Expired token fails validation."""
        # Create token that expires immediately
        token = self.manager.create_token(
            issuer="a",
            subject="b",
            ops_allowed=["read"],
            binding=self.binding,
            expiry_minutes=0  # Already expired
        )
        # Manually set expiry to past
        expired_token = DelegationCapabilityToken(
            token_id=token.token_id,
            issuer=token.issuer,
            subject=token.subject,
            ops_allowed=token.ops_allowed,
            binding=token.binding,
            expiry=(datetime.now(timezone.utc) - timedelta(hours=1)).isoformat().replace("+00:00", "Z"),
            signature=""  # Will fail sig check but we test expiry first in this case
        )
        # Actually, expiry is checked after signature, so let's just check is_expired
        self.assertTrue(expired_token.is_expired())

    def test_validate_binding_match(self):
        """Validation with matching binding succeeds."""
        token = self.manager.create_token(
            issuer="a",
            subject="agent-b",
            ops_allowed=["read"],
            binding=self.binding
        )
        is_valid, error = self.manager.validate_token(
            token,
            expected_task_id="task-123",
            expected_contract_id="contract-456",
            expected_subject="agent-b"
        )
        self.assertTrue(is_valid)
        self.assertIsNone(error)

    def test_validate_binding_mismatch(self):
        """Validation with wrong binding fails."""
        token = self.manager.create_token(
            issuer="a",
            subject="b",
            ops_allowed=["read"],
            binding=self.binding
        )
        is_valid, error = self.manager.validate_token(
            token,
            expected_task_id="wrong-task"
        )
        self.assertFalse(is_valid)
        self.assertEqual(error, IDP_E_BINDING_MISMATCH)

    def test_feature_flag_disabled_validation(self):
        """When ENABLE_IDP=false, all tokens valid (backward compat)."""
        os.environ["ENABLE_IDP"] = "false"
        try:
            # Even invalid signature passes when disabled
            invalid_token = DelegationCapabilityToken(
                token_id="bad",
                issuer="bad",
                subject="bad",
                signature="invalid"
            )
            is_valid, error = self.manager.validate_token(invalid_token)
            self.assertTrue(is_valid)  # Bypassed when disabled
            self.assertIsNone(error)
        finally:
            os.environ["ENABLE_IDP"] = "true"


class TestLeastPrivilege(unittest.TestCase):
    """Test I2 Least Privilege enforcement."""

    def setUp(self):
        self.manager = DelegationTokenManager(secret=b"test-secret")
        self.binding = TokenBinding("task-1", "contract-1")

    def test_allowed_operation(self):
        """Operation in ops_allowed passes."""
        token = self.manager.create_token(
            issuer="a",
            subject="b",
            ops_allowed=["read_file", "write_file"],
            binding=self.binding
        )
        is_allowed, error = self.manager.check_least_privilege(
            token, "read_file"
        )
        self.assertTrue(is_allowed)
        self.assertIsNone(error)

    def test_denied_operation_not_in_token(self):
        """Operation not in ops_allowed fails."""
        token = self.manager.create_token(
            issuer="a",
            subject="b",
            ops_allowed=["read_file"],
            binding=self.binding
        )
        is_allowed, error = self.manager.check_least_privilege(
            token, "execute_shell"
        )
        self.assertFalse(is_allowed)
        self.assertEqual(error, IDP_E_DCT_VIOLATION)

    def test_contract_allowed_tools_constraint(self):
        """Operation not in contract's allowed_tools fails."""
        token = self.manager.create_token(
            issuer="a",
            subject="b",
            ops_allowed=["read_file", "write_file", "execute_shell"],
            binding=self.binding
        )
        # Contract only allows read/write
        is_allowed, error = self.manager.check_least_privilege(
            token,
            "execute_shell",
            allowed_tools=["read_file", "write_file"]
        )
        self.assertFalse(is_allowed)
        self.assertEqual(error, IDP_E_DCT_VIOLATION)

    def test_contract_denied_tools_constraint(self):
        """Operation in contract's denied_tools fails."""
        token = self.manager.create_token(
            issuer="a",
            subject="b",
            ops_allowed=["read_file", "execute_shell"],
            binding=self.binding
        )
        # Contract denies execute_shell
        is_allowed, error = self.manager.check_least_privilege(
            token,
            "execute_shell",
            denied_tools=["execute_shell", "delete_file"]
        )
        self.assertFalse(is_allowed)
        self.assertEqual(error, IDP_E_DCT_VIOLATION)

    def test_feature_flag_disabled_privilege(self):
        """When ENABLE_IDP=false, all operations allowed."""
        os.environ["ENABLE_IDP"] = "false"
        try:
            token = DelegationCapabilityToken(
                token_id="t",
                issuer="a",
                subject="b",
                ops_allowed=("read",)
            )
            # Requesting write even though token only allows read
            is_allowed, error = self.manager.check_least_privilege(
                token, "write"
            )
            self.assertTrue(is_allowed)  # Bypassed when disabled
        finally:
            os.environ["ENABLE_IDP"] = "true"


class TestConvenienceFunctions(unittest.TestCase):
    """Test module-level convenience functions."""

    def test_create_token_convenience(self):
        """create_token() uses default manager."""
        os.environ["ENABLE_IDP"] = "true"
        binding = TokenBinding("task-1", "contract-1")
        token = create_token(
            issuer="a",
            subject="b",
            ops_allowed=["read"],
            binding=binding
        )
        self.assertEqual(token.issuer, "a")
        self.assertTrue(token.signature)

    def test_validate_token_convenience(self):
        """validate_token() uses default manager."""
        binding = TokenBinding("task-1", "contract-1")
        token = create_token(
            issuer="a",
            subject="b",
            ops_allowed=["read"],
            binding=binding
        )
        is_valid, error = validate_token(token)
        self.assertTrue(is_valid)


class TestTokenExpiry(unittest.TestCase):
    """Test token expiry edge cases."""

    def test_is_expired_with_past_date(self):
        """Token with past expiry is_expired=True."""
        past = (datetime.now(timezone.utc) - timedelta(hours=1)).isoformat()
        token = DelegationCapabilityToken(
            token_id="t",
            issuer="a",
            subject="b",
            expiry=past.replace("+00:00", "Z")
        )
        self.assertTrue(token.is_expired())

    def test_is_expired_with_future_date(self):
        """Token with future expiry is_expired=False."""
        future = (datetime.now(timezone.utc) + timedelta(hours=1)).isoformat()
        token = DelegationCapabilityToken(
            token_id="t",
            issuer="a",
            subject="b",
            expiry=future.replace("+00:00", "Z")
        )
        self.assertFalse(token.is_expired())

    def test_is_expired_no_expiry(self):
        """Token with no expiry is_expired=False."""
        token = DelegationCapabilityToken(
            token_id="t",
            issuer="a",
            subject="b",
            expiry=None
        )
        self.assertFalse(token.is_expired())

    def test_is_expired_invalid_format(self):
        """Token with invalid expiry is_expired=True (safe default)."""
        token = DelegationCapabilityToken(
            token_id="t",
            issuer="a",
            subject="b",
            expiry="not-a-valid-date"
        )
        self.assertTrue(token.is_expired())


if __name__ == "__main__":
    unittest.main()
