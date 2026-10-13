/- SPDX-License-Identifier: Apache-2.0
Selected adaptation of HUMMBL's tree transformation experiment.
These operations are concrete tree functions, not a general HUMMBL algebra.
-/
set_option warningAsError true

namespace OrderMatters

inductive Tree where
  | leaf : Nat → Tree
  | node : Tree → Tree → Tree
  deriving DecidableEq, Repr

def leftHook (t : Tree) : Tree := .node (.leaf 0) t
def rightHook (t : Tree) : Tree := .node t (.leaf 1)

/-- Both orders are defined, but they disagree for every input tree. -/
theorem hooks_noncomm (t : Tree) :
    leftHook (rightHook t) ≠ rightHook (leftHook t) := by
  intro h
  injection h with leftEqual _
  cases leftEqual

def mirror : Tree → Tree
  | .leaf n => .leaf n
  | .node l r => .node (mirror r) (mirror l)

/-- An operation can be reversible even when other operations do not commute. -/
theorem mirror_twice (t : Tree) : mirror (mirror t) = t := by
  induction t with
  | leaf n => rfl
  | node l r ihl ihr =>
    change Tree.node (mirror (mirror l)) (mirror (mirror r)) = Tree.node l r
    rw [ihl, ihr]

#eval leftHook (rightHook (.leaf 2))
#eval rightHook (leftHook (.leaf 2))
#eval mirror (mirror (.node (.leaf 2) (.leaf 3)))
#print axioms hooks_noncomm
#print axioms mirror_twice

end OrderMatters
