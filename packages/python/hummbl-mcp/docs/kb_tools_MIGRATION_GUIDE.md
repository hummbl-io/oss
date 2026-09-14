# Migration Guide: Integrating Knowledge Base into Existing Agents

This guide shows how to add standardized memory and context management to your existing agents.

## Quick Start (5 minutes)

### 1. Install Dependencies

No external dependencies required - uses Python stdlib only.

```bash
# Just ensure kb_tools.py is accessible
export PYTHONPATH="${PYTHONPATH}:${HOME}/.knowledge"
```

### 2. Basic Integration

```python
from kb_tools import MemoryStore, ContextManager

class YourAgent:
    def __init__(self, name: str):
        self.memory = MemoryStore(name)
        self.context = ContextManager(name, model="sonnet-4.5", limit=200000)

    def do_work(self):
        # Add observations
        self.memory.add(
            type="observation",
            content="Something important happened",
            tags=["important"],
            importance=0.8
        )

        # Track token usage
        self.context.track_usage(tokens_used=50000)

        # Query past memories
        related = self.memory.query(tags=["important"], min_importance=0.7)
```

### 3. Run Example

```bash
cd ~/.knowledge
python3 example_integration.py
```

## Detailed Integration Patterns

### Pattern 1: Add Memory to Existing Agent

**Before:**
```python
class CostOptimizer:
    def analyze(self):
        result = self._run_analysis()
        print(f"Analysis: {result}")
        return result
```

**After:**
```python
from kb_tools import MemoryStore

class CostOptimizer:
    def __init__(self):
        self.memory = MemoryStore("cost-optimizer")

    def analyze(self):
        result = self._run_analysis()

        # Record the analysis
        self.memory.add(
            type="observation",
            content=f"Cost analysis: {result}",
            tags=["cost", "analysis"],
            importance=0.7
        )

        return result
```

### Pattern 2: Context Window Management

```python
from kb_tools import ContextManager

class KnowledgeCurator:
    def __init__(self):
        self.ctx = ContextManager("knowledge-curator", limit=200000)

    def process_batch(self, items):
        for i, item in enumerate(items):
            # Track usage
            tokens_used = self._estimate_tokens(item)
            self.ctx.track_usage(tokens_used)

            # Check if compression needed
            if self.ctx.should_compress(threshold=0.8):
                self._compress_context()

            self._process(item)
```

### Pattern 3: Task Tracking

```python
class IncidentCommander:
    def __init__(self):
        self.memory = MemoryStore("incident-commander")
        self.ctx = ContextManager("incident-commander")

    def handle_incident(self, incident_id: str):
        # Start tracking
        self.ctx.add_task(incident_id)

        # Do work...
        self.memory.add(
            type="decision",
            content=f"Initiated incident response",
            tags=["incident", "critical"],
            importance=0.9,
            context={"incident_id": incident_id}
        )

        # Complete
        self.ctx.remove_task(incident_id)
```

### Pattern 4: Query Historical Context

```python
# Before making a decision, check what worked before
past_successes = self.memory.query(
    type="success",
    tags=["deployment"],
    min_importance=0.7,
    limit=10
)

# Learn from past errors
past_errors = self.memory.query(
    type="error",
    tags=["api"],
    min_importance=0.5
)
```

## CLI Usage

### Query Memories

```bash
python3 ~/.knowledge/kb_tools.py query cost-optimizer \
  --tags cost,alert \
  --min-importance 0.7
```

### Add Memory

```bash
python3 ~/.knowledge/kb_tools.py add cost-optimizer \
  "Budget exceeded by 20%" \
  --type observation \
  --tags cost,budget,alert \
  --importance 0.9
```

### Garbage Collection

```bash
# Dry run (preview)
python3 ~/.knowledge/kb_tools.py gc cost-optimizer --dry-run

# Actually remove expired
python3 ~/.knowledge/kb_tools.py gc cost-optimizer
```

### Check Status

```bash
python3 ~/.knowledge/kb_tools.py status cost-optimizer
```

## Schema Validation (Optional)

If you want to validate memory entries against the schema:

```python
import json
import jsonschema

# Load schema
with open("~/.knowledge/schemas/memory-v1.schema.json") as f:
    schema = json.load(f)

# Validate entry
entry = {...}
jsonschema.validate(entry, schema)  # Raises if invalid
```

## Best Practices

### 1. Tag Consistently

Use lowercase, hyphenated tags:
- ✅ `cost`, `api-error`, `high-priority`
- ❌ `Cost`, `API Error`, `HighPriority`

### 2. Set Appropriate Importance

- 0.9-1.0: Critical decisions, major incidents
- 0.7-0.8: Important observations, successful patterns
- 0.5-0.6: Normal observations, routine decisions
- 0.3-0.4: Low-priority notes
- 0.0-0.2: Ephemeral debug info

### 3. Add Context Metadata

```python
self.memory.add(
    content="...",
    context={
        "task_id": "task-123",
        "session_id": "session-abc",
        "user": "owner",
        "source": "api"
    }
)
```

### 4. Use References to Link Memories

```python
# First memory
id1 = self.memory.add(content="Started deployment")

# Related memory
id2 = self.memory.add(
    content="Deployment completed",
    references=[id1]  # Links back to start
)
```

### 5. Clean Up Regularly

Add to your daily/weekly cron:
```bash
# Garbage collect all agents
for agent in ~/.knowledge/agents/*/; do
  python3 ~/.knowledge/kb_tools.py gc "$(basename "$agent")"
done
```

## Migration Checklist

- [ ] Import `MemoryStore` and `ContextManager`
- [ ] Initialize in `__init__()`
- [ ] Add `.memory.add()` calls for key observations/decisions
- [ ] Add `.context.track_usage()` for token tracking
- [ ] Add `.context.add_task()` / `.remove_task()` for task tracking
- [ ] Query past memories before making decisions
- [ ] Set up periodic garbage collection
- [ ] Update agent documentation

## Troubleshooting

**Q: Where are my memories stored?**
A: `~/.knowledge/agents/<your-agent-name>/memory.jsonl`

**Q: How do I reset an agent's memory?**
A: Delete `~/.knowledge/agents/<agent-name>/` directory

**Q: Can multiple agents share memories?**
A: Yes, use the `~/.knowledge/shared/` directory and query with different agent names

**Q: What if I hit context limits?**
A: Use `ContextManager.should_compress()` and implement compression strategy

## Examples in This Repo

- `example_integration.py` - Complete working example
- `kb_tools.py` - Full API reference (see docstrings)
- `schemas/` - JSON schemas for validation

---
*Gap remediation - addressing 5 critical memory gaps identified in gap analysis*
