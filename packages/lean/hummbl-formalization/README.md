# hummbl-formalization

Selected Lean 4 experiments from HUMMBL. Each theorem is scoped to the
definitions in its source file; this directory does not establish a complete
theory of cognition or governance.

## Exhibit gallery

Each file is independent: no project imports, Mathlib, credentials, or datasets.
The numbers and Boolean individuals are synthetic. With elan installed, run
these commands from this directory:

```bash
lean +leanprover/lean4:v4.34.0-rc2 examples/TreeRecovery.lean
lean +leanprover/lean4:v4.34.0-rc2 examples/OrderMatters.lean
lean +leanprover/lean4:v4.34.0-rc2 examples/QuantifierScope.lean
lean +leanprover/lean4:v4.34.0-rc2 examples/VacuousChecks.lean
```

| Exhibit | Question | Checked result |
| --- | --- | --- |
| [Tree recovery](examples/TreeRecovery.lean) | Can a leaf sequence determine every original tree? | A collision rules out a universal inverse. |
| [Order matters](examples/OrderMatters.lean) | Can we swap two transformations? | Left and right tree hooks disagree in both orders for every tree; mirroring twice restores a tree. |
| [Quantifier scope](examples/QuantifierScope.lean) | Does “everyone follows someone” mean one shared someone? | A shared witness implies individual witnesses; a two-person countermodel refutes the converse. |
| [Vacuous checks](examples/VacuousChecks.lean) | Do two test entries guarantee coverage of distinct pairs? | `[0, 0]` passes a distinct-pair condition while its entries fail; a distinct-partner hypothesis repairs the implication. |

### Order matters

For the input leaf `2`, inserting `0` on the left and `1` on the right yields
either `(0, (2, 1))` or `((0, 2), 1)`, depending on order. Both operations are
total. The difference is therefore about composition order, not an undefined
operation. A separate induction proves that mirroring twice recovers any tree.
These facts describe the defined tree functions; they do not establish an
algebra for all reasoning transformations.

### Quantifier scope

The two readings are `∀ person, ∃ someone, follows person someone` and
`∃ someone, ∀ person, follows person someone`. In the countermodel, two
individuals follow each other but not themselves. Everyone has someone to
follow, yet neither individual is followed by everyone.

This is a formal-semantics teaching model: the relation is supplied explicitly.
It illustrates the distinction between two readings without implementing
natural-language parsing or deciding which reading a speaker intended.

### Vacuous checks

The condition “every distinct pair passes” only imposes a requirement when
there is a distinct pair. A list with two copies of a failing input can satisfy
that condition. The general repair theorem adds the missing premise: each
listed input has a distinct listed partner. Together with the pairwise check,
this entails that every listed input passes. The theorem does not assert that
real test suites use this flawed criterion or that distinct inputs alone are
sufficient for useful coverage.

### What verification means

Every file prints its examples and the axiom dependencies of its theorems.
Check the compiler's exit status, not just the printed examples: an error can
produce partial output. Warnings are treated as errors. There are no admitted
proofs or custom axioms in these exhibits. The two duplicate-list proofs in
`VacuousChecks.lean` use Lean's standard propositional extensionality (`propext`)
through simplification; its other proofs and the other exhibits report no
axiom dependencies. These checks establish the statements for the supplied
definitions, not empirical claims about agents or language.

## Try a proof: what flattening loses

[TreeRecovery.lean](examples/TreeRecovery.lean) is a standalone exhibit using
Lean's built-in library. It has no Mathlib dependency and does not load the
surrounding Lake project.

With elan installed, run from this directory:

```bash
lean +leanprover/lean4:v4.34.0-rc2 examples/TreeRecovery.lean
```

Elan may download the pinned compiler on first use. After installation, the
example can be checked offline. Successful checking exits with status zero
and prints the two leaf lists, their tree-equality result, and each theorem's
axiom dependencies.

```text
[0, 1, 2]
[0, 1, 2]
false
```

The two trees group the same labels differently:

```text
((0, 1), 2)       (0, (1, 2))
       \             /
          [0, 1, 2]
```

| Theorem | What Lean checks |
| --- | --- |
| `decompose_compose` | Keeping ordered children recovers the original pair. |
| `flatten_collision` | Two distinct tree shapes produce the same leaf list. |
| `no_exact_reconstruction` | No function from leaf lists to trees reverses this flattening for every tree. |

This is a small example of how formal work can sharpen a representation
question. In linguistics, a token sequence and a parse tree are different
objects; the exhibit illustrates that distinction with numeric labels. It
does not implement a parser, model linguistic ambiguity, or prove a claim
about human language. In mathematics, the concrete collision supplies a
counterexample to a proposed universal inverse. In logic, that counterexample
is used to prove the negation of an existential statement.

The proof applies to the specified flattening map and unrestricted tree
domain. Preserving shape, restricting the domain, or asking only for the same
leaf sequence changes the problem. It is not a general impossibility result
for compression or reconstruction.

The source is an Apache-2.0 adaptation of HUMMBL's tree experiment, published
as selected code with synthetic inputs. It contains no runtime traces or
private repository history. The existing repository CI does not compile Lean;
use the pinned command above to reproduce verification.

## Other sketches

The surrounding Lake project contains separate mathematical sketches. These
commands build that project and may fetch its dependencies; they are not
needed for the standalone exhibit:

```bash
lake build
lake exe hummbl_formalization
```
