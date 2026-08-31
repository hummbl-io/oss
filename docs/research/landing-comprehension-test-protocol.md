# hummbl.io landing-page comprehension protocol

Status: **UNRUN — no participant results are claimed.**

This protocol measures GAP-002 (cold-visitor comprehension) on the [landing claims ledger](https://hummbl.io/manifest/landing-claims.json); it does not itself close that gap.

## Decision question

After only the first screen and then a short unrestricted scan of the page, can a cold visitor accurately explain what HUMMBL does, why agentic systems need it, what the package guarantees, what supports those claims, where assurance ends, and what to do next?

## Participants

Recruit five real people who have not reviewed or worked on this landing page. Aim for this role mix:

- two software or AI builders;
- one security, risk, or compliance practitioner;
- one organizational technology buyer or leader;
- one technically literate generalist.

Do not substitute synthetic personas, agents, or the patch author for participants. Record only an anonymous participant ID and broad role; do not collect names, contact details, employer, or other unnecessary personal data.

Use these exact role labels in the receipt: `builder` (two participants), `security-risk-compliance`, `technology-buyer`, and `technical-generalist`.

## Recruitment script

> We are testing whether the hummbl.io landing page explains itself; we are not testing you. The session takes about five minutes. We will record only an anonymous ID, a broad role, your answers, and scores. Please do not provide your name, employer, contact information, or confidential information. Your participation is voluntary, and you may stop at any time.

Confirm verbal consent before showing the page. Do not record audio or video under this protocol.

## Procedure

1. Record the exact tested URL (`https://hummbl.io/`), 40-character deployed commit SHA, UTC start time, and viewport. Use 1440×900 unless an accessibility need requires another viewport; record any deviation as a limitation.
2. Show the participant the first viewport for 20 seconds. Do not explain HUMMBL or define any term on the page.
3. Hide the page. Ask questions 1–3 below and record the participant's words without coaching.
4. Allow up to three minutes to inspect the whole page.
5. Hide the page again. Ask questions 4–6 and the confidence question.
6. Record whether the participant identified a sensible next action and whether any answer made a material assurance overclaim.
7. Score the response using the rubric before discussing the intended answers. Do not revise scores after revealing the anchors.

Questions:

1. What does HUMMBL do?
2. Why would an agentic system need it?
3. What action would you take next if it were relevant to you?
4. What does HUMMBL actually guarantee or make checkable?
5. What evidence supports the page's main technical claims?
6. Where does HUMMBL's assurance boundary end?
7. How confident are you in your explanation, from 1 to 5?

## Scoring rubric

Score each of the six substantive questions from 0 to 2.

- **2 — accurate:** captures the bounded intended meaning without a material overclaim.
- **1 — partial:** directionally correct but misses a key element or boundary.
- **0 — incorrect/absent:** cannot answer, gives an unrelated answer, or materially overstates assurance.

Predefine these answer anchors. A score of 2 tests comprehension of the page, not recall of ledger trivia (exact CI run IDs, job IDs, or skipped-test counts are not required).

| Dimension | A score of 2 includes |
| --------- | --------------------- |
| What      | Open-source runtime governance primitives for controlling agent authority and producing checkable evidence |
| Why       | Policies and documents are not on the execution path; authority, containment, and evidence must be |
| Next      | A role-appropriate action such as inspect source, install the package, or request a governance review |
| Guarantee | In-process mediation when integrated; HMAC integrity and authenticity inside a shared-secret trust domain (not public-key non-repudiation) |
| Evidence  | Claims ledger, public repository CI, and the executable example |
| Boundary  | Alpha maturity; repository CI is not production use; HMAC is shared-secret not public-key; no conferred legal compliance or certification |

## Acceptance threshold

The page passes this protocol only when:

- at least four of five participants score 9 or higher out of 12;
- every participant scores at least 1 on assurance boundary;
- no participant interprets Alpha, repository CI, HMAC, or framework mappings as production certification, a production-use receipt, public non-repudiation, or legal compliance;
- at least four participants identify a sensible next action.

If the page fails, preserve the anonymized raw responses, identify the repeated misunderstanding, make the smallest copy or information-architecture correction, and rerun with five new cold participants.

## Result handling

Copy `docs/research/landing-comprehension-receipt-template.json` to a SHA-scoped working receipt only when a real session begins. Keep raw responses internal until a privacy and publication review is complete. Do not commit names, employers, contact details, recordings, or other identifying data.

For each participant, add an object with anonymous `id`, the exact `role` label, six integer `scores` (`what`, `why`, `next`, `guarantee`, `evidence`, and `boundary`), integer `confidence`, booleans `sensible_next_action` and `material_overclaim_detected`, and verbatim-but-anonymous `responses` `q1` through `q6`. The validator reports every missing or invalid field. A completed receipt uses a non-`UNRUN` status (for example, `COMPLETE`).

Validate the receipt before interpreting it:

```text
python tools/scripts/validate_landing_comprehension_receipt.py docs/research/landing-comprehension-receipt-template.json
python tools/scripts/validate_landing_comprehension_receipt.py path/to/receipt.json
python tools/scripts/test_validate_landing_comprehension_receipt.py
```

The validator recomputes all aggregate fields and `threshold_met` from the five participant records and does not trust client-supplied aggregates. A repository template with `status: "UNRUN"` and empty `participants` is valid preparation, not a comprehension result (`threshold_met` is false).
