/-
# Ashby ↔ Wissner-Gross: Log-Order Isomorphism and Path Entropy

This module formalizes preliminary results toward the HUMMBL
doctrine's claim that Ashby's Law of Requisite Variety and
Wissner-Gross's causal entropic principle are "dual statements."

## What this module ACTUALLY proves (honest scope)

1. **Ashby's Law (simple form)**: if a regulator counters a
   disturbance, the target is in the regulator's range. This is
   a building block, NOT the full requisite-variety theorem.

2. **Path entropy monotonicity**: log is monotone on positive
   naturals. More paths → higher entropy. This is a property of
   the log function, not specific to Wissner-Gross's dynamics.

3. **Log-order isomorphism on positive naturals**: for v₁, v₂ ≥ 1,
   v₁ ≥ v₂ ↔ log(v₁) ≥ log(v₂). This is a generic fact about the
   order-embedding property of log, NOT yet a bridge between
   Ashby's cybernetic structures and Wissner-Gross's dynamical
   structures. The two sides are bare ℕ variables, not quantities
   derived from actual Regulator/Disturbance/Path objects.

4. **Governance reduces path entropy**: constraining path count
   reduces entropy. This is monotonicity applied in reverse.

5. **Governance preserves non-negative entropy**: a constrained
   system with ≥1 path still has entropy ≥ 0. This is a property
   of log on [1, ∞), NOT a proof of the HUMMBL complementarity
   thesis (which would require showing necessity/trade-off with
   respect to target-reaching).

## What this module does NOT prove (honest gaps)

- It does NOT prove the full Ashby-Wissner-Gross duality. The
  duality theorem (`log_order_iso_on_pos_nat`) proves a generic
  fact about log. To make it a genuine duality, the file would
  need a shared underlying object connecting Ashby's variety
  (Fintype.card of a regulator's state space) to Wissner-Gross's
  path count (cardinality of paths in a dynamical system). This
  connection is future work.

- It does NOT prove the HUMMBL governance complementarity thesis.
  `governance_preserves_nonneg_entropy` proves that a constrained
  system has non-negative entropy, not that governance is
  NECESSARY for goal-directed action. A real complementarity
  theorem would need to show that unconstrained path-space
  maximization fails to reach a specific target, and that
  governance's constraint restores target-reaching.

- It does NOT formalize Wissner-Gross's causal entropic FORCE
  (F = T_c ∇S_c), the causal horizon τ, or the dynamical content
  of the 2013 paper. `causalPathEntropy` is "log of a count,"
  which is the thinnest possible slice of the theory.

- `ashby_law_simple` does NOT use `variety` (Fintype.card). The
  full Ashby theorem (pigeonhole over cardinality) is future work.

## Lessons applied from peer review of McShea proof

- No definition is identical to the conclusion it's used to prove
- Every hypothesis is load-bearing (no inert premises, no
  underscore-silenced unused variables)
- Definitions match the actual theory
- What is definitionally true vs substantively proven is stated
  explicitly (see above)
- Theorems are named after what they PROVE, not after the theory
  they ASPIRE to formalize

## Sources

- Ashby, W. R. (1956). An Introduction to Cybernetics. Chapman & Hall.
  §11/5: "only variety can absorb variety"
- Wissner-Gross & Freer (2013). Causal Entropic Forces.
  Phys. Rev. Lett. 110, 168702.
- HUMMBL doctrine: foundations/WISSNER_GROSS.md
  "Ashby and Wissner-Gross are the dual statements"
- Peer review: peer-review-ashby-wg-claude-sonnet-5-2026-08-25.md
  (7 issues flagged, 6 addressed in this revision)
-/

import Mathlib.Data.Fintype.Basic
import Mathlib.Data.Real.Basic
import Mathlib.Analysis.SpecialFunctions.Log.Basic

namespace HummblFormalization.AshbyWissnerGross

/-! ## Core definitions

We model "variety" (Ashby's term) as the cardinality of a finite
type, and "causal path entropy" (Wissner-Gross's term) as the
log of a path count. The key insight for the future duality: both
are measures of "how many possibilities," related by a monotone
function (log), so the inequality direction is preserved.

NOTE: `variety` is defined here for future use in the full Ashby
theorem (pigeonhole over Fintype.card). It is not yet used in any
theorem in this file. The full Ashby theorem is future work.
-/

/-- The variety of a finite type is its cardinality.

Ashby (1956, §7/3): "variety is the number of possible
indistinguishable states." We use Fintype.card.

NOTE: Not yet used in any theorem below. Reserved for the full
Ashby pigeonhole theorem (future work). -/
def variety (α : Type) [Fintype α] : ℕ :=
  Fintype.card α

/-- A disturbance is a function from states to states.

Ashby models the disturbance as a mapping that transforms the
system's state. The regulator must be able to counter each
possible transformation. -/
def Disturbance (α : Type) := α → α

/-- A regulator is a function from states to states.

The regulator's job is to map any state the disturbance produces
back to a desired/target state. -/
def Regulator (α : Type) := α → α

/-! ## Ashby's Law of Requisite Variety (simple form)

Ashby's Law (1956, §11/5): "only variety can absorb variety."
The full formal statement requires a pigeonhole argument over
Fintype.card: if the regulator's output variety < the
disturbance's input variety, there exist disturbances the
regulator cannot counter. This is future work.

Here we prove the simplest non-trivial form: if a regulator
counters a disturbance, the target is in the regulator's range.
This is a building block for the full theorem, not the full
theorem itself.
-/

/-- A regulator "counters" a disturbance if applying the
disturbance then the regulator always yields the target state. -/
def Counters {α : Type} (reg : Regulator α) (dist : Disturbance α)
    (target : α) : Prop :=
  ∀ s : α, reg (dist s) = target

/-- **Ashby's Law (simple form)**: if a regulator counters at
least one disturbance, then the regulator's image includes
the target state.

This is a building block for the full requisite-variety theorem
(which would use `variety` and a pigeonhole argument). It is
NOT the full Ashby Law — it does not mention variety or
cardinality. It establishes that a regulating regulator must
be able to produce the target state. -/
theorem ashby_law_simple
    {α : Type} [Nonempty α]
    (reg : Regulator α)
    (dist : Disturbance α)
    (target : α)
    (h_counters : Counters reg dist target) :
    ∃ s : α, reg s = target := by
  -- If the regulator counters the disturbance, then for any
  -- state s, reg (dist s) = target. So (dist s) is a witness.
  exact ⟨dist (Classical.arbitrary α), h_counters _⟩

/-! ## Causal Path Entropy (Wissner-Gross)

Wissner-Gross defines causal path entropy as the log of the
number of accessible future paths over horizon τ. We formalize
this as the log of the path count.

NOTE: This is the thinnest possible formalization. It captures
"log of a count" but does NOT model:
- The causal horizon τ (central to the 2013 paper and HUMMBL doctrine)
- Path structure (no type of "paths," no dynamics, no state-space)
- The causal entropic force F = T_c ∇S_c (the dynamical claim)
- The causal temperature T_c

What remains is the monotonicity property: more paths → higher
entropy. This is true of any counting measure and carries none
of the dynamical content specific to Wissner-Gross's theory.
-/

/-- Causal path entropy: the log of the number of accessible
paths. We use real-valued entropy (in nats).

For a deterministic system with 1 path, entropy = log(1) = 0.
For a non-deterministic system with k paths, entropy = log(k).

NOTE: This is "log of a count," not the full Wissner-Gross
formalism. See module header for what is not modeled. -/
noncomputable def causalPathEntropy (pathCount : ℕ) : ℝ :=
  Real.log (pathCount : ℝ)

/-- **Monotonicity of path entropy**: if system A has more
accessible paths than system B, then A has higher causal path
entropy.

This is a property of the log function (monotonicity on positive
reals), not specific to Wissner-Gross's dynamics. It is the
"more options → higher log-count" fact, which is true of any
counting measure.

The proof uses `Real.log_le_log` from Mathlib. -/
theorem path_entropy_monotone
    (k₁ k₂ : ℕ) (h : k₁ ≥ k₂) (h_pos : k₂ ≥ 1) :
    causalPathEntropy k₁ ≥ causalPathEntropy k₂ := by
  -- log is monotone on positive reals
  -- k₁ ≥ k₂ ≥ 1, so (k₁ : ℝ) ≥ (k₂ : ℝ) ≥ 1 > 0
  have hk₂_pos : (0 : ℝ) < (k₂ : ℝ) := by
    have : 0 < k₂ := by omega
    exact_mod_cast this
  have hk₁_ge_k₂ : (k₁ : ℝ) ≥ (k₂ : ℝ) := by
    exact_mod_cast h
  -- Real.log_le_log : 0 < x → x ≤ y → log x ≤ log y
  exact Real.log_le_log hk₂_pos hk₁_ge_k₂

/-! ## Log-Order Isomorphism on Positive Naturals

This section proves a generic fact about the log function: on
positive naturals, the order is preserved and reflected by log.
Specifically, for v₁, v₂ ≥ 1: v₁ ≥ v₂ ↔ log(v₁) ≥ log(v₂).

This is NOT the Ashby-Wissner-Gross duality. It is a building
block toward it. The duality would require showing that Ashby's
variety (Fintype.card of a regulator's state space) and
Wissner-Gross's path count (cardinality of paths in a dynamical
system) are the same underlying quantity, then applying this
isomorphism. That connection is future work.

The theorem is named `log_order_iso_on_pos_nat` (not
`ashby_wissner_gross_duality`) to honestly reflect what it
proves: a property of log, not a bridge between two theories.
-/

/-- **Log-order isomorphism on positive naturals**: for v₁, v₂ ≥ 1,
v₁ ≥ v₂ ↔ log(v₁) ≥ log(v₂).

Forward: log is monotone (Real.log_le_log).
Backward: log is strictly monotone (Real.log_lt_log), applied
via contrapositive.

This is a generic fact about the order-embedding property of
log on [1, ∞). It is a building block toward the Ashby-Wissner-
Gross duality, not the duality itself. To make it a duality,
the variables would need to be derived from actual Ashby
structures (Regulator, Disturbance, variety) and Wissner-Gross
structures (paths, horizon τ), not bare ℕ. -/
theorem log_order_iso_on_pos_nat
    (v₁ v₂ : ℕ)
    (h_pos₁ : v₁ ≥ 1)
    (h_pos₂ : v₂ ≥ 1) :
    (v₁ ≥ v₂) ↔
    (causalPathEntropy v₁ ≥ causalPathEntropy v₂) := by
  constructor
  · -- Forward: log is monotone
    intro h
    exact path_entropy_monotone v₁ v₂ h h_pos₂
  · -- Backward: log is strictly monotone (contrapositive)
    intro h_wg
    by_contra h_not
    have h_lt_nat : v₁ < v₂ := by omega
    -- v₁ < v₂
    have h_lt : (v₁ : ℝ) < (v₂ : ℝ) := by
      exact_mod_cast h_lt_nat
    have h_pos₁_real : (0 : ℝ) < (v₁ : ℝ) := by
      have : 0 < v₁ := by omega
      exact_mod_cast this
    have h_pos₂_real : (0 : ℝ) < (v₂ : ℝ) := by
      have : 0 < v₂ := by omega
      exact_mod_cast this
    -- log(v₁) < log(v₂) since log is strictly monotone
    have h_log_lt : Real.log (v₁ : ℝ) < Real.log (v₂ : ℝ) := by
      exact Real.log_lt_log h_pos₁_real h_lt
    -- But h_wg says log(v₁) ≥ log(v₂) — contradiction
    have : causalPathEntropy v₁ < causalPathEntropy v₂ := h_log_lt
    linarith

/-! ## Governance as Path-Space Constraint

The HUMMBL thesis: governance is the complementary force to
intelligence. Intelligence maximizes path entropy
(Wissner-Gross); governance constrains it.

NOTE: The theorems below prove that governance REDUCES entropy
(monotonicity) and PRESERVES non-negative entropy (positivity of
log on [1,∞)). They do NOT prove the full complementarity
thesis, which would require showing that governance is NECESSARY
for goal-directed action (i.e., unconstrained path-space
maximization fails to reach a specific target, and governance's
constraint restores target-reaching). That is future work.
-/

/-- **Governance reduces path entropy**: if governance constrains
the path count from k_unconstrained to k_constrained
(k_constrained ≤ k_unconstrained), then the constrained system
has ≤ path entropy.

This is monotonicity of log applied in the constraint direction.
It formalizes "governance constrains intelligence" at the level
of path-count comparison, not the full complementarity thesis. -/
theorem governance_reduces_path_entropy
    (k_unconstrained k_constrained : ℕ)
    (h_constrained : k_constrained ≤ k_unconstrained)
    (h_constrained_pos : k_constrained ≥ 1) :
    causalPathEntropy k_constrained ≤ causalPathEntropy k_unconstrained := by
  have h_le : k_unconstrained ≥ k_constrained := h_constrained
  have h_pos : k_constrained ≥ 1 := h_constrained_pos
  exact path_entropy_monotone k_unconstrained k_constrained h_le h_pos

/-- **Governance preserves non-negative entropy**: if governance
constrains the path count but preserves at least 1 path, the
constrained system has entropy ≥ 0 (can still act).

This proves two facts:
1. Governance reduces entropy (constraint direction)
2. The governed system has non-negative entropy (log ≥ 0 for k ≥ 1)

NOTE: This is NOT the HUMMBL complementarity thesis. A real
complementarity theorem would need to show that unconstrained
path-space maximization FAILS to reach a specific target, and
that governance's constraint RESTORES target-reaching. This
theorem proves monotonicity + positivity, not necessity or
trade-off. -/
theorem governance_preserves_nonneg_entropy
    (k_intelligence k_governed : ℕ)
    (h_governance_reduces : k_governed ≤ k_intelligence)
    (h_governance_preserves : k_governed ≥ 1) :
    -- Governance reduces entropy (constraint)
    (causalPathEntropy k_governed ≤ causalPathEntropy k_intelligence) ∧
    -- But the governed system still has non-negative entropy (can act)
    (causalPathEntropy k_governed ≥ 0) := by
  refine ⟨?_, ?_⟩
  · exact governance_reduces_path_entropy k_intelligence k_governed
      h_governance_reduces h_governance_preserves
  · -- log(k) ≥ 0 when k ≥ 1, since log(1) = 0 and log is monotone
    show Real.log (k_governed : ℝ) ≥ 0
    have h_k_ge_one : (1 : ℝ) ≤ (k_governed : ℝ) := by
      exact_mod_cast h_governance_preserves
    have h_log_ge_log_one : Real.log (1 : ℝ) ≤ Real.log (k_governed : ℝ) := by
      exact Real.log_le_log (by norm_num) h_k_ge_one
    have h_log_one : Real.log (1 : ℝ) = 0 := by simp
    linarith

end HummblFormalization.AshbyWissnerGross
