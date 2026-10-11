/-
SPDX-License-Identifier: Apache-2.0

Selected, self-contained adaptation of HUMMBL's tree composition/decomposition
experiment. Synthetic labels only. Uses Lean Init; no Mathlib or project imports.
Run the pinned command in the parent README. Proofs concern these definitions,
not arbitrary compression algorithms or natural-language understanding.
-/

set_option warningAsError true

namespace TreeRecovery

inductive Tree where
  | leaf : Nat → Tree
  | node : Tree → Tree → Tree
  deriving DecidableEq, Repr

def compose (parts : Tree × Tree) : Tree := .node parts.1 parts.2

def decompose : Tree → Option (Tree × Tree)
  | .leaf _ => none
  | .node left right => some (left, right)

def flatten : Tree → List Nat
  | .leaf label => [label]
  | .node left right => flatten left ++ flatten right

def leftAssoc : Tree := .node (.node (.leaf 0) (.leaf 1)) (.leaf 2)
def rightAssoc : Tree := .node (.leaf 0) (.node (.leaf 1) (.leaf 2))

/-- Keeping the ordered children permits exact recovery of composed parts. -/
theorem decompose_compose (parts : Tree × Tree) :
    decompose (compose parts) = some parts := by
  cases parts
  rfl

/-- Erasing shape makes two distinct trees observationally identical. -/
theorem flatten_collision :
    flatten leftAssoc = flatten rightAssoc ∧ leftAssoc ≠ rightAssoc := by
  constructor
  · rfl
  · intro h
    cases h

/-- No total function can undo this flattening for every tree. -/
theorem no_exact_reconstruction :
    ¬ ∃ recover : List Nat → Tree, ∀ tree, recover (flatten tree) = tree := by
  intro h
  obtain ⟨recover, correct⟩ := h
  have same : leftAssoc = rightAssoc := by
    calc
      leftAssoc = recover (flatten leftAssoc) := (correct leftAssoc).symm
      _ = recover (flatten rightAssoc) := congrArg recover flatten_collision.left
      _ = rightAssoc := correct rightAssoc
  exact flatten_collision.right same

-- Computed examples illustrate the collision; the theorems above prove it.
#eval flatten leftAssoc
#eval flatten rightAssoc
#eval decide (leftAssoc = rightAssoc)

-- Inspect the trusted assumptions of each advertised theorem.
#print axioms decompose_compose
#print axioms flatten_collision
#print axioms no_exact_reconstruction

end TreeRecovery
