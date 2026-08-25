# Node Onboarding: Dan's MacBook Pro (Big Dog)

**Role:** Tier 2.5 High-Logic Edge Node
**Status:** PROPOSED
**Hardware:** Apple Silicon (M3/M4 Max anticipated)

## Integration Plan

1. **Mesh Connectivity:**
   - [ ] Establish Tailscale presence.
   - [ ] Configure SSH key auth from Desktop and NodeZero.
   - [ ] Add `big-dog` alias to mesh `.ssh/config`.

2. **ML Stack Upgrade:**
   - [ ] Install PyTorch with MPS (Metal) support.
   - [ ] Provision Ollama for 70B parameter models (Llama 3.3).
   - [ ] Deploy HUMMBL Reasoning Oracle (Tier 3 Monitoring).

3. **Governance Link:**
   - [ ] Initialize local `hummbl-tuples` repository.
   - [ ] Connect to the Coordination Bus (`messages.tsv`).
   - [ ] Enable automated `ATTEST` oracle for Tier 1 breakthroughs.

## Metadata
- **Assigned Intent:** `node-onboarding-20260327`
- **Verifier:** `gemini-cli-researcher`
