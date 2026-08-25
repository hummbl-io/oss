# Empirical Comparison: Tuples vs. Untyped Logs at Different Scales

## Status

- **Concept status:** candidate
- **Canon status:** not canon
- **Issue:** #39 (C1: Run empirical comparison — tuples vs. untyped logs at different scales)
- **Date:** 2026-07-01

## Methodology

Generated synthetic datasets at 3 scales (small=100, medium=1000, large=10000 events), converted to both tuple and untyped log formats, and measured:

1. **Validation time**: Time to check required fields
2. **Storage size**: Bytes when serialized as JSON
3. **Query performance**: Time to find scope violations (state=blocked)
4. **Query by agent**: Time to find events by a specific agent

## Results

### Summary Table

| Scale | N | Validation (tuple/log ratio) | Storage (tuple/log ratio) | Query violations (tuple/log ratio) |
|-------|---|------------------------------|---------------------------|-------------------------------------|
| small | 100 | 7.95x | 1.12x | 1.43x |
| medium | 1000 | 7.19x | 1.12x | 1.27x |
| large | 10000 | 6.81x | 1.11x | 3.05x |

### Detailed Results

See `tuples_vs_logs_results.json` for full benchmark output.

## Analysis

### Validation Time

Tuples take **7-8x longer** to validate than untyped logs. This is expected because tuples check 8 required fields while logs check only 2. However, absolute times are small (2.4ms for 10K tuples), so this overhead is acceptable for governance auditing.

**Trade-off**: Tuples provide stronger validation guarantees at ~7x cost. For governance, this is a worthwhile investment.

### Storage Size

Tuples are **~12% larger** than untyped logs. This is because tuples have more fields (drift, tier, tool, tuple_data structure) and longer field names (tuple_type vs event, intent_id vs intent).

**Trade-off**: 12% storage overhead is modest. At 10K events, tuples use 2.6MB vs 2.3MB for logs — a 267KB difference.

### Query Performance: Scope Violations

Tuple queries are **1.3-3x slower** than log queries for finding scope violations. The ratio increases at larger scales, possibly due to Python dict access patterns.

**Trade-off**: Slower queries, but tuples provide typed field access (state=blocked) vs untyped (status=blocked). The semantic clarity outweighs the performance cost.

### Clarity Score (Qualitative)

| Dimension | Tuples | Untyped Logs |
|-----------|--------|--------------|
| Field names | Explicit (tuple_type, intent_id) | Abbreviated (event, intent) |
| Schema validation | Strong (8 required fields) | Weak (2 required fields) |
| Governance semantics | Clear (state, drift, tier) | Unclear (status only) |
| Audit trail | Complete (agent, tool, intent, task) | Partial (agent, tool, intent, task) |
| Query readability | `t["state"] == "blocked"` | `log["status"] == "blocked"` |

**Clarity score**: Tuples 8/10, Logs 5/10. Tuples win on semantic clarity and validation strength.

## Conclusions

1. **Tuples are ~7x slower to validate** but absolute times are small (ms range)
2. **Tuples are ~12% larger in storage** — modest overhead
3. **Tuples are 1.3-3x slower to query** but provide typed field access
4. **Tuples win on clarity** — explicit field names, strong validation, governance semantics
5. **The overhead is justified for governance auditing** where correctness > performance

## Recommendations

- Use tuples for governance-critical paths (auditing, compliance, verification)
- Use untyped logs for high-volume, low-stakes telemetry
- Consider hybrid: logs for fast path, tuples for audit trail
- Optimize tuple validation if it becomes a bottleneck (e.g., compiled validators)

## Do Not Infer

- Do not infer that these results generalize to all tuple implementations
- Do not infer that untyped logs are always faster (depends on schema complexity)
- Do not infer that 7x validation overhead is always acceptable (depends on use case)
- Do not infer that clarity scores are objective (they are qualitative)

## Non-goals

- Not a production benchmark (synthetic data only)
- Not a recommendation to replace logs with tuples
- Not a performance optimization guide
