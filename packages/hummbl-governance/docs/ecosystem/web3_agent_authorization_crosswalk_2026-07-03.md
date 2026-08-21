# Web3 Agent Authorization Crosswalk Under Human Command

Status: candidate research crosswalk
Date: 2026-07-03
Scope: `hummbl-io/hummbl-governance#161`
Parent context: `hummbl-io/hummbl-governance#1199`

This document is source-audited prior art for Web3 agent authorization under
Human Command. It does not canonize Web3 vocabulary, make Ownward Web3-first,
approve a substrate, add a primitive, change CI, change runtime behavior,
publish a release, or promote any external project to HUMMBL canon.

## Human Command Boundary

Human Command means the human retains operational authority over delegation,
interruption, refusal, escalation, revocation, and redirection.

Use `sovereignty` only when all are true:

- bounded domain exists;
- external claimants exist;
- final human authority is at stake;
- refusal, revocation, redirection, and term-setting are supported.

Use `self-custody` only when cryptographic keys, wallets, user-held
credentials, or concrete auditable data or record control are in scope.
Do not use it as broad agency, flourishing, autonomy, or wellbeing language.

## Source Receipts

All source anchors below were retrieved on 2026-07-03. They are source
receipts, not endorsement or maturity proof.

| Lane | Source | Receipt URL | Bounded use |
|---|---|---|---|
| Agent identity / reputation | ERC-8004 draft | https://eips.ethereum.org/EIPS/eip-8004 | Candidate agent identity, reputation, and validation registries. The EIP is draft status, so do not treat it as settled standard. |
| Agent identity / services | Olas stack docs | https://stack.olas.network/ | Prior art for agent/service packaging and deployment flows. |
| Human-in-loop authorization | WaaP for Agents | https://docs.waap.human.tech/for-agents | Prior art for two-party signing, limits, and human approval over agent wallet actions. |
| Human-in-loop authorization | Newton Protocol docs | https://docs.newton.xyz/developers/overview/about | Prior art for policy engines around onchain transaction authorization. |
| Agent onchain actions | Coinbase AgentKit docs | https://docs.cdp.coinbase.com/agent-kit/welcome | Prior art for agent wallet management and onchain action providers. |
| Wallet authentication | EIP-4361 SIWE | https://eips.ethereum.org/EIPS/eip-4361 | Prior art for scoped signed-message authentication, nonce, and session semantics. |
| Roles / multisig | Safe | https://safe.global/ | Prior art for multisig and smart-account control surfaces. |
| Roles / permissions | Hats Protocol docs | https://docs.hatsprotocol.xyz/ | Prior art for programmable onchain roles and permissions. |
| Governance voting | Snapshot docs | https://docs.snapshot.box/ | Prior art for offchain voting spaces, proposals, strategies, and vote calculation. |
| Governance execution | Aragon docs | https://docs.aragon.org/ | Prior art for DAO plugins, permissions, proposals, and governance UI/tooling. |
| Governance staking | Tally docs | https://docs.tally.xyz/ | Prior art for governance and staking surfaces around protocol participation. |
| Verifiable credentials | W3C VCDM 2.0 | https://www.w3.org/TR/vc-data-model-2.0/ | Standards anchor for issuer-holder-verifier credential claims. |
| Decentralized identifiers | W3C DID 1.1 | https://www.w3.org/TR/did-1.1/ | Standards anchor for decentralized identifier terminology. |
| Credential trust registries | cheqd docs | https://docs.cheqd.io/product/studio/trust-registries/dtc/referencing-in-credential | Prior art for linking credentials to trusted issuer registries. |
| Credential tooling | walt.id docs | https://docs.walt.id/concepts/digital-credentials/verifiable-credentials-w3c | Prior art for VC implementation and wallet/tooling language. |
| Name resolution | ENS docs | https://docs.ens.domains/ | Prior art for names, resolvers, records, and ownership boundaries. |
| Wallet login | SpruceID / SIWE | https://blog.spruceid.com/sign-in-with-ethereum/ | Prior art for wallet-based account authentication patterns. |
| Social reputation | Farcaster protocol repo | https://github.com/farcasterxyz/protocol | Prior art for decentralized social identity and protocol-level reputation signals. |
| Social graph | Lens docs | https://lens.xyz/docs/protocol | Prior art for accounts, usernames, graphs, groups, feeds, apps, rules, actions, and sponsorships. |
| Decentralized AI substrate | Ritual docs | https://docs.ritualfoundation.org/ | Prior art for autonomous-agent substrate claims; treat sovereignty language as external and unadopted. |
| Decentralized AI substrate | Bittensor docs | https://docs.learnbittensor.org/ | Prior art for subnet, miner, validator, incentive, and digital-commodity language. |
| Decentralized compute | Akash docs | https://akash.network/docs/ | Prior art for decentralized compute marketplace and deployment surfaces. |
| Decentralized AI alliance | ASI Alliance | https://superintelligence.io/ | Prior art for ecosystem/market positioning; do not treat as authorization primitive proof. |

## Primitive Crosswalk

| Web3 primitive | HUMMBL analogue | Ownward relevance | Primary risks | Maturity |
|---|---|---|---|---|
| ERC-8004 agent identity registry | `IdentityEngine`, agent identity registry, receipt-bound service descriptors | Could inform portable agent identity receipts and endpoint/domain verification. | Draft status, Sybil exposure, reputation gaming, endpoint spoofing, transferable ownership confusion. | useful-but-immature |
| ERC-8004 reputation registry | Receipt engine plus external feedback ledger | Could inform machine-readable feedback receipts if reviewer identity and Sybil controls are explicit. | Onchain feedback is not trust; client-address filtering can still be gamed; offchain aggregators become hidden authority. | speculative |
| ERC-8004 validation registry | Receipt engine, contestability, independent validation receipt | Useful as a pattern for recording validation requests and responses. | Validation quality depends on validator selection, stake model, proof class, and replayable evidence. | speculative |
| Olas service/agent packaging | Lifecycle, delegation context, service manifest | Could inform deployment metadata for governed agent services. | Autonomous economic-agent framing may exceed Human Command unless bounded by delegation, revocation, and receipts. | useful-but-immature |
| WaaP two-party signing and limits | Delegation token caveats, approval-required caveat, kill-switch hold mode | Strong prior art for agent wallet actions that cannot sign alone and escalate high-risk actions. | Telegram or external approval UX can become the control plane; limits must be inspectable, revocable, and logged. | useful-but-immature |
| Newton policy authorization | Capability fence, policy gate, authority engine | Good conceptual match for transaction policies, spend limits, compliance checks, and pre-execution gating. | Policy author, policy freshness, oracle dependence, sanctions/compliance claims, and failure modes need separate review. | useful-but-immature |
| Coinbase AgentKit wallet/action providers | Tool registry, capability fence, delegation token `ops_allowed` | Useful inventory of onchain action provider patterns for scoped tool grants. | Giving an agent a wallet is not Human Command; action providers need least privilege, approval gates, and audit receipts. | production-ready for tooling, not sufficient alone |
| EIP-4361 Sign-In with Ethereum | Identity proof, scoped signed session, nonce-based login | Useful for wallet authentication and session scope language. | Wallet control is not personhood, consent, authority, or durable agent authorization by itself. | production-ready pattern |
| Safe multisig / smart account | Non-author review, multi-party approval, break-glass authority | Strong role-control pattern for treasury or irreversible onchain actions. | Signer key compromise, signer collusion, slow emergency response, false sense that multisig equals governance quality. | production-ready pattern |
| Hats roles / permissions | Role registry, delegation chain, revocation ledger | Useful for role-bearing permissions and revocable authority assignments. | Tokenized roles are not competence; role state must map to current human approval and org policy. | useful-but-immature |
| Snapshot voting | Review signal, advisory vote, community sentiment receipt | Useful as non-binding input to governance review. | Offchain votes can be non-executing, token-weighted, captured, or misread as operator approval. | production-ready for voting, not authority |
| Aragon DAO permissions/plugins | Governance process, proposal execution, permissioned plugin architecture | Useful reference for permission-scoped execution and proposal lifecycle. | DAO governance does not replace OWNER authority or HUMMBL non-author review. | production-ready pattern |
| Tally / Cactus governance | Proposal dashboard, staking/reward participation, vote visibility | Useful for public governance tracking patterns. | Token staking and voting incentives can distort authority, competence, or Human Command. | production-ready pattern |
| W3C VCs / DIDs | Credential evidence, identity proof, issuer-holder-verifier record | Useful for auditable credentials when issuer authority and revocation are verifiable. | VC/DID validity does not prove the holder should be trusted for the requested action. Privacy and correlation risks remain. | production-ready standards |
| cheqd / walt.id / SpruceID | Credential tooling and wallet-auth implementation prior art | Useful implementation references for credential presentation, trust registries, and SIWE flows. | Vendor/tool maturity varies; trust registry governance is the hard problem, not the proof envelope. | useful-but-immature |
| ENS names / resolver records | Human-readable identity alias, endpoint discovery, metadata pointer | Useful for discovery and public labels when ownership and resolver state are verified. | ENS name ownership is not identity, consent, competence, or current authority. | production-ready pattern |
| Farcaster / Lens social reputation | Public graph/reputation signal | Useful only as weak supplemental evidence for public identity or history. | Social reputation is Sybil-prone, context-dependent, gameable, and not authorization. | useful-but-immature |
| Ritual / Bittensor / Akash / ASI substrate claims | Compute/service discovery, model/service market, external execution substrate | Possible future substrate watchlist for compute, incentives, and agent service discovery. | External autonomy and incentive language can conflict with Human Command; compute availability is not authorization. | speculative to useful-but-immature by use case |

## Candidate Admission Rules

Before any Web3 primitive is admitted as a governed substrate candidate, record:

1. requested primitive or substrate name;
2. exact source receipts and retrieval dates;
3. maturity classification with evidence;
4. human authority owner and revocation path;
5. action scope, spend scope, data scope, and time scope;
6. approval thresholds for routine, high-risk, irreversible, or regulated actions;
7. denial/refusal/interruption behavior;
8. receipt format for authorization, execution, failure, and revocation;
9. key custody and recovery model;
10. privacy, correlation, and right-to-delete implications;
11. Sybil and reputation-abuse assumptions;
12. regulatory, sanctions, financial, tax, consumer, and UX risk notes;
13. rollback or containment plan;
14. reviewer decision: reject, hold, candidate, or promote for governance review.

## Maturity Classifications

Use these labels only inside this advisory crosswalk:

- `production-ready pattern`: externally deployed pattern with mature docs, but
  still not sufficient for HUMMBL adoption without local gates.
- `useful-but-immature`: promising prior art, incomplete standardization,
  immature operations, or unresolved governance/security assumptions.
- `speculative`: interesting but not ready to influence design except as
  watchlist or research.
- `irrelevant`: no meaningful relation to Human Command authorization.
- `avoid`: conflicts with Human Command or materially increases risk without
  compensating evidence.

## Do Not Infer

- Web3 authorization primitives are sufficient for HUMMBL or Ownward.
- Onchain identity equals human trust.
- Agent reputation is Sybil-resistant by default.
- Wallet control equals Human Command.
- Token incentives are required.
- DAO voting equals operator approval.
- Social graph reputation is authorization.
- Self-custody should be generalized beyond keys, credentials, or concrete
  auditable records.
- External `sovereign agent` language is HUMMBL sovereignty doctrine.

## Security, Regulatory, And UX Risk Notes

- Wallets and keys create irreversible-action risk; require spend limits,
  approval thresholds, emergency revocation, and signed receipts.
- Credentials create privacy and correlation risk; minimize disclosed claims
  and avoid writing sensitive personal data to public or immutable ledgers.
- Reputation systems require explicit Sybil assumptions and reviewer-source
  weighting; raw wallet feedback must remain weak evidence.
- Policy engines require policy provenance, policy freshness, failure behavior,
  and dispute paths.
- Governance voting and token staking can produce incentives that conflict with
  human authority, competence, and safety.
- Any regulated financial, medical, defense-adjacent, identity, employment,
  insurance, credit, sanctions, tax, or consumer-protection use requires human
  expert review before agent execution.
- User experience must show what the agent can do, what the human approved,
  what can be revoked, what cannot be undone, and where receipts are stored.

## Recommendation

Do not make Ownward Web3-first.

Admit no external Web3 primitive directly into HUMMBL canon from this pass.
The strongest candidate patterns for future governed substrate review are:

1. SIWE-style scoped session signing for wallet authentication, bounded to
   authentication only.
2. Safe-style multi-approval for irreversible onchain actions.
3. WaaP/Newton-style policy and two-party signing patterns for wallet actions,
   if limits, revocation, and receipts are locally inspectable.
4. VC/DID-style credential evidence, if issuer authority, revocation, selective
   disclosure, and privacy controls are governed locally.
5. ERC-8004-style agent identity and validation registries as a watchlist,
   not an adopted standard, while the EIP remains draft.

Every candidate must remain subordinate to Human Command: explicit authority,
least privilege, revocation, escalation, refusal, receipts, and human review
for high-consequence execution.

## Next Gate

Review this advisory crosswalk against `hummbl-governance#161` and the
downstream relationship to `#162`. Any schema, fixture, runtime, CI, release,
public claim, canon, integration, vendor, wallet, or substrate adoption requires
a separate human-approved PR.
