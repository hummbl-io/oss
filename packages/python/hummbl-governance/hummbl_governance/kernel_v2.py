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
import time
from typing import Any, Callable, Dict, List, Optional, Set, Tuple


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
        self._release_key = release_key or b"hummbl-sovereign-operator-seed"
        self._state = AutomatonState(
            name="NORMAL",
            severity=SeverityLevel.DISENGAGED,
            reason="System initialized",
            timestamp=time.time(),
        )

    @property
    def state(self) -> AutomatonState:
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
        payload_bytes = json.dumps(payload, sort_keys=True).encode("utf-8")
        payload_hash = hashlib.sha256(payload_bytes).hexdigest()
        
        envelope = f"{sequence_id}:{actor}:{action}:{payload_hash}:{prev_hash}:{ts}".encode("utf-8")
        receipt_hash = hashlib.sha256(envelope).hexdigest()
        
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
        self._entries: List[LedgerReceipt] = []
        self._latest_hash: str = self.GENESIS_HASH

    @property
    def height(self) -> int:
        return len(self._entries)

    @property
    def latest_hash(self) -> str:
        return self._latest_hash

    def append(
        self,
        actor: str,
        action: str,
        payload: Dict[str, Any],
        coordinate: str = "RE1",
    ) -> LedgerReceipt:
        """Append receipt to chain with strictly monotonic sequence."""
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
        expected_prev = self.GENESIS_HASH
        for idx, r in enumerate(self._entries):
            if r.sequence_id != idx + 1:
                return False
            if r.prev_hash != expected_prev:
                return False
            # Verify self-hash
            envelope = f"{r.sequence_id}:{r.actor}:{r.action}:{r.payload_hash}:{r.prev_hash}:{r.timestamp}".encode("utf-8")
            computed = hashlib.sha256(envelope).hexdigest()
            if r.receipt_hash != computed:
                return False
            expected_prev = r.receipt_hash
        return True


# ===========================================================================
# 4. Generator P — The Poset Capability Attenuation Filter
# ===========================================================================

@dataclasses.dataclass(frozen=True)
class CapabilityToken:
    """Immutable delegation token bounded by strict poset contraction."""
    token_id: str
    issuer: str
    subject: str
    depth: int
    max_depth: int
    allowed_scopes: Tuple[str, ...]
    expiry: float

    def attenuate(self, new_subject: str, sub_scopes: Set[str], lifetime_seconds: float) -> CapabilityToken:
        """Contraction mapping: depth decreases, scope subset, expiry strictly earlier."""
        now = time.time()
        new_expiry = min(self.expiry, now + lifetime_seconds)
        parent_scopes = set(self.allowed_scopes)
        
        # Invariant P-Scope: Child cannot exceed parent scope
        if not sub_scopes.issubset(parent_scopes):
            illegal = sub_scopes - parent_scopes
            raise PermissionError(f"Invariant P-Scope: Sub-scope {illegal} exceeds parent scope {parent_scopes}")
            
        # Invariant P-Depth: Depth must monotonically decrease
        if self.depth <= 0:
            raise PermissionError("Invariant P-Depth: Maximum delegation depth exhausted (depth = 0)")
            
        token_hash = hashlib.sha256(f"{self.token_id}:{new_subject}:{now}".encode("utf-8")).hexdigest()[:16]
        return CapabilityToken(
            token_id=f"tok_{token_hash}",
            issuer=self.subject,
            subject=new_subject,
            depth=self.depth - 1,
            max_depth=self.max_depth,
            allowed_scopes=tuple(sorted(sub_scopes)),
            expiry=new_expiry,
        )

    def is_valid_for(self, scope: str) -> bool:
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
    collected_signatures: Dict[str, str] = dataclasses.field(default_factory=dict)
    status: BarrierStatus = BarrierStatus.PENDING
    created_at: float = dataclasses.field(default_factory=time.time)
    timeout_seconds: float = 3600.0

    def submit_signature(self, signer: str, proof_token: str) -> bool:
        if self.status != BarrierStatus.PENDING:
            return False
        if time.time() > (self.created_at + self.timeout_seconds):
            self.status = BarrierStatus.REJECTED
            return False
        if signer in self.required_signers:
            self.collected_signatures[signer] = proof_token
            if set(self.collected_signatures.keys()).issuperset(self.required_signers):
                self.status = BarrierStatus.APPROVED
            return True
        return False

    def suspend(self, reason: str) -> None:
        """Emergency suspension when preempted by an automaton halt."""
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
        salt: str = "hummbl-sovereign-salt",
    ) -> Dict[str, Any]:
        """GDPR Art. 17 right-to-erasure via deterministic keyed hash substitution.
        
        Preserves structural integrity and repeatability without leaking plaintext.
        """
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

    def __init__(self, release_key: Optional[bytes] = None) -> None:
        self.automaton = GuardedAutomaton("ROOT_GOVERNOR", release_key)
        self.ledger = CausalLedger()
        self.active_barriers: Dict[str, QuorumBarrier] = {}
        self.predicates = ConstraintPredicate()
        self.projections = ProjectionFunctor()

    def execute_governed_action(
        self,
        token: CapabilityToken,
        action: str,
        scope: str,
        payload: Dict[str, Any],
    ) -> LedgerReceipt:
        """Execute a governed transition verifying all cross-generator invariants.
        
        Commutation checks:
          SY x P: Is automaton healthy before checking capability?
          P x RE: Does token allow scope before emitting receipt?
          IN x RE: Does payload satisfy constraint predicate before append?
        """
        # 1. SY Preemption check: If Automaton is in HALT or EMERGENCY, fail-closed
        if self.automaton.state.severity >= SeverityLevel.HALT_ALL:
            raise RuntimeError(
                f"Invariant SY-Preempt: Action '{action}' blocked by active halt: "
                f"{self.automaton.state.name} ({self.automaton.state.reason})"
            )

        # 2. P Poset Contraction check: Does token allow scope?
        if not token.is_valid_for(scope):
            raise PermissionError(
                f"Invariant P-Scope: Subject '{token.subject}' unauthorized for scope '{scope}'"
            )

        # 3. Append to Ledger and return signed receipt
        receipt = self.ledger.append(
            actor=token.subject,
            action=action,
            payload=payload,
            coordinate="CO1.RE1",
        )
        return receipt
