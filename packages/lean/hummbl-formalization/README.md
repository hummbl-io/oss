# hummbl-formalization

Selected Lean 4 experiments from HUMMBL. Each theorem is scoped to the
definitions in its source file; this directory does not establish a complete
theory of cognition or governance.

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
