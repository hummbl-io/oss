/-
SPDX-License-Identifier: Apache-2.0
Copyright 2024-2026 HUMMBL

HummblFormalization.GovernanceStateMachines
Formal verification of HUMMBL governance state machines:
  1. Monotonic Scope Attenuation on Delegation Chains (#35, #36a)
  2. Fail-Closed Absorption of KillSwitch.EMERGENCY and SafetyLatch.LOCKED (#34, #36b)
  3. Non-Bypassability of MonotonicGate and CircuitBreaker Mutual Exclusion (#34, #36c)
  4. Physical AI Watchdog Dead-Man's Switch & Telemetry Staleness Bound (#46, #47)

Self-contained (Lean 4 Init only, zero Mathlib dependency, zero sorry, warningAsError).
-/

set_option warningAsError true

namespace HummblFormalization.GovernanceStateMachines

/-! ## Section 1: Monotonic Scope Attenuation on Delegation Chains -/

/-- Set inclusion modeled on lists over a decidable domain. -/
def ListSubset (xs ys : List Nat) : Prop :=
  ∀ x, x ∈ xs → x ∈ ys

theorem listSubset_refl (xs : List Nat) : ListSubset xs xs := by
  intro x hx
  exact hx

theorem listSubset_trans {xs ys zs : List Nat}
    (h₁ : ListSubset xs ys) (h₂ : ListSubset ys zs) : ListSubset xs zs := by
  intro x hx
  exact h₂ x (h₁ x hx)

/-- Formal state of a Delegation Capability Token / Context in a delegation chain. -/
structure DelegationTokenState where
  tokenId   : Nat
  ops       : List Nat
  resources : List Nat
  caveats   : List Nat
  expiry    : Nat
  depth     : Nat
  maxDepth  : Nat
  budget    : Nat
  deriving DecidableEq, Repr

/-- An action request requires an operation, a target resource, a runtime
    caveat-satisfaction witness, and the current timestamp. -/
structure ActionContext where
  op                : Nat
  resource          : Nat
  unsatisfiedCaveat : Option Nat
  now               : Nat
  cost              : Nat
  deriving DecidableEq, Repr

/-- Predicate defining whether a token authorizes an action context. -/
def Authorizes (t : DelegationTokenState) (ctx : ActionContext) : Prop :=
  ctx.op ∈ t.ops ∧
  ctx.resource ∈ t.resources ∧
  (∀ c ∈ t.caveats, ctx.unsatisfiedCaveat ≠ some c) ∧
  ctx.now ≤ t.expiry ∧
  t.depth ≤ t.maxDepth ∧
  ctx.cost ≤ t.budget

/-- Single-hop monotonic attenuation relation between a parent token and child token.
    Enforces:
      - S_{k+1} ⊆ S_k (operations narrow, resources narrow, caveats accumulate)
      - E_{k+1} ≤ E_k (expiry cannot be extended)
      - d_{k+1} = d_k + 1 ≤ D_max (strict depth increment within ceiling)
      - β_{k+1} ≤ β_k (budget cannot escalate) -/
structure Attenuates (parent child : DelegationTokenState) : Prop where
  ops_sub       : ListSubset child.ops parent.ops
  res_sub       : ListSubset child.resources parent.resources
  caveats_super : ListSubset parent.caveats child.caveats
  expiry_le     : child.expiry ≤ parent.expiry
  depth_inc     : child.depth = parent.depth + 1
  depth_bound   : child.depth ≤ parent.maxDepth
  maxDepth_eq   : child.maxDepth = parent.maxDepth
  budget_le     : child.budget ≤ parent.budget

/-- **Theorem 1.1 (Single-Hop Authorization Subsumption)**:
    If `child` attenuates `parent`, then every action authorized by `child`
    is also authorized by `parent`. A child token can never widen permissions
    or outlive its parent. -/
theorem attenuates_subsumes_authorization
    {parent child : DelegationTokenState}
    (h_att : Attenuates parent child)
    (ctx : ActionContext)
    (h_auth : Authorizes child ctx) :
    Authorizes parent ctx := by
  rcases h_auth with ⟨h_op, h_res, h_cav, h_exp, _h_dep, h_bud⟩
  refine ⟨?_, ?_, ?_, ?_, ?_, ?_⟩
  · exact h_att.ops_sub ctx.op h_op
  · exact h_att.res_sub ctx.resource h_res
  · intro c hc
    exact h_cav c (h_att.caveats_super c hc)
  · exact Nat.le_trans h_exp h_att.expiry_le
  · have h_d : parent.depth < child.depth := by
      rw [h_att.depth_inc]
      exact Nat.lt_succ_self parent.depth
    exact Nat.le_of_lt (Nat.lt_of_lt_of_le h_d h_att.depth_bound)
  · exact Nat.le_trans h_bud h_att.budget_le

/-- Inductive multi-hop delegation chain from `root` to `leaf` in `k` hops. -/
inductive ValidChain : DelegationTokenState → DelegationTokenState → Nat → Prop where
  | root {t : DelegationTokenState} (h_valid : t.depth ≤ t.maxDepth) :
      ValidChain t t 0
  | step {root mid leaf : DelegationTokenState} {k : Nat}
      (h_chain : ValidChain root mid k)
      (h_att : Attenuates mid leaf) :
      ValidChain root leaf (k + 1)

/-- **Theorem 1.2 (Multi-Hop Monotonic Scope Attenuation)**:
    Along any valid `k`-hop delegation chain from `root` to `leaf`:
      1. `leaf.ops ⊆ root.ops`
      2. `leaf.resources ⊆ root.resources`
      3. `root.caveats ⊆ leaf.caveats`
      4. `leaf.expiry ≤ root.expiry`
      5. `leaf.budget ≤ root.budget`
      6. `leaf.depth = root.depth + k`
      7. `leaf.depth ≤ root.maxDepth`
      8. `leaf.maxDepth = root.maxDepth` -/
theorem chain_monotonic_attenuation
    {root leaf : DelegationTokenState} {k : Nat}
    (h_chain : ValidChain root leaf k) :
    ListSubset leaf.ops root.ops ∧
    ListSubset leaf.resources root.resources ∧
    ListSubset root.caveats leaf.caveats ∧
    leaf.expiry ≤ root.expiry ∧
    leaf.budget ≤ root.budget ∧
    leaf.depth = root.depth + k ∧
    leaf.depth ≤ root.maxDepth ∧
    leaf.maxDepth = root.maxDepth := by
  induction h_chain with
  | root h_valid =>
    refine ⟨listSubset_refl _, listSubset_refl _, listSubset_refl _,
            Nat.le_refl _, Nat.le_refl _, ?_, h_valid, rfl⟩
    omega
  | step _ h_att ih =>
    rcases ih with ⟨h_ops, h_res, h_cav, h_exp, h_bud, h_dep_eq, _h_dep_le, h_max_eq⟩
    refine ⟨listSubset_trans h_att.ops_sub h_ops,
            listSubset_trans h_att.res_sub h_res,
            listSubset_trans h_cav h_att.caveats_super,
            Nat.le_trans h_att.expiry_le h_exp,
            Nat.le_trans h_att.budget_le h_bud,
            ?_, ?_, ?_⟩
    · have h1 := h_att.depth_inc
      omega
    · have h2 := h_att.depth_bound
      omega
    · exact Eq.trans h_att.maxDepth_eq h_max_eq

/-- **Theorem 1.3 (Non-Escalation Along Arbitrary Delegation Chains)**:
    Any action context authorized by a descendant `leaf` token at hop `k`
    is necessarily authorized by the `root` token. -/
theorem chain_authorizes_implies_root_authorizes
    {root leaf : DelegationTokenState} {k : Nat}
    (h_chain : ValidChain root leaf k)
    (ctx : ActionContext)
    (h_auth : Authorizes leaf ctx) :
    Authorizes root ctx := by
  induction h_chain with
  | root _ => exact h_auth
  | step _ h_att ih =>
    exact ih (attenuates_subsumes_authorization h_att ctx h_auth)

/-- **Theorem 1.4 (No Lifetime Extension)**:
    If the root token has expired (`root.expiry < now`), then no descendant
    token in any valid chain can authorize an action at time `now`. -/
theorem expired_root_forbids_all_descendants
    {root leaf : DelegationTokenState} {k : Nat}
    (h_chain : ValidChain root leaf k)
    (ctx : ActionContext)
    (h_expired : root.expiry < ctx.now) :
    ¬ Authorizes leaf ctx := by
  intro h_auth
  have h_root := chain_authorizes_implies_root_authorizes h_chain ctx h_auth
  have h_le : ctx.now ≤ root.expiry := h_root.2.2.2.1
  omega

/-- **Theorem 1.5 (Bounded Chain Depth Ceiling)**:
    The number of delegation hops `k` in any valid chain from `root`
    cannot exceed `root.maxDepth - root.depth`. -/
theorem chain_hops_bounded_by_maxDepth
    {root leaf : DelegationTokenState} {k : Nat}
    (h_chain : ValidChain root leaf k) :
    k ≤ root.maxDepth - root.depth := by
  have h := chain_monotonic_attenuation h_chain
  have h_eq := h.2.2.2.2.2.1
  have h_le := h.2.2.2.2.2.2.1
  omega

/-! ## Section 2: Fail-Closed Absorption of KillSwitch and SafetyLatch -/

/-- Four graduated KillSwitch modes matching `hummbl_governance.KillSwitchMode`. -/
inductive KillSwitchMode where
  | DISENGAGED       : KillSwitchMode
  | HALT_NONCRITICAL : KillSwitchMode
  | HALT_ALL         : KillSwitchMode
  | EMERGENCY        : KillSwitchMode
  deriving DecidableEq, Repr

/-- Monotone severity rank of `KillSwitchMode`. -/
def modeRank : KillSwitchMode → Nat
  | .DISENGAGED       => 0
  | .HALT_NONCRITICAL => 1
  | .HALT_ALL         => 2
  | .EMERGENCY        => 3

/-- Three states of the hardware/persistence `SafetyLatch`. -/
inductive SafetyLatchState where
  | UNLOCKED : SafetyLatchState
  | ARMED    : SafetyLatchState
  | LOCKED   : SafetyLatchState
  deriving DecidableEq, Repr

/-- Monotone severity rank of `SafetyLatchState`. -/
def latchRank : SafetyLatchState → Nat
  | .UNLOCKED => 0
  | .ARMED    => 1
  | .LOCKED   => 2

/-- Coupled safety kernel state modeling `KillSwitch`, `SafetyLatch`,
    HMAC file integrity, and persistence failure latch (`_persistence_failed`). -/
structure CoupledSafetyState where
  ksMode            : KillSwitchMode
  latch             : SafetyLatchState
  fileIntegrityOk   : Bool
  persistenceFailed : Bool
  activeHaltEventId : Nat
  deriving DecidableEq, Repr

/-- Total fail-closed task permission function matching `KillSwitch.check_task_allowed`
    coupled with `SafetyLatch` and HMAC file-integrity verification. -/
def taskAllowed (s : CoupledSafetyState) (isCritical : Bool) : Bool :=
  if !s.fileIntegrityOk || s.persistenceFailed then
    false
  else
    match s.latch with
    | .LOCKED => false
    | _ =>
      match s.ksMode with
      | .DISENGAGED       => true
      | .HALT_NONCRITICAL => isCritical
      | .HALT_ALL         => isCritical
      | .EMERGENCY        => false

/-- **Theorem 2.1 (Fail-Closed on Corrupt State File or Failed Persistence)**:
    If HMAC file verification fails (`fileIntegrityOk = false`) or a state write
    latches a persistence failure (`persistenceFailed = true`), all tasks are blocked. -/
theorem fail_closed_on_integrity_or_persistence_fault
    (s : CoupledSafetyState) (isCritical : Bool)
    (h_fault : s.fileIntegrityOk = false ∨ s.persistenceFailed = true) :
    taskAllowed s isCritical = false := by
  unfold taskAllowed
  rcases h_fault with h_int | h_pers
  · simp [h_int]
  · simp [h_pers]

/-- **Theorem 2.2 (KillSwitch.EMERGENCY Blocks All Tasks Including Critical)**:
    When `ksMode = .EMERGENCY`, `taskAllowed` returns `false` for every task. -/
theorem emergency_blocks_all_tasks
    (s : CoupledSafetyState) (isCritical : Bool)
    (h_emg : s.ksMode = .EMERGENCY) :
    taskAllowed s isCritical = false := by
  unfold taskAllowed
  cases h_f : (!s.fileIntegrityOk || s.persistenceFailed)
  · simp
    cases h_l : s.latch <;> simp [h_emg]
  · rfl

/-- **Theorem 2.3 (SafetyLatch.LOCKED Blocks All Tasks Including Critical)**:
    When `latch = .LOCKED`, `taskAllowed` returns `false` for every task. -/
theorem latch_locked_blocks_all_tasks
    (s : CoupledSafetyState) (isCritical : Bool)
    (h_lock : s.latch = .LOCKED) :
    taskAllowed s isCritical = false := by
  unfold taskAllowed
  cases h_f : (!s.fileIntegrityOk || s.persistenceFailed)
  · simp [h_lock]
  · rfl

/-- Unprivileged runtime transitions (triggerable by agents, watchdogs, or storage faults
    without an authenticated operator K10 release receipt). -/
inductive UnprivilegedStep : CoupledSafetyState → CoupledSafetyState → Prop where
  | escalateKillSwitch {s : CoupledSafetyState} (newMode : KillSwitchMode) (evId : Nat)
      (h_not_disengaged : newMode ≠ .DISENGAGED)
      (h_monotone : modeRank s.ksMode ≤ modeRank newMode) :
      UnprivilegedStep s { s with ksMode := newMode, activeHaltEventId := evId }
  | tripLatch {s : CoupledSafetyState} (newLatch : SafetyLatchState)
      (h_monotone : latchRank s.latch ≤ latchRank newLatch) :
      UnprivilegedStep s { s with latch := newLatch }
  | storageWriteFailure {s : CoupledSafetyState} :
      UnprivilegedStep s { s with persistenceFailed := true, latch := .LOCKED }
  | tamperOrMissingFile {s : CoupledSafetyState} :
      UnprivilegedStep s { s with fileIntegrityOk := false, latch := .LOCKED }

/-- Multi-step unprivileged execution trajectory (reflexive-transitive closure). -/
inductive UnprivilegedTrajectory : CoupledSafetyState → CoupledSafetyState → Prop where
  | refl {s : CoupledSafetyState} : UnprivilegedTrajectory s s
  | tail {s₁ s₂ s₃ : CoupledSafetyState}
      (h_traj : UnprivilegedTrajectory s₁ s₂)
      (h_step : UnprivilegedStep s₂ s₃) :
      UnprivilegedTrajectory s₁ s₃

theorem latchRank_le_locked (l : SafetyLatchState) : latchRank l ≤ latchRank .LOCKED := by
  cases l <;> decide

/-- **Lemma 2.4 (Single-Step Monotonicity of KillSwitch and SafetyLatch Ranks)**:
    Every unprivileged step preserves or increases both `modeRank` and `latchRank`. -/
theorem unprivileged_step_monotone
    {s s' : CoupledSafetyState}
    (h_step : UnprivilegedStep s s') :
    modeRank s.ksMode ≤ modeRank s'.ksMode ∧
    latchRank s.latch ≤ latchRank s'.latch := by
  cases h_step with
  | escalateKillSwitch _ _ _ h_mono =>
    exact ⟨h_mono, Nat.le_refl _⟩
  | tripLatch _ h_mono =>
    exact ⟨Nat.le_refl _, h_mono⟩
  | storageWriteFailure =>
    exact ⟨Nat.le_refl _, latchRank_le_locked s.latch⟩
  | tamperOrMissingFile =>
    exact ⟨Nat.le_refl _, latchRank_le_locked s.latch⟩

/-- **Theorem 2.5 (Trajectory Monotonicity of KillSwitch and SafetyLatch)**:
    Across any finite sequence of unprivileged steps, neither `ksMode` nor `latch`
    can ever weaken. -/
theorem unprivileged_trajectory_monotone
    {s sFinal : CoupledSafetyState}
    (h_traj : UnprivilegedTrajectory s sFinal) :
    modeRank s.ksMode ≤ modeRank sFinal.ksMode ∧
    latchRank s.latch ≤ latchRank sFinal.latch := by
  induction h_traj with
  | refl => exact ⟨Nat.le_refl _, Nat.le_refl _⟩
  | tail _ h_step ih =>
    have h_next := unprivileged_step_monotone h_step
    exact ⟨Nat.le_trans ih.1 h_next.1, Nat.le_trans ih.2 h_next.2⟩

/-- Helper: any mode with `modeRank ≥ 3` is `.EMERGENCY`. -/
theorem mode_eq_emergency_of_rank_ge_three (m : KillSwitchMode)
    (h : 3 ≤ modeRank m) : m = .EMERGENCY := by
  cases m <;> trivial

/-- Helper: any latch state with `latchRank ≥ 2` is `.LOCKED`. -/
theorem latch_eq_locked_of_rank_ge_two (l : SafetyLatchState)
    (h : 2 ≤ latchRank l) : l = .LOCKED := by
  cases l <;> trivial

/-- **Theorem 2.6 (Fail-Closed Absorption of `KillSwitch.EMERGENCY`)**:
    Once `KillSwitch` enters `.EMERGENCY`, every state `sFinal` reachable via any
    unprivileged trajectory remains in `.EMERGENCY` and blocks all tasks. -/
theorem kill_switch_emergency_absorbing
    {s sFinal : CoupledSafetyState}
    (h_emg : s.ksMode = .EMERGENCY)
    (h_traj : UnprivilegedTrajectory s sFinal)
    (isCritical : Bool) :
    sFinal.ksMode = .EMERGENCY ∧ taskAllowed sFinal isCritical = false := by
  have h_mono := (unprivileged_trajectory_monotone h_traj).1
  rw [h_emg] at h_mono
  have h_eq : sFinal.ksMode = .EMERGENCY :=
    mode_eq_emergency_of_rank_ge_three sFinal.ksMode h_mono
  exact ⟨h_eq, emergency_blocks_all_tasks sFinal isCritical h_eq⟩

/-- **Theorem 2.7 (Fail-Closed Absorption of `SafetyLatch.LOCKED`)**:
    Once `SafetyLatch` enters `.LOCKED`, every state `sFinal` reachable via any
    unprivileged trajectory remains `.LOCKED` and blocks all tasks. -/
theorem safety_latch_locked_absorbing
    {s sFinal : CoupledSafetyState}
    (h_lock : s.latch = .LOCKED)
    (h_traj : UnprivilegedTrajectory s sFinal)
    (isCritical : Bool) :
    sFinal.latch = .LOCKED ∧ taskAllowed sFinal isCritical = false := by
  have h_mono := (unprivileged_trajectory_monotone h_traj).2
  rw [h_lock] at h_mono
  have h_eq : sFinal.latch = .LOCKED :=
    latch_eq_locked_of_rank_ge_two sFinal.latch h_mono
  exact ⟨h_eq, latch_locked_blocks_all_tasks sFinal isCritical h_eq⟩

/-! ## Section 3: Non-Bypassability of MonotonicGate & CircuitBreaker Invariants -/

/-- State of a `MonotonicGate` combining K4 sequence monotonicity (`SequenceEngine`),
    P27 forward-only canon/risk ratchet (`CanonRegistry`), and corruption latch. -/
structure MonotonicGateState where
  currentSeq : Nat
  canonLevel : Nat
  corrupted  : Bool
  deriving DecidableEq, Repr

/-- Input proposal to `MonotonicGate`. -/
structure GateProposal where
  proposedSeq      : Nat
  proposedLevel    : Nat
  operatorApproved : Bool
  deriving DecidableEq, Repr

/-- Decision predicate for `MonotonicGate`. -/
def gateCheck (g : MonotonicGateState) (p : GateProposal) : Bool :=
  (!g.corrupted) &&
  p.operatorApproved &&
  decide (g.currentSeq < p.proposedSeq) &&
  decide (g.canonLevel ≤ p.proposedLevel)

/-- State transition of `MonotonicGate`: returns `some g'` iff `gateCheck g p = true`. -/
def gateTransition (g : MonotonicGateState) (p : GateProposal) : Option MonotonicGateState :=
  if gateCheck g p then
    some { g with currentSeq := p.proposedSeq, canonLevel := p.proposedLevel }
  else
    none

/-- A guarded execution step can emit an observable effect `eff` from state `g`
    to `g'` under proposal `p` ONLY when `gateTransition g p = some g'`. -/
inductive GuardedExecution : MonotonicGateState → GateProposal → MonotonicGateState → Nat → Prop where
  | execute {g g' : MonotonicGateState} {p : GateProposal} (effectId : Nat)
      (h_pass : gateTransition g p = some g') :
      GuardedExecution g p g' effectId

/-- **Theorem 3.1 (Non-Bypassability & Strict Monotonicity of `MonotonicGate`)**:
    If a `GuardedExecution` step occurs, then:
      1. The gate was not corrupted (`g.corrupted = false`)
      2. Operator approval was verified (`p.operatorApproved = true`)
      3. Sequence ID strictly increased (`g.currentSeq < g'.currentSeq`)
      4. Canon/authority level did not regress (`g.canonLevel ≤ g'.canonLevel`) -/
theorem monotonic_gate_non_bypassable
    {g g' : MonotonicGateState} {p : GateProposal} {eff : Nat}
    (h_exec : GuardedExecution g p g' eff) :
    g.corrupted = false ∧
    p.operatorApproved = true ∧
    g.currentSeq < g'.currentSeq ∧
    g.canonLevel ≤ g'.canonLevel := by
  cases h_exec with
  | execute _ h_pass =>
    unfold gateTransition at h_pass
    split at h_pass
    · rename_i h_chk
      injection h_pass with h_eq
      subst h_eq
      unfold gateCheck at h_chk
      simp only [Bool.and_eq_true, Bool.not_eq_true', decide_eq_true_eq] at h_chk
      rcases h_chk with ⟨⟨⟨h_corr, h_appr⟩, h_seq⟩, h_lvl⟩
      exact ⟨h_corr, h_appr, h_seq, h_lvl⟩
    · contradiction

/-- **Theorem 3.2 (Replay and Rewind Rejection)**:
    Any proposal with `proposedSeq ≤ g.currentSeq` is deterministically rejected
    (`gateTransition g p = none`) and cannot produce a `GuardedExecution`. -/
theorem monotonic_gate_rejects_replay
    (g : MonotonicGateState) (p : GateProposal)
    (h_replay : p.proposedSeq ≤ g.currentSeq) :
    gateTransition g p = none := by
  unfold gateTransition gateCheck
  have h_not_lt : ¬ (g.currentSeq < p.proposedSeq) := by omega
  simp [h_not_lt]

/-- **Theorem 3.3 (Corrupted Gate Latch Fails Closed)**:
    If `g.corrupted = true` (e.g., corrupted `sequence_counters.json` under K4),
    `gateTransition g p = none` for all proposals `p`. -/
theorem monotonic_gate_corrupted_fails_closed
    (g : MonotonicGateState) (p : GateProposal)
    (h_corr : g.corrupted = true) :
    gateTransition g p = none := by
  unfold gateTransition gateCheck
  simp [h_corr]

/-- CircuitBreaker states matching `hummbl_governance.CircuitBreakerState`. -/
inductive CBMode where
  | CLOSED    : CBMode
  | OPEN      : CBMode
  | HALF_OPEN : CBMode
  deriving DecidableEq, Repr

structure CBState where
  mode          : CBMode
  failures      : Nat
  threshold     : Nat
  probeInFlight : Bool
  deriving DecidableEq, Repr

/-- Whether `CircuitBreaker.call` admits a request prior to executing `fn`. -/
def cbAdmits (s : CBState) : Bool :=
  match s.mode with
  | .CLOSED    => true
  | .OPEN      => false
  | .HALF_OPEN => !s.probeInFlight

/-- **Theorem 3.4 (CircuitBreaker OPEN Rejects & HALF_OPEN Enforces Single-Probe Mutex)**:
    An `OPEN` breaker admits no calls, and a `HALF_OPEN` breaker with a probe
    in flight rejects all concurrent calls. -/
theorem cb_open_and_half_open_mutex (s : CBState) :
    (s.mode = .OPEN → cbAdmits s = false) ∧
    (s.mode = .HALF_OPEN → s.probeInFlight = true → cbAdmits s = false) := by
  constructor
  · intro h_open
    unfold cbAdmits
    simp [h_open]
  · intro h_half h_probe
    unfold cbAdmits
    simp [h_half, h_probe]

/-! ## Section 4: Physical AI Watchdog Dead-Man's Switch & Telemetry Staleness Bound -/

/-- Telemetry freshness check: requires causal timestamp ordering (`tSample ≤ tNow`),
    bounded staleness (`tNow - tSample ≤ tauStale`), and strict sequence increase (`lastSeq < sampleSeq`). -/
def telemetryFresh (tNow tSample tauStale lastSeq sampleSeq : Nat) : Bool :=
  decide (tSample ≤ tNow) &&
  decide (tNow - tSample ≤ tauStale) &&
  decide (lastSeq < sampleSeq)

/-- Watchdog dead-man's switch update on `CoupledSafetyState`:
    if telemetry is stale or out-of-sequence, locks `SafetyLatch` and engages `.EMERGENCY`. -/
def watchdogStep (s : CoupledSafetyState) (tNow tSample tauStale lastSeq sampleSeq : Nat) :
    CoupledSafetyState :=
  if telemetryFresh tNow tSample tauStale lastSeq sampleSeq then
    s
  else
    { s with ksMode := .EMERGENCY, latch := .LOCKED }

/-- **Theorem 4.1 (Stale or Replayed Telemetry Trips Watchdog to Absorbing Halt)**:
    Whenever `tNow - tSample > tauStale` or `sampleSeq ≤ lastSeq`, `watchdogStep`
    transitions the safety kernel to `.EMERGENCY` and `.LOCKED`, blocking all tasks. -/
theorem stale_telemetry_trips_watchdog_halt
    (s : CoupledSafetyState)
    (tNow tSample tauStale lastSeq sampleSeq : Nat)
    (isCritical : Bool)
    (h_stale : tauStale < tNow - tSample ∨ sampleSeq ≤ lastSeq) :
    let s' := watchdogStep s tNow tSample tauStale lastSeq sampleSeq
    s'.ksMode = .EMERGENCY ∧
    s'.latch = .LOCKED ∧
    taskAllowed s' isCritical = false := by
  dsimp
  unfold watchdogStep telemetryFresh
  rcases h_stale with h_dt | h_seq
  · have h_not : ¬ (tNow - tSample ≤ tauStale) := by omega
    simp [h_not, emergency_blocks_all_tasks]
  · have h_not : ¬ (lastSeq < sampleSeq) := by omega
    simp [h_not, emergency_blocks_all_tasks]

-- Verify executable examples and print axiom dependencies
#eval taskAllowed ⟨.EMERGENCY, .UNLOCKED, true, false, 1⟩ true
#eval taskAllowed ⟨.DISENGAGED, .LOCKED, true, false, 1⟩ true
#eval gateTransition ⟨41, 2, false⟩ ⟨42, 3, true⟩
#eval gateTransition ⟨41, 2, false⟩ ⟨41, 3, true⟩
#eval taskAllowed (watchdogStep ⟨.DISENGAGED, .ARMED, true, false, 0⟩ 1250 1000 200 10 11) true

#print axioms attenuates_subsumes_authorization
#print axioms chain_monotonic_attenuation
#print axioms chain_authorizes_implies_root_authorizes
#print axioms expired_root_forbids_all_descendants
#print axioms chain_hops_bounded_by_maxDepth
#print axioms fail_closed_on_integrity_or_persistence_fault
#print axioms emergency_blocks_all_tasks
#print axioms latch_locked_blocks_all_tasks
#print axioms kill_switch_emergency_absorbing
#print axioms safety_latch_locked_absorbing
#print axioms monotonic_gate_non_bypassable
#print axioms monotonic_gate_rejects_replay
#print axioms monotonic_gate_corrupted_fails_closed
#print axioms cb_open_and_half_open_mutex
#print axioms stale_telemetry_trips_watchdog_halt

end HummblFormalization.GovernanceStateMachines
