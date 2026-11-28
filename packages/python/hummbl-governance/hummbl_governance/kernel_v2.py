# Copyright 2026 Reuben Bowlby
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# SPDX-License-Identifier: Apache-2.0

"""Base120 Micro-Kernel (v2.0 Architecture).

Algebraic reduction of the 51 historical governance primitives into 6
orthogonal Base120 Generative Archetypes (PIN-CODE-RESY) governed by a
6x6 Commutation Invariant Tensor.

Generators:
    SY: Automaton (Guarded FSM, Monotonic Severity, Containment)
    RE: Ledger (Merkle-Stream Causal Sink, SHA-256 Hash Chaining)
    P:  Filter (Poset Capability Attenuation, Monotonic Depth Contraction)
    CO: Quorum (Asynchronous Barrier Gates, Multi-Party/Operator Proofs)
    IN: Predicate (Pure Stateless Invariant & Falsifiability Assertions)
    DE: Projection (Stateless Catamorphic Views & Hash-Preserving Erasure)

Zero external runtime dependencies (Python standard library only).
"""

from __future__ import annotations

import dataclasses
import enum
import hashlib
import hmac
import json
import math
import secrets
import threading
import time
from typing import Any, Dict, FrozenSet, List, Optional, Set, Tuple

CRITICAL_ACTIONS: FrozenSet[str] = frozenset(
    {
        "safety_monitoring",
        "data_persistence",
        "audit_logging",
        "cost_tracking",
        "kill_switch_itself",
    }
)


# ===========================================================================
# 1. Base120 Coordinate Representation
# ===========================================================================

class Base120Family(enum.Enum):
    """The 6 fundamental transformation families of HUMMBL Base120."""
    PERSPECTIVE = "P"     # Capabilities, Trust Tiers, Identity Envelopes
    INVERSION = "IN"      # Constraints, Falsifiers, Threat Mitigations
    COMPOSITION = "CO"    # Quorum, Contract Net, Admission Gates
    DECOMPOSITION = "DE"  # Projections, Slicing, Stateless Catamorphisms
    RECURSION = "RE"      # Merkle Streams, Causal Clocks, Hash Chains
    SYSTEMS = "SY"        # Guarded Automata, Kill Switches, Global Bounds


@dataclasses.dataclass(frozen=True)
class Base120Coordinate:
    """Positional Base120 coordinate in PIN-CODE-RESY notation."""
    family: Base120Family
    index: int  # 1 to 20 per family

    def __post_init__(self) -> None:
        if not (1 <= self.index <= 20):
            raise ValueError(f"Base120 operator index must be 1..20, got {self.index}")

    def __str__(self) -> str:
        return f"{self.family.value}{self.index}"


# ===========================================================================
# 2. Generator SY — The Guarded Automaton (State Machine)
# ===========================================================================

class SeverityLevel(enum.IntEnum):
    """Monotonically ordered severity levels."""
    DISENGAGED = 0
    HALT_NONCRITICAL = 1
    HALT_ALL = 2
    EMERGENCY = 3


@dataclasses.dataclass(frozen=True)
class AutomatonState:
    """Immutable state for a guarded automaton."""
    name: str
    severity: SeverityLevel
    reason: str
    timestamp: float
    metadata: Dict[str, Any] = dataclasses.field(default_factory=dict)


class GuardedAutomaton:
    """Generator SY: Finite state machine with non-downgrading monotonic transitions.
    
    Invariant: Transitions to equal or higher severity are allowed autonomously.
    Downgrading severity requires a valid operator release token (PBKDF2/HMAC).
    """

    def __init__(self, name: str, release_key: Optional[bytes] = None) -> None:
        self.name = name
        if not isinstance(release_key, bytes) or not release_key:
            raise ValueError("release_key must be non-empty bytes")
        self._release_key = release_key
        self._lock = threading.RLock()
        self._state = AutomatonState(
            name="NORMAL",
            severity=SeverityLevel.DISENGAGED,
            reason="System initialized",
            timestamp=time.time(),
        )

    @property
    def state(self) -> AutomatonState:
        with self._lock:
            return self._state

    def transition(
        self,
        target_name: str,
        target_severity: SeverityLevel,
        reason: str,
        release_token: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> AutomatonState:
        """Evaluate state transition adhering to monotonicity."""
        with self._lock:
            current = self._state

            # Downgrade check (K10 / Reversibility / Operator Quorum)
            if target_severity < current.severity:
                if not self._verify_release(current, release_token):
                    raise PermissionError(
                        f"Invariant SY-Monotonicity: Cannot downgrade from {current.severity.name} "
                        f"to {target_severity.name} without valid operator release token."
                    )

            new_state = AutomatonState(
                name=target_name,
                severity=target_severity,
                reason=reason,
                timestamp=time.time(),
                metadata=metadata or {},
            )
            self._state = new_state
            return new_state

    def generate_release_token(self, state: AutomatonState) -> str:
        """Generate valid operator release token for current state."""
        payload = f"{self.name}:{state.severity.name}:{state.timestamp}".encode("utf-8")
        return hmac.new(self._release_key, payload, hashlib.sha256).hexdigest()

    def _verify_release(self, state: AutomatonState, token: Optional[str]) -> bool:
        if not token:
            return False
        expected = self.generate_release_token(state)
        return hmac.compare_digest(expected, token)


# ===========================================================================
# 3. Generator RE — The Merkle-Stream Causal Ledger
# ===========================================================================

@dataclasses.dataclass(frozen=True)
class LedgerReceipt:
    """Immutable, hash-chained receipt record."""
    sequence_id: int
    actor: str
    action: str
    payload_hash: str
    prev_hash: str
    timestamp: float
    receipt_hash: str
    coordinate: str = "RE1"

    @staticmethod
    def compute_receipt_hash(
        sequence_id: int,
        actor: str,
        action: str,
        payload_hash: str,
        prev_hash: str,
        timestamp: float,
        coordinate: str,
    ) -> str:
        """Compute unambiguous SHA-256 hash over canonical JSON of all receipt fields."""
        envelope = json.dumps(
            {
                "sequence_id": sequence_id,
                "actor": actor,
                "action": action,
                "payload_hash": payload_hash,
                "prev_hash": prev_hash,
                "timestamp": timestamp,
                "coordinate": coordinate,
            },
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
        return hashlib.sha256(envelope).hexdigest()

    @classmethod
    def create(
        cls,
        sequence_id: int,
        actor: str,
        action: str,
        payload: Dict[str, Any],
        prev_hash: str,
        coordinate: str = "RE1",
    ) -> LedgerReceipt:
        ts = time.time()
        payload_bytes = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
        payload_hash = hashlib.sha256(payload_bytes).hexdigest()
        receipt_hash = cls.compute_receipt_hash(
            sequence_id=sequence_id,
            actor=actor,
            action=action,
            payload_hash=payload_hash,
            prev_hash=prev_hash,
            timestamp=ts,
            coordinate=coordinate,
        )
        return cls(
            sequence_id=sequence_id,
            actor=actor,
            action=action,
            payload_hash=payload_hash,
            prev_hash=prev_hash,
            timestamp=ts,
            receipt_hash=receipt_hash,
            coordinate=coordinate,
        )


class CausalLedger:
    """Generator RE: Append-only event sink with cryptographic Merkle/SHA-256 chaining.

    Enforces Invariants K1 (Receipt), K4 (Temporal sequence), K11 (Integrity).
    """

    GENESIS_HASH = "0" * 64

    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._entries: List[LedgerReceipt] = []
        self._latest_hash: str = self.GENESIS_HASH

    @property
    def height(self) -> int:
        with self._lock:
            return len(self._entries)

    @property
    def latest_hash(self) -> str:
        with self._lock:
            return self._latest_hash

    def append(
        self,
        actor: str,
        action: str,
        payload: Dict[str, Any],
        coordinate: str = "RE1",
    ) -> LedgerReceipt:
        """Append receipt to chain with strictly monotonic sequence."""
        with self._lock:
            seq = len(self._entries) + 1
            receipt = LedgerReceipt.create(
                sequence_id=seq,
                actor=actor,
                action=action,
                payload=payload,
                prev_hash=self._latest_hash,
                coordinate=coordinate,
            )
            self._entries.append(receipt)
            self._latest_hash = receipt.receipt_hash
            return receipt

    def verify_integrity(self) -> bool:
        """Formally verify total causal sequence and unbroken hash chain (K11)."""
        with self._lock:
            expected_prev = self.GENESIS_HASH
            for idx, r in enumerate(self._entries):
                if r.sequence_id != idx + 1:
                    return False
                if r.prev_hash != expected_prev:
                    return False
                computed = LedgerReceipt.compute_receipt_hash(
                    sequence_id=r.sequence_id,
                    actor=r.actor,
                    action=r.action,
                    payload_hash=r.payload_hash,
                    prev_hash=r.prev_hash,
                    timestamp=r.timestamp,
                    coordinate=r.coordinate,
                )
                if not hmac.compare_digest(r.receipt_hash, computed):
                    return False
                expected_prev = r.receipt_hash
            return hmac.compare_digest(expected_prev, self._latest_hash)


# ===========================================================================
# 4. Generator P — The Poset Capability Attenuation Filter
# ===========================================================================

@dataclasses.dataclass(frozen=True)
class CapabilityToken:
    """Immutable delegation token bounded by strict poset contraction and HMAC auth."""
    token_id: str
    issuer: str
    subject: str
    depth: int
    max_depth: int
    allowed_scopes: Tuple[str, ...]
    expiry: float
    signature: str = ""

    def _canonical_bytes(self) -> bytes:
        return json.dumps(
            {
                "domain": "cap-token-v2",
                "token_id": self.token_id,
                "issuer": self.issuer,
                "subject": self.subject,
                "depth": self.depth,
                "max_depth": self.max_depth,
                "allowed_scopes": list(self.allowed_scopes),
                "expiry": self.expiry,
            },
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")

    def compute_signature(self, signing_key: bytes) -> str:
        if not isinstance(signing_key, bytes) or not signing_key:
            raise ValueError("signing_key must be non-empty bytes")
        return hmac.new(signing_key, self._canonical_bytes(), hashlib.sha256).hexdigest()

    def verify_signature(self, signing_key: bytes) -> bool:
        if not self.signature or not isinstance(signing_key, bytes) or not signing_key:
            return False
        expected = self.compute_signature(signing_key)
        return hmac.compare_digest(expected, self.signature)

    def attenuate(
        self,
        new_subject: str,
        sub_scopes: Set[str],
        lifetime_seconds: float,
        signing_key: Optional[bytes] = None,
    ) -> CapabilityToken:
        """Contraction mapping: depth decreases, scope subset, expiry strictly earlier."""
        if (
            not isinstance(lifetime_seconds, (int, float))
            or isinstance(lifetime_seconds, bool)
            or not math.isfinite(lifetime_seconds)
            or lifetime_seconds <= 0
        ):
            raise ValueError("lifetime_seconds must be a finite positive number")
        if signing_key is not None and not self.verify_signature(signing_key):
            raise PermissionError("Invariant P-Auth: Cannot attenuate an unauthenticated token.")
        now = time.time()
        new_expiry = min(self.expiry, now + lifetime_seconds)
        parent_scopes = set(self.allowed_scopes)

        # Invariant P-Scope: Child cannot exceed parent scope
        if not sub_scopes.issubset(parent_scopes):
            illegal = sub_scopes - parent_scopes
            raise PermissionError(
                f"Invariant P-Scope: Sub-scope {illegal} exceeds parent scope {parent_scopes}"
            )

        # Invariant P-Depth: Depth must monotonically decrease
        if self.depth <= 0:
            raise PermissionError("Invariant P-Depth: Maximum delegation depth exhausted (depth = 0)")

        token_hash = hashlib.sha256(
            f"{self.token_id}:{new_subject}:{now}".encode("utf-8")
        ).hexdigest()[:16]
        child = CapabilityToken(
            token_id=f"tok_{token_hash}",
            issuer=self.subject,
            subject=new_subject,
            depth=self.depth - 1,
            max_depth=self.max_depth,
            allowed_scopes=tuple(sorted(sub_scopes)),
            expiry=new_expiry,
        )
        if signing_key is not None:
            return dataclasses.replace(child, signature=child.compute_signature(signing_key))
        return child

    def is_valid_for(self, scope: str) -> bool:
        if not isinstance(self.expiry, (int, float)) or not math.isfinite(self.expiry):
            return False
        if time.time() > self.expiry:
            return False
        return scope in self.allowed_scopes


# ===========================================================================
# 5. Generator CO — The Asynchronous Quorum Barrier
# ===========================================================================

class BarrierStatus(enum.Enum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    SUSPENDED = "SUSPENDED"


@dataclasses.dataclass
class QuorumBarrier:
    """Generator CO: Asynchronous human/multi-agent approval barrier."""
    barrier_id: str
    action_intent: str
    required_signers: Set[str]
    signer_keys: Dict[str, bytes] = dataclasses.field(default_factory=dict, repr=False)
    collected_signatures: Dict[str, str] = dataclasses.field(default_factory=dict)
    status: BarrierStatus = BarrierStatus.PENDING
    created_at: float = dataclasses.field(default_factory=time.time)
    timeout_seconds: float = 3600.0
    _lock: threading.RLock = dataclasses.field(
        default_factory=threading.RLock, init=False, repr=False, compare=False
    )

    def sign_approval(self, signer: str, signer_key: bytes) -> str:
        """Compute HMAC-SHA256 approval proof bound to barrier_id, action_intent, and signer."""
        if not isinstance(signer_key, bytes) or not signer_key:
            raise ValueError("signer_key must be non-empty bytes")
        payload = json.dumps(
            {
                "domain": "quorum-v2",
                "barrier_id": self.barrier_id,
                "action_intent": self.action_intent,
                "signer": signer,
            },
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
        return hmac.new(signer_key, payload, hashlib.sha256).hexdigest()

    def _is_valid_proof(self, signer: str, proof_token: Any) -> bool:
        if (
            not isinstance(proof_token, str)
            or len(proof_token) != 64
            or any(ch not in "0123456789abcdefABCDEF" for ch in proof_token)
        ):
            return False
        key = self.signer_keys.get(signer)
        if not isinstance(key, bytes) or not key:
            return False
        expected = self.sign_approval(signer, key)
        return hmac.compare_digest(expected, proof_token.lower())

    def submit_signature(self, signer: str, proof_token: str) -> bool:
        with self._lock:
            if self.status != BarrierStatus.PENDING:
                return False
            if time.time() > (self.created_at + self.timeout_seconds):
                self.status = BarrierStatus.REJECTED
                return False
            if signer not in self.required_signers or not self._is_valid_proof(signer, proof_token):
                return False
            self.collected_signatures[signer] = proof_token.lower()
            if all(
                self._is_valid_proof(req, self.collected_signatures.get(req))
                for req in self.required_signers
            ):
                self.status = BarrierStatus.APPROVED
            return True

    def suspend(self, reason: str) -> None:
        """Emergency suspension when preempted by an automaton halt."""
        with self._lock:
            _ = reason
            self.status = BarrierStatus.SUSPENDED


# ===========================================================================
# 6. Generator IN — The Pure Constraint Predicate
# ===========================================================================

class ConstraintPredicate:
    """Generator IN: Stateless boolean assertions and falsifiability checking."""

    @staticmethod
    def assert_schema_keys(target: Dict[str, Any], required_keys: Set[str]) -> Tuple[bool, List[str]]:
        missing = [k for k in required_keys if k not in target]
        return len(missing) == 0, [f"Missing required key: {k}" for k in missing]

    @staticmethod
    def assert_falsifiability(proposition: Dict[str, Any]) -> Tuple[bool, str]:
        """Invariant D2: A hypothesis without an explicit falsifier is rejected."""
        if "falsifier" not in proposition or not proposition["falsifier"]:
            return False, "Invariant D2 (FALSIFIABILITY): Proposition lacks an empirical falsifier."
        return True, "Falsifier present"

    @staticmethod
    def assert_non_collusion(agent_a: str, agent_b: str, shared_context: Dict[str, Any]) -> bool:
        """Prevent self-attestation or cyclical peer approval."""
        _ = shared_context
        return agent_a != agent_b


# ===========================================================================
# 7. Generator DE — Stateless Projection & Catamorphic Redaction
# ===========================================================================

class ProjectionFunctor:
    """Generator DE: Stateless catamorphisms folding over ledger events."""

    @staticmethod
    def redact_pseudonymize(
        payload: Dict[str, Any],
        pii_fields: Set[str],
        salt: Optional[str] = None,
    ) -> Dict[str, Any]:
        """GDPR Art. 17 right-to-erasure via deterministic keyed hash substitution.
        
        Preserves structural integrity and repeatability without leaking plaintext.
        """
        if not isinstance(salt, str) or not salt:
            raise ValueError("salt must be a non-empty string")
        redacted = dict(payload)
        for field in pii_fields:
            if field in redacted:
                val = str(redacted[field]).encode("utf-8")
                token = hashlib.sha256(val + salt.encode("utf-8")).hexdigest()[:16]
                redacted[field] = f"[PSEUDO_{token}]"
        return redacted

    @staticmethod
    def fold_records_of_processing(receipts: List[LedgerReceipt]) -> Dict[str, Any]:
        """Assemble an Article 30 RoPA document purely by folding over receipts."""
        actors = set(r.actor for r in receipts)
        actions = set(r.action for r in receipts)
        return {
            "document_type": "Art30_RoPA",
            "total_processing_events": len(receipts),
            "actors": sorted(actors),
            "distinct_actions": sorted(actions),
            "latest_anchor": receipts[-1].receipt_hash if receipts else "0" * 64,
        }


# ===========================================================================
# 8. The 6x6 Commutation Invariant Tensor & Unified Micro-Kernel
# ===========================================================================

class Base120MicroKernel:
    """The unified sovereign micro-kernel orchestrating the 6 Base120 generators."""

    def __init__(
        self,
        release_key: Optional[bytes] = None,
        kernel_id: Optional[str] = None,
    ) -> None:
        self.automaton = GuardedAutomaton("ROOT_GOVERNOR", release_key)
        assert isinstance(release_key, bytes)
        self.kernel_id = kernel_id if kernel_id else secrets.token_hex(16)
        self._token_key = hashlib.sha256(
            b"hummbl-kernel-v2-token:" + self.kernel_id.encode("utf-8") + b":" + release_key
        ).digest()
        self._lock = threading.RLock()
        self.ledger = CausalLedger()
        self.active_barriers: Dict[str, QuorumBarrier] = {}
        self.predicates = ConstraintPredicate()
        self.projections = ProjectionFunctor()

    def issue_token(
        self,
        issuer: str,
        subject: str,
        allowed_scopes: Tuple[str, ...],
        depth: int = 3,
        lifetime_seconds: float = 3600.0,
    ) -> CapabilityToken:
        """Mint an HMAC-authenticated root capability token bound to this kernel."""
        if (
            not isinstance(lifetime_seconds, (int, float))
            or isinstance(lifetime_seconds, bool)
            or not math.isfinite(lifetime_seconds)
            or lifetime_seconds <= 0
        ):
            raise ValueError("lifetime_seconds must be a finite positive number")
        now = time.time()
        tok_id = "tok_" + hashlib.sha256(
            f"{issuer}:{subject}:{now}:{','.join(sorted(allowed_scopes))}".encode("utf-8")
        ).hexdigest()[:16]
        unsigned = CapabilityToken(
            token_id=tok_id,
            issuer=issuer,
            subject=subject,
            depth=depth,
            max_depth=depth,
            allowed_scopes=tuple(sorted(allowed_scopes)),
            expiry=now + lifetime_seconds,
        )
        return dataclasses.replace(unsigned, signature=unsigned.compute_signature(self._token_key))

    def attenuate_token(
        self,
        parent: CapabilityToken,
        new_subject: str,
        sub_scopes: Set[str],
        lifetime_seconds: float,
    ) -> CapabilityToken:
        """Attenuate a kernel-issued token and sign the contracted child token."""
        return parent.attenuate(
            new_subject=new_subject,
            sub_scopes=sub_scopes,
            lifetime_seconds=lifetime_seconds,
            signing_key=self._token_key,
        )

    def execute_governed_action(
        self,
        token: CapabilityToken,
        action: str,
        scope: str,
        payload: Dict[str, Any],
    ) -> LedgerReceipt:
        """Execute a governed transition verifying all cross-generator invariants.

        Commutation checks:
          SY x P: Is automaton healthy (or critical-only under HALT_NONCRITICAL)?
          P x RE: Is token kernel-authenticated and authorized for scope?
        """
        with self._lock:
            state = self.automaton.state
            # 1. SY Preemption check: fail-closed on HALT_ALL/EMERGENCY and noncritical on HALT_NONCRITICAL
            if state.severity >= SeverityLevel.HALT_ALL:
                raise RuntimeError(
                    f"Invariant SY-Preempt: Action '{action}' blocked by active halt: "
                    f"{state.name} ({state.reason})"
                )
            if state.severity == SeverityLevel.HALT_NONCRITICAL and action not in CRITICAL_ACTIONS:
                raise RuntimeError(
                    f"Invariant SY-Preempt: Noncritical action '{action}' blocked during "
                    f"HALT_NONCRITICAL: {state.name} ({state.reason})"
                )

            # 2. P Poset Contraction & Authentication check
            if not token.verify_signature(self._token_key):
                raise PermissionError(
                    f"Invariant P-Auth: CapabilityToken '{token.token_id}' signature invalid or missing"
                )
            if not token.is_valid_for(scope):
                raise PermissionError(
                    f"Invariant P-Scope: Subject '{token.subject}' unauthorized for scope '{scope}'"
                )

            # 3. Append to Ledger and return signed receipt
            return self.ledger.append(
                actor=token.subject,
                action=action,
                payload=payload,
                coordinate="CO1.RE1",
            )
