# Java Editions Feasibility Research Report

**Research Date**: 2026-08-20
**Goal**: Investigate whether an "editions" or "epochs" mechanism (C++ P1881, Rust editions) could work for Java at the language layer
**Source**: subagent_explore (background), saved by parent (subagent was read-only)

---

## Executive Summary

This report investigates the feasibility of implementing an "editions" or "epochs" mechanism for Java — similar to C++ P1881 or Rust editions — that would allow opt-in language modes enabling breaking changes while preserving cross-edition interoperability.

**Key Finding**: An editions mechanism for Java faces significant technical and cultural barriers that make it substantially more challenging than in Rust or C++. The primary obstacles are Java's binary compatibility requirements, the JVM's design philosophy, and the absence of any serious community discussion of such a mechanism. While theoretically possible, an editions system would likely require substantial JVM specification changes and would unlock only marginal benefits given Java's existing compatibility strategies.

---

## 1. C++ P1881 Analysis

### What P1881 Proposes

**Paper**: "Epochs: a backward-compatible language evolution mechanism" by Vittorio Romeo (P1881R0: 2019, P1881R1: 2020)

**Core Mechanism**: P1881 proposes adding an opt-in module-level switch called an "epoch declaration" that changes the meaning of source code within a module unit:

```cpp
epoch 2023;
module ParticleMovement;
export void move(Particle&, float x, float y);
```

**Key Features**:
- Epochs are applied at the module unit level (refined from module-level in R1)
- Different module partitions can target different epochs
- Epochs are named by year (e.g., `epoch 2023`)
- Migration is never mandatory
- Epochs must not affect ABI (Application Binary Interface)
- Changes are "skin deep" — they affect how source transforms to AST, not the final binary

**Cross-Epoch Interoperability**:
- Module units can import and consume other modules targeting different epochs
- Restrictions apply only to the source code where the module unit is defined, not to importers
- Different epochs must be normalized to the same intermediate format (e.g., AST) during compilation

**Motivation**: The proposal addresses C++'s accumulation of obsolete constructs, dangerous defaults, and design mistakes that cannot be removed due to backward compatibility constraints. Examples: `typedef` (superseded by `using`), `std::bind` (superseded by lambdas), implicit conversions, uninitialized variables, macros.

### Status

**Current Status**: **Stalled/Closed**

- **Belfast 2019**: EWG-I poll showed strong interest (22 SF, 2 F, 2 N, 0 A, 0 SA) in solving the problem
- **Consensus**: Bring a revision to the Tooling Study Group (SG15)
- **Prague 2019**: EWG-I poll confirmed the problem is worth solving (1 SF, 17 F, 4 N, 2 A, 0 SA)
- **GitHub Issue #631**: Marked as "closed" with last activity in March 2021

The proposal has not been accepted into any C++ standard. It remains in committee limbo, with no active development since 2021.

### Objections and Concerns

**Technical Objections**:
1. **Implementation Complexity**: Compiler vendors would need to perform "humongous amount of work"
2. **Module Dependency**: Tightly coupled to C++20 modules, which have seen slow adoption
3. **Normalization Overhead**: Different epochs must be normalized to the same intermediate format

**Philosophical Objections**:
1. **Scope Concerns**: Whether epochs should be at module level, translation unit level, or block scope
2. **User-Defined Rulesets**: Strong opposition (15 SA, 5 N, 2 F, 0 SF, 2 WA)
3. **Feature Placement**: Debate over whether new non-breaking features should always be confined to the latest epoch (4 SF, 4 F, 4 N, 5 A, 4 SA)

**Sources**: P1881R1 (open-std.org), GitHub Issue #631, ISO C++ Status

---

## 2. Rust Editions Analysis

### How Rust Editions Work

**Core Mechanism**: Rust editions are opt-in language modes specified in `Cargo.toml`:

```toml
[package]
name = "my_crate"
version = "0.1.0"
edition = "2021"
```

**Key Principles**:
1. **Opt-in**: Existing crates don't see edition changes unless they explicitly migrate
2. **No Ecosystem Split**: Crates in different editions must seamlessly interoperate
3. **Skin-Deep Changes**: Edition changes only affect parsing; all editions compile to the same internal representation (MIR)
4. **Automated Migration**: `cargo fix --edition` automates most migrations
5. **Gradual Adoption**: Each crate can migrate independently without affecting dependencies

**Edition History**:
- **Rust 2015**: Original edition (default if unspecified)
- **Rust 2018**: Introduced `async`/`await` keywords, module system changes
- **Rust 2021**: Minor edition, more limited in scope
- **Rust 2024**: Largest edition to date (released February 2025)

### Cross-Edition Interoperability

**Technical Mechanism**:
- Editions only affect the parser and early compilation stages
- The AST is largely identical across editions
- HIR (High-level IR) and MIR (Mid-level IR) are edition-agnostic
- The compiler tracks edition information in spans for context-aware parsing

**Example**: `async` is only treated as a keyword in edition 2018+ — the compiler checks `self.span.rust_2018()`.

### What Can Change Between Editions

**Allowed Changes** (from Rust 2024):
- New keywords (e.g., `async`, `await` in 2018)
- Changes to temporary scope rules
- RPIT (Return Position Impl Trait) lifetime capture rules
- Match ergonomics reservations
- Unsafe attribute requirements (`export_name`, `link_section`, `no_mangle` now require `unsafe`)
- Macro fragment specifier changes

**What Cannot Change**:
- **ABI**: Editions must not change the binary interface
- **MIR Semantics**: The internal representation's semantics must remain stable
- **Trait Coherence**: Global type system properties cannot be edition-specific
- **Type Inference Rules**: Changes that affect cross-crate type inference are limited

**Limitations**: The requirement for cross-edition interoperability means changes must be "skin deep." As the RFC states: "Edition can change the way that concrete Rust syntax is desugared into MIR, but doesn't change the semantics of MIR itself."

### Migration Process

```bash
cargo update
cargo fix --edition
# Edit Cargo.toml to set edition = "2024"
cargo build
cargo fmt
```

**Migration Philosophy**: "If it's difficult for you to upgrade to the latest edition, we consider that a bug."

**Sources**: Rust Edition Guide, Rust 2024 Announcement, RFC 3085, Compiler Dev Guide

---

## 3. Java Community Discussion of Editions

### Search Results: No Evidence of Editions Proposals

Comprehensive searches for: "Java editions mechanism", "Java language modes", "Java opt-in breaking changes", "Java epoch proposal", "Java versioned source", "openjdk editions", "openjdk epochs", "openjdk language mode".

**Result**: **Zero relevant hits** for an editions/epochs mechanism in the Java community.

### What Java Does Have Instead

**1. Source Version Flags (`-source`, `--release`)** (JEP 247):
- `javac -source N`: Compile with language features from version N
- `javac --release N`: Compile for specific platform version
- These are **backward compatibility** mechanisms, not opt-in breaking changes

**2. Multi-Release JAR Files (JEP 238)**:
- Multiple versions of class files in a single JAR
- **Purpose**: Forward compatibility, not language evolution

**3. Preview Features (Project Amber)**:
- New language features released as "preview" for one or more releases
- Must be explicitly enabled with `--enable-preview`
- Can be withdrawn if feedback is negative (e.g., String Templates)
- **Purpose**: Safe experimentation, not breaking changes

**4. Deprecation and Removal Process**:
- APIs are deprecated for at least one major release before removal
- Examples: Security Manager (deprecated Java 17, removal planned), Applet API (removed Java 21)
- **Purpose**: Gradual cleanup, not editions

### Brian Goetz and Language Architects' Positions

**Brian Goetz's Philosophy** (from "Move Deliberately and Don't Break Anything"):
- "Breaking changes undermine investment in code and trust in Java"
- Emphasizes backward compatibility as a core Java value
- Default methods (Java 8) were designed to enable interface evolution without breaking existing implementations

**Mailing List Discussions**:
- **Checked Exceptions (2019)**: OpenJDK developers acknowledge checked exceptions are problematic but see no viable transition path
- **Binary Compatibility**: Extensive discussion about maintaining binary compatibility when adding methods to interfaces
- **No Editions Discussion**: Despite extensive debate on compatibility, no one has proposed an editions mechanism

**Key Quote** (lambda-dev mailing list, 2012):
> "Unless we're willing to freeze the platform in concrete (we're not), what we can do is try and reduce the surface area of potential conflicts."

This suggests incremental, conservative evolution rather than editions-style breaking changes.

**Sources**: JEP 247, JEP 238, Project Amber, Brian Goetz Presentation (infoq.com), lambda-dev mailing list

---

## 4. Technical Feasibility Analysis for Java Editions

### Proposed Mechanism: `--source-edition 2026`

**Hypothetical Usage**:
```bash
javac --source-edition 2026 MyClass.java
```

This would enable breaking changes such as:
- Removing checked exceptions
- Making nullability explicit (non-null by default)
- Reifying generics (removing type erasure)
- Removing raw types
- Changing overload resolution rules

### Technical Barriers

#### Barrier 1: Binary Compatibility Requirements

**Java's Core Contract**: The JVM specification requires that class files compiled with older JDK versions must run on newer JVMs. The bytecode format is stable across versions. Method signatures and field types must match exactly.

**Problem with Editions**:
- If Edition 2026 removes checked exceptions, method signatures would change
- Existing bytecode expecting checked exceptions would break
- Cross-edition interoperability would require ABI changes, violating JVM compatibility guarantees

**Contrast with Rust**: Rust editions work because Rust has no stable ABI across crates by default — each crate is statically linked, editions only affect parsing, not the final binary.

**Contrast with C++**: C++ epochs work because C++ has no stable ABI across compilers/versions — templates are instantiated per translation unit, and the proposal explicitly requires epochs to not affect ABI.

#### Barrier 2: Type Erasure and Generics

**Current State**: Java generics use type erasure — `List<String>` compiles to `List` in bytecode, type parameters are erased at compile time, bridge methods are generated for compatibility.

**Reified Generics in an Edition**:
- Would require changing the bytecode format to include type parameters
- Existing bytecode without type information couldn't interoperate
- Would require "flag day" migration of all libraries

**From Project Valhalla Documentation**:
> "It must be possible to evolve an existing non-generic class to be generic in a binary-compatible and source-compatible manner. Without this requirement, generifying a class would require a 'flag day' where all clients and subclasses have to be at least recompiled, if not modified — all at once."

This requirement is why Java chose type erasure. An edition mechanism would violate this.

#### Barrier 3: JVM Specification Changes

**Required Changes**:
1. **Class File Format**: New attributes for edition metadata
2. **Verification Logic**: Different verification rules per edition
3. **Linking**: Cross-edition method resolution
4. **Reflection**: API to query edition information
5. **JCK (Java Compatibility Kit)**: New tests for edition interoperability

**Scope**: These are not trivial changes. They would require a JSR process, multi-year development timeline, coordination across all JVM vendors (Oracle, OpenJDK, IBM, Azul, etc.), and updates to all JVM-based languages (Kotlin, Scala, Groovy).

#### Barrier 4: Library Ecosystem

**Java's Dependency Graph**: Millions of libraries in Maven Central, deep transitive dependency chains, mixed-version deployments common.

**Edition Migration Challenge**:
- If Library A uses Edition 2026 and Library B uses Edition 2025:
  - Can they depend on each other?
  - What if A's API removes checked exceptions that B expects?
  - What if A reifies generics that B expects erased?

**Contrast with Rust**: Rust's Cargo ecosystem is newer (2015), fewer transitive dependencies on average, crates are more frequently updated, edition interoperability is designed into the compiler from the start.

#### Barrier 5: Tooling Ecosystem

**Affected Tools**: IDEs (IntelliJ, Eclipse, VS Code), build tools (Maven, Gradle), static analysis tools (SpotBugs, Checkstyle), bytecode manipulation libraries (ASM, Byte Buddy), application servers (Tomcat, WildFly, WebSphere).

**Migration Cost**: Each tool would need to parse edition metadata, apply edition-specific rules, support cross-edition analysis, update plugins and integrations.

**Historical Precedent**: The Java 9 module system (Project Jigsaw) required massive tooling updates and caused significant ecosystem disruption. An editions mechanism would be comparable in scope.

### What Could Work (Limited Editions)

**Possible Edition Changes** (if barriers were addressed):
1. **Keyword Reservations**: Reserve new keywords (like Rust's `async`)
2. **Warning Promotions**: Turn warnings into errors in new editions
3. **Deprecation Enforcement**: Strengthen deprecation warnings
4. **Syntax Cleanup**: Remove rarely-used syntax (e.g., `goto` keyword reservation)

**Not Possible** (due to ABI):
1. Removing checked exceptions
2. Reifying generics
3. Changing method overload resolution
4. Removing null from reference types
5. Changing primitive type semantics

### Project Leyden Impact

**Project Leyden Goals**: Improve startup time, time to peak performance, and footprint. Introduce AOT (Ahead-of-Time) compilation. Static images with closed-world constraints.

**Relevance to Editions**:
- AOT could theoretically make editions easier by eliminating dynamic class loading constraints, allowing whole-program optimization, enabling edition-specific optimizations at compile time
- **However**: Leyden's "condensers" are opt-in transformations; the project explicitly aims to preserve "Java's core values of readability, compatibility, and generality"; closed-world constraints are weaker than full editions; Leyden does not propose language-level editions

**From Leyden Documentation**:
> "We will explore a spectrum of constraints, weaker than the closed-world constraint, and discover what optimizations they enable."

This suggests gradual optimization, not editions-style breaking changes.

**Sources**: Project Valhalla, Project Leyden, JEP 514, JEP 516

---

## 5. Lessons from Other Languages

### Python 2 → 3: The Cautionary Tale

**What Happened**: Python 3.0 (2008) was intentionally backward incompatible. Removed features, changed semantics, reorganized standard library.

**Migration Challenges**:
- **12-Year Transition**: Python 2.7 supported until 2020
- **Ecosystem Split**: Many libraries maintained Python 2 and 3 branches
- **Tooling Required**: `2to3` automated converter, `six` compatibility library
- **Community Pain**: Large organizations delayed migration for years

**Key Breaking Changes**: `print` statement → function, Unicode strings vs bytes, integer division changes, removed builtins, dictionary method renames.

**Lessons for Java**:
1. **Flag Days Are Painful**: Coordinated breaking changes cause ecosystem disruption
2. **Tooling Is Critical**: Automated migration tools are essential but insufficient
3. **Timeline Matters**: 12 years is too long for a transition
4. **Binary Compatibility Matters**: Python's lack of binary compatibility made this easier than it would be for Java

**Sources**: Python 3.0 Release Notes, Python Porting Guide, PEP 3002

### C#: Language Versioning Without Editions

**C# Approach**: Language versions are tied to .NET runtime versions. `LangVersion` can be overridden in project files. No editions mechanism — each version is backward compatible.

**Versioning Strategy**: C# 13 requires .NET 9, C# 12 requires .NET 8, etc. Newer language features require newer runtime libraries.

**Breaking Changes**: C# has avoided breaking changes at the language level. Some breaking changes at the library level (e.g., .NET Core transition). No opt-in language modes for breaking changes.

**Lesson**: C# achieves language evolution through runtime coupling, careful feature design, and library-level changes rather than language-level breaking changes.

**Sources**: C# Language Versioning (learn.microsoft.com), C# Versioning

### Swift: Language Modes with ABI Stability

**Swift's Evolution**:
- Swift 2 → 3: Major breaking changes, painful migration
- Swift 3 → 4: Introduced language modes to allow gradual migration
- Swift 4 → 5: ABI stability achieved
- Swift 6: Concurrency checking enabled by default

**Swift 4 Language Modes**: Same compiler supports Swift 3 and Swift 4. Modules can be compiled with different language modes. Incremental adoption across the ecosystem.

**Key Difference from Rust**: Swift aimed for ABI stability (achieved in Swift 5). Language modes were a temporary bridge to stability. Once ABI stable, editions became less necessary.

**Lesson**: Language modes can be a bridge to ABI stability, but once stability is achieved, the need for editions diminishes.

**Sources**: Swift Evolution, Swift 6 Release, WWDC 2024

### Summary of Lessons

| Language | Approach | Success? | Key Lesson |
|----------|----------|----------|------------|
| Python 2→3 | Flag day breaking changes | Mixed (painful) | Avoid flag days; ensure tooling |
| Rust | Editions with interoperability | High success | Design for interoperability from start |
| C# | Runtime-coupled versioning | High success | Avoid language-level breaking changes |
| Swift | Temporary language modes | High success | Use modes as bridge to stability |
| C++ | Epochs proposed (not adopted) | N/A | Implementation complexity is high |

---

## 6. Concluding Assessment

### Is an Editions Mechanism Feasible for Java?

**Short Answer**: **Theoretically possible, but practically infeasible with current Java architecture and community values.**

### Barriers

**Technical Barriers** (High):
1. **Binary Compatibility**: Java's strict binary compatibility requirements conflict with editions that change method signatures or type systems
2. **JVM Specification**: Would require fundamental changes to the JVM spec, class file format, and verification logic
3. **Generics Erasure**: Reifying generics would break existing bytecode and require flag-day migration
4. **Tooling Ecosystem**: Massive coordinated update required across IDEs, build tools, and analysis tools
5. **Library Ecosystem**: Deep dependency graphs make cross-edition interoperability extremely complex

**Cultural Barriers** (High):
1. **No Community Demand**: Zero evidence of community discussion or demand for editions
2. **Compatibility Philosophy**: Java language architects explicitly prioritize backward compatibility
3. **Risk Aversion**: Enterprise Java users are highly conservative; breaking changes would face strong resistance
4. **Alternative Mechanisms**: Java already has preview features, deprecation, and source flags for controlled evolution

**Cost-Benefit Analysis** (Negative):
- **Cost**: Multi-year JVM specification effort, ecosystem-wide tooling updates, potential library ecosystem split
- **Benefit**: Ability to remove checked exceptions, reify generics, make other breaking changes
- **Verdict**: Costs vastly outweigh benefits given Java's existing compatibility strategies

### What Would an Edition Unlock?

**If editions were feasible**, they could enable:
1. **Removing Checked Exceptions**: Long-standing complaint, but transition path unclear
2. **Reified Generics**: Would improve performance and enable new patterns, but breaks binary compatibility
3. **Null-Safe Types**: JEP 8303099 proposes gradual nullness without editions
4. **Removing Raw Types**: Could improve type safety, but massive ecosystem impact
5. **Syntax Cleanup**: Remove rarely-used features, but marginal benefit

**However**, most of these are being addressed through other mechanisms:
- Null safety: JEP 8303099 (Null-Restricted and Nullable Types)
- Generics: Project Valhalla (value classes, specialized generics)
- Checked exceptions: No consensus on solution, but editions not proposed

### Recommended Alternatives

**Instead of editions**, Java should continue with:
1. **Preview Features**: Safe experimentation with opt-in (`--enable-preview`)
2. **Deprecation Process**: Gradual removal with long deprecation periods
3. **Project Amber**: Incremental language improvements
4. **Project Valhalla**: Value classes and specialized generics (with compatibility)
5. **Project Leyden**: AOT compilation and static images (without language editions)

### Path Forward

**If the Java community wanted to explore editions**:
1. **Start Small**: Propose limited editions for syntax-only changes (keyword reservations)
2. **Community Discussion**: OpenJDK mailing list discussion to gauge interest
3. **Prototype**: Experimental implementation in a fork (e.g., in Project Valhalla)
4. **JSR Process**: Formal specification through JCP
5. **Ecosystem Coordination**: Work with IDE vendors, build tool maintainers, library authors

**However**, given the lack of community demand and high barriers, this path is unlikely to be pursued.

### Final Verdict

**An editions mechanism for Java is not feasible in the foreseeable future** due to:

1. **Technical**: Would require breaking Java's core binary compatibility contract
2. **Cultural**: No community demand; compatibility is a core value
3. **Economic**: Costs outweigh benefits; alternatives exist
4. **Precedent**: Other languages' approaches don't map to Java's constraints

**Java's strength is its stability and backward compatibility**. While this creates constraints on language evolution, it is also a key reason for Java's success in enterprise environments. An editions mechanism would undermine this strength without providing commensurate benefits.

**Recommendation**: Continue with Java's existing compatibility strategies (preview features, deprecation, gradual evolution) rather than pursuing an editions mechanism.

---

## Sources

### C++ P1881
- P1881R1: open-std.org/jtc1/sc22/wg21/docs/papers/2020/p1881r1.html
- P1881R0: open-std.org/JTC1/SC22/WG21/docs/papers/2019/p1881r0.html
- GitHub Issue #631: github.com/cplusplus/papers/issues/631
- ISO C++ Status: isocpp.org/STD/STATUS

### Rust Editions
- Rust Edition Guide: doc.rust-lang.org/edition-guide/
- Rust 2024 Announcement: blog.rust-lang.org/2025/02/20/Rust-1.85.0/
- RFC 3085: rust-lang.github.io/rfcs/3085-edition-2021.html
- Compiler Dev Guide: rustc-dev-guide.rust-lang.org/guides/editions.html

### Java Community
- JEP 247: openjdk.org/jeps/247
- JEP 238: openjdk.org/jeps/238
- Project Amber: openjdk.org/projects/amber/
- Brian Goetz Presentation: infoq.com/presentations/lessons-java-evolution/
- lambda-dev mailing list: mail.openjdk.org/pipermail/lambda-dev/2012-November/006850.html
- Checked Exceptions Discussion: mail.openjdk.org/pipermail/jdk-dev/2019-October/003461.html

### Java Technical
- Project Valhalla: openjdk.org/projects/valhalla/design-notes/in-defense-of-erasure
- Project Leyden: openjdk.org/projects/leyden/
- JEP 8303099 (Null-Restricted Types)
- JEP 514 (AOT Ergonomics), JEP 516 (AOT Object Caching)

### Other Languages
- Python 3.0: docs.python.org/3/whatsnew/3.0.html
- PEP 3002: peps.python.org/pep-3002/
- C# Versioning: learn.microsoft.com/en-us/dotnet/csharp/language-reference/language-versioning
- Swift Evolution: github.com/swiftlang/swift-evolution

---

**Report Prepared**: 2026-08-20 (subagent research date Jan 2026)
**Research Method**: Web search, specification review, mailing list analysis
**Confidence Level**: High (comprehensive search across multiple sources)
**Note**: Originally produced by background subagent_explore (read-only); saved by parent agent.
