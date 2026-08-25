# BIF on Mobile — Use Cases for Claude Code + Sonnet 4.6

Patterns for running BIF sessions from the Claude mobile app via Claude Code. Mobile changes the context, not the methodology: the four phases and 15-batch structure stay constant; what changes is *when* you reach for BIF and *what triggers a session*. The entries below are organized by how well mobile enables each pattern.

---

## Tier 1 — Mobile-Native Wins

These use cases only work — or work best — when you're away from a desk. The window is short, the trigger is external, and a desktop session would be too late.

**Capture-and-Classify on Encounter.** You encounter a new tool, API, or framework at a conference, in a Slack thread, or in an article. Open Claude Code, describe what you found, and Sonnet classifies it against BIF's four domain templates, drafts a source inventory (llms.txt → docs → API ref → blog → repo), and creates a PRD stub for a future ingestion session. The capture is ephemeral — waiting until you're back at a desk loses the context.
_Batch flex:_ Output is a PRD stub only; actual ingestion happens later. Use the PRD Template from FRAMEWORK.md Part 2 as the scaffold.

**Delta Document on Breaking News.** A major version drops — a new model release, a framework version, a breaking API change. You're reading the announcement on your phone. Paste the changelog or release notes into Claude Code and Sonnet formats it as a Batch 4 Delta Document: New / Changed / Deprecated / Unchanged — matching the `examples/anthropic/04_Delta_Document.md` schema. The news is freshest right now; formatting it later loses nuance.
_Batch flex:_ Scope is Batch 4 only. Reference the Version Diff Protocol in FRAMEWORK.md Part 4B. Cross-reference against your existing Batch 1 knowledge file if one exists.

**Competitive Intelligence Capture.** During a vendor demo, sales call, or product deep-dive, you observe things that won't be in any public doc. Describe what you saw and Sonnet structures it as a SaaS Evaluation Batch 10 (Competitive Analysis / Decision Document): capabilities, pricing signals, positioning gaps, migration friction. Voice input works well here.
_Batch flex:_ Use `templates/saas-evaluation.md` as the base. Treat the observed session notes as Batch 10 source material; plan a full four-phase BIF run for later if the vendor warrants it.

**Photo-to-Source Inventory.** Photograph a whiteboard, conference slide, or product screen. Sonnet extracts all tool and platform names, cross-references them against your existing BIF sessions (`bif status`), and flags which have no ingestion started. Camera and vision input are mobile-native; this workflow has no desktop equivalent.
_Batch flex:_ Output feeds the Pre-Ingestion Checklist (FRAMEWORK.md Part 3). Names with no existing session become candidates for new `bif start` commands.

**Certification Flashcard Session.** Commuting or in a waiting room — ask Sonnet to generate spaced-repetition Q&A from any completed batch file. "Quiz me on Claude's model catalog and pricing tiers" draws from `examples/anthropic/01_Claude_API_Core_Reference.md`. "Test my understanding of Phase 2 hardening patterns" draws from a Batch 6 file. Idle commute time is the right cadence for this; a desktop session adds no value.
_Batch flex:_ Follow the Certification Adaptation checklist in FRAMEWORK.md Part 3. Weight questions toward the exam domain weightings noted in your Phase 1 batch plan.

---

## Tier 2 — Workflow Continuation Away from Desk

These use cases can run on desktop too, but mobile removes the friction of needing to be at a workstation to keep a session moving.

**Session Status Dashboard.** Quick check on all in-flight ingestion projects: which batches are complete, which are blocked, what's queued next. Run `bif status` via Claude Code, ask Sonnet to summarize progress across all open sessions, and decide whether to push a batch forward or flag a blocker for the next desktop session.
_Batch flex:_ No batch changes needed. Maps directly to `tool_bif_session_status()` in `mcp_server.py` and the `bif status` CLI subcommand.

**Batch Validation on the Go.** Have a draft knowledge file or a pasted excerpt? Run it through the six-point quality checklist: metadata header, structured headers, code blocks, currency check, site map, token budget. Sonnet flags gaps using the same logic as `tool_bif_validate_batch()`. Good for reviewing a collaborator's batch output before a desktop merge.
_Batch flex:_ Quality checklist is in FRAMEWORK.md Part 3. Token budget target is ≤50K tokens per file; see FRAMEWORK.md Part 4B for split strategies.

**New Template Drafting.** Encounter a domain not covered by the four existing templates — blockchain, design systems, hardware/firmware, compliance frameworks? Describe the domain and its key concerns; Sonnet adapts the closest existing template (usually `templates/ai-ml-platform.md` or `templates/saas-evaluation.md`) and proposes a 10-batch plan with domain-specific batch names. The draft goes into `templates/` on the next desktop session.
_Batch flex:_ Follow the pattern from existing templates: one table, 10 rows, batch number + name + purpose. Cross-check against the use case notes in `USE_CASES.md`.

**USE_CASES.md Contribution.** Discover a new persona, domain, or goal pattern in the field — "M&A diligence on a startup's tech stack", "incident post-mortem for a vendor outage", "partner certification audit". Describe it; Sonnet formats it to match the USE_CASES.md style (bold title, one-sentence description, italicized batch flex note) and commits the draft to the repo branch from mobile.
_Batch flex:_ Match the existing section structure: By Persona, By Domain, or By Goal/Outcome. Entries should be short; depth belongs in FRAMEWORK.md.

**Batch Planning for a New Domain.** You have a concrete deadline and a new domain to learn: "I need to understand Temporal.io for a client engagement starting in three weeks." Describe the domain, goal, and timeline; Sonnet maps phases to your timeline, recommends which batches to front-load, and drafts a source priority list. Output is a ready-to-use PRD matching the template in FRAMEWORK.md Part 2.
_Batch flex:_ Short timelines compress Phase 4; narrow goals (one exam domain, one integration) compress Phase 3. Use `bif start` with the resulting PRD to create the session.

---

## Tier 3 — Team and Collaboration

These use cases benefit from mobile primarily because the trigger is a meeting, a call, or a handoff — contexts where you're not at a desk.

**Onboarding Knowledge Package.** A new team member joins a project with an already-ingested stack. Pull the relevant batch outputs from `examples/` and ask Sonnet to curate a tailored starter pack: Batch 1 (what it is), Batch 3 (how to use the tooling), Batch 5 (best practices). Add a guided reading plan with role-specific questions. Best triggered at the start of an onboarding conversation, not after.
_Batch flex:_ Selection depends on the new member's role. Ops/SRE leans toward Batches 3 and 6; developer leans toward Batches 1 and 5; architect leans toward Batches 2 and 9. See FRAMEWORK.md Section 5.2 for the team scaling model.

**RFP / Vendor Evaluation Memo.** A client asks for a tool comparison mid-call. Feed Sonnet a description of two or three options; it generates a structured evaluation memo in Batch 10 Decision Document format: capability matrix, pricing signals, migration friction, go/no-go with rationale. Use `templates/saas-evaluation.md` as the skeleton.
_Batch flex:_ When you have time for a real ingestion run, use the "double-run" pattern from USE_CASES.md (Phases 1–2 once per product, then a side-by-side comparison batch).

**KRINEIA Governance Logging.** A batch is complete and needs a receipt entry in `_receipts/krineia/primary.jsonl`. Sonnet generates a properly-formatted KRINEIA JSON receipt (operator: append) to add to the chain. Enforces the KRINEIA constraint set: append only, no rewrite/delete/summarize_and_replace. Good to do immediately after completing a batch rather than batching up receipts for later.
_Batch flex:_ No batch changes. Reference `KRINEIA.md` for the manifest format and permitted operators.

---

## Tier 4 — Framework Evolution

Minor but persistent tasks that benefit from mobile because they arise while reading or reviewing, not while actively working.

**FRAMEWORK.md Micro-Edits.** Small clarifications, typo fixes, or hardening protocol improvements noticed while reading the canonical doc on mobile. Quick edit via Claude Code, Conventional Commits format (`docs(framework): clarify token budget split threshold`), committed to the branch from mobile.
_Batch flex:_ No batch changes. Follow the contribution conventions in `CONTRIBUTING.md`: `type/agent/short-desc` branch names, small diffs, Conventional Commits.

**CPN Course Completion Tracking.** After completing a Claude Partner Network course, update `examples/anthropic/CPN_COURSE_COMPLETION_MAP.md` with badge evidence (LinkedIn badge, screenshot, certificate, or dated note). Sonnet routes the course to the correct batch file and drafts the delta note. Best done immediately after badge receipt rather than queued up.
_Batch flex:_ The routing table is already in `CPN_COURSE_COMPLETION_MAP.md`: Claude API courses → Batch 01, MCP → pending, SDK/Code → pending, Safety → Delta document.

---

## Ranking by Impact × Mobile Fit

Ordered by how well mobile's unique affordances (camera, voice, idle time, ephemeral moments) serve each use case:

| Rank | Use Case | Core reason it wins on mobile |
|------|----------|-------------------------------|
| 1 | Capture-and-Classify on Encounter | Ephemeral moment — delay kills context |
| 2 | Delta Document on Breaking News | News breaks on phone; act at peak freshness |
| 3 | Photo-to-Source Inventory | Camera + vision is mobile-only |
| 4 | Certification Flashcard Session | Commute time = study time |
| 5 | Competitive Intelligence Capture | During demos and calls, not at a desk |
| 6 | Batch Planning for New Domain | Triggered by a conversation or meeting |
| 7 | RFP / Vendor Evaluation Memo | Client asks mid-call; timing matters |
| 8 | Session Status Dashboard | Quick check fits a 2-minute mobile moment |
| 9 | KRINEIA Governance Logging | Do it immediately after batch completion |
| 10 | USE_CASES.md Contribution | Field observations don't wait for a desk |
| 11 | Batch Validation on the Go | Review a draft while away from office |
| 12 | New Template Drafting | Capture domain ideas while still fresh |
| 13 | Onboarding Knowledge Package | Share reading plan during team onboarding call |
| 14 | FRAMEWORK.md Micro-Edits | Typo fixes encountered while reading |
| 15 | CPN Course Completion Tracking | Document completion immediately after badge |

---

## Cross-Cutting Notes

**Voice input.** Competitive intelligence capture, batch planning, and RFP memo generation all work well with voice-dictated descriptions. Sonnet handles the structuring; you supply the raw observations.

**Paste-in workflows.** Delta documents, batch validation, and flashcard sessions work by pasting source material (changelogs, knowledge file excerpts, doc pages) directly into the Claude Code prompt. Mobile share-sheet integrations can streamline this workflow.

**Commit from mobile.** For use cases that produce file-level changes (USE_CASES.md contribution, FRAMEWORK.md edit, CPN tracking, new template draft), Claude Code supports committing and pushing to a feature branch from the mobile session when the branch is pre-configured.

**When not to use mobile.** Large multi-batch ingestion runs involving numerous web fetches, file consolidations, and cross-document merges are better suited to a desktop environment. Mobile works best for capture, validation, status checks, and lightweight continuation tasks rather than comprehensive BIF project completion.
