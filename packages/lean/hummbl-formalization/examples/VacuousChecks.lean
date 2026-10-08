/- SPDX-License-Identifier: Apache-2.0
Synthetic adaptation of HUMMBL's distinct-partner reachability argument.
A list's length alone does not establish coverage of distinct cases.
-/
set_option warningAsError true

namespace VacuousChecks

def PairwisePass {Case : Type} (cases : List Case) (passes : Case → Prop) : Prop :=
  ∀ a ∈ cases, ∀ b ∈ cases, a ≠ b → passes a ∧ passes b

def AllPass {Case : Type} (cases : List Case) (passes : Case → Prop) : Prop :=
  ∀ a ∈ cases, passes a

abbrev passes (n : Nat) : Prop := n = 1

theorem two_entries : ([0, 0] : List Nat).length = 2 := rfl

/-- The duplicate list has no distinct pair, so the implication never fires. -/
theorem duplicates_pass_pairwise : PairwisePass [0, 0] passes := by
  intro a ha b hb different
  have aZero : a = 0 := by simpa using ha
  have bZero : b = 0 := by simpa using hb
  exact (different (aZero.trans bZero.symm)).elim

theorem duplicates_fail_all : ¬ AllPass [0, 0] passes := by
  intro h
  have impossible : (0 : Nat) = 1 := h 0 (by simp)
  cases impossible

/-- Coverage repair: each listed case must have a distinct listed partner. -/
theorem all_of_pairwise_and_partner {Case : Type}
    (cases : List Case) (passes : Case → Prop)
    (pairwise : PairwisePass cases passes)
    (partner : ∀ a ∈ cases, ∃ b ∈ cases, a ≠ b) :
    AllPass cases passes := by
  intro a ha
  obtain ⟨b, hb, different⟩ := partner a ha
  exact (pairwise a ha b hb different).left

#eval ([0, 0] : List Nat).length
#eval decide (passes 0)
#print axioms two_entries
#print axioms duplicates_pass_pairwise
#print axioms duplicates_fail_all
#print axioms all_of_pairwise_and_partner

end VacuousChecks
