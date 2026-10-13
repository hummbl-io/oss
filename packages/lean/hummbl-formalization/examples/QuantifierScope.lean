/- SPDX-License-Identifier: Apache-2.0
Synthetic relation illustrating quantifier scope. No language dataset or parser.
-/
set_option warningAsError true

namespace QuantifierScope

def EveryoneSomeone {Person : Type} (follows : Person → Person → Prop) : Prop :=
  ∀ person, ∃ someone, follows person someone

def SomeoneEveryone {Person : Type} (follows : Person → Person → Prop) : Prop :=
  ∃ someone, ∀ person, follows person someone

/-- A shared witness supplies an individual witness for each person. -/
theorem shared_implies_individual {Person : Type}
    (follows : Person → Person → Prop) :
    SomeoneEveryone follows → EveryoneSomeone follows := by
  intro ⟨someone, h⟩ person
  exact ⟨someone, h person⟩

-- Two synthetic individuals, represented by false and true.
-- Each follows the other, and neither follows themself.
abbrev follows (person someone : Bool) : Prop := person ≠ someone

theorem each_has_someone : EveryoneSomeone follows := by
  intro person
  cases person with
  | false => exact ⟨true, by decide⟩
  | true => exact ⟨false, by decide⟩

theorem no_shared_someone : ¬ SomeoneEveryone follows := by
  intro ⟨someone, h⟩
  exact h someone rfl

/-- The weaker reading does not imply the stronger reading. -/
theorem converse_fails : EveryoneSomeone follows ∧ ¬ SomeoneEveryone follows :=
  ⟨each_has_someone, no_shared_someone⟩

#eval decide (follows false true)
#eval decide (follows true false)
#eval decide (follows false false)
#print axioms shared_implies_individual
#print axioms each_has_someone
#print axioms no_shared_someone
#print axioms converse_fails

end QuantifierScope
