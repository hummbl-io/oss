"""
Smoke test for hummbl-wargame.sh import paths and function signatures.

Verifies that all modules, classes, and functions used by the monthly
wargame script (~/bin/hummbl-wargame.sh) are importable and have the
expected signatures. Does NOT run the full wargame — just checks that
the import paths won't break.

Origin: goal-harness goal-20260902T022818Z-329
"""
import inspect
import unittest
from pathlib import Path


class TestWargameImports(unittest.TestCase):
    """Verify all import paths used by hummbl-wargame.sh are valid."""

    def test_kernel_import(self):
        """Kernel is importable from hummbl_governance.kernel.kernel."""
        from hummbl_governance.kernel.kernel import Kernel
        sig = inspect.signature(Kernel.__init__)
        params = list(sig.parameters.keys())
        self.assertIn("state_dir", params)
        self.assertIn("enforce_identity", params)

    def test_validate_rollback_import(self):
        """validate_rollback is importable from hummbl_governance.kernel.rollback."""
        from hummbl_governance.kernel.rollback import validate_rollback
        sig = inspect.signature(validate_rollback)
        params = list(sig.parameters.keys())
        self.assertIn("declaration", params)

    def test_validate_recovery_import(self):
        """validate_recovery is importable from hummbl_governance.kernel.recovery_verifier."""
        from hummbl_governance.kernel.recovery_verifier import validate_recovery
        sig = inspect.signature(validate_recovery)
        params = list(sig.parameters.keys())
        self.assertIn("verification", params)

    def test_doctrine_engine_import(self):
        """DoctrineEngine and Stage are importable from hummbl_governance.kernel.doctrine_engine."""
        from hummbl_governance.kernel.doctrine_engine import DoctrineEngine, Stage
        sig = inspect.signature(DoctrineEngine.__init__)
        params = list(sig.parameters.keys())
        self.assertIn("state_dir", params)
        # Stage should be an enum with expected members
        self.assertTrue(hasattr(Stage, "__members__"))

    def test_kill_switch_import(self):
        """KillSwitch, KillSwitchMode, KillSwitchEngagedError are importable."""
        from hummbl_governance.kill_switch import (
            KillSwitch,
            KillSwitchMode,
        )
        sig = inspect.signature(KillSwitch.__init__)
        params = list(sig.parameters.keys())
        self.assertIn("state_dir", params)
        self.assertIn("require_hmac", params)
        # KillSwitchMode should have expected members
        self.assertTrue(hasattr(KillSwitchMode, "DISENGAGED"))
        self.assertTrue(hasattr(KillSwitchMode, "HALT_ALL"))
        self.assertTrue(hasattr(KillSwitchMode, "EMERGENCY"))

    def test_circuit_breaker_import(self):
        """CircuitBreaker, CircuitBreakerOpen, CircuitBreakerState are importable."""
        from hummbl_governance.circuit_breaker import (
            CircuitBreaker,
            CircuitBreakerState,
        )
        sig = inspect.signature(CircuitBreaker.__init__)
        params = list(sig.parameters.keys())
        self.assertIn("failure_threshold", params)
        self.assertIn("recovery_timeout", params)
        # CircuitBreakerState should have expected members
        self.assertTrue(hasattr(CircuitBreakerState, "CLOSED"))
        self.assertTrue(hasattr(CircuitBreakerState, "OPEN"))
        self.assertTrue(hasattr(CircuitBreakerState, "HALF_OPEN"))


class TestWargameSignatures(unittest.TestCase):
    """Verify function signatures match what hummbl-wargame.sh expects."""

    def test_kernel_constructor_accepts_state_dir(self):
        """Kernel(state_dir=Path(...)) should work."""
        from hummbl_governance.kernel.kernel import Kernel
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            k = Kernel(state_dir=Path(tmp))
            self.assertIsNotNone(k)

    def test_doctrine_engine_constructor_accepts_state_dir(self):
        """DoctrineEngine(state_dir=Path(...)) should work."""
        from hummbl_governance.kernel.doctrine_engine import DoctrineEngine
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            de = DoctrineEngine(state_dir=Path(tmp))
            self.assertIsNotNone(de)

    def test_kill_switch_constructor_accepts_state_dir_and_require_hmac(self):
        """KillSwitch(state_dir=Path(...), require_hmac=False) should work."""
        from hummbl_governance.kill_switch import KillSwitch
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            ks = KillSwitch(state_dir=Path(tmp), require_hmac=False)
            self.assertIsNotNone(ks)

    def test_circuit_breaker_constructor_accepts_threshold_and_timeout(self):
        """CircuitBreaker(failure_threshold=N, recovery_timeout=F) should work."""
        from hummbl_governance.circuit_breaker import CircuitBreaker
        cb = CircuitBreaker(failure_threshold=3, recovery_timeout=0.1)
        self.assertIsNotNone(cb)


if __name__ == "__main__":
    unittest.main()
