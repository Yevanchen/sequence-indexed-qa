# Memory System - Sequence-Indexed QA Architecture

This is a custom long-term memory system designed for LLM context retrieval based on Q-A sequence indexing.

## Architecture

### Core Principle
- **Questions (Q)** are semantic anchors — always stored (cheap, meaningful)
- **Answers (A)** are stored selectively — only if significance > 0.6 or user-marked
- **Sequences matter** — last 5 Q-A pairs provide more context than random samples
- **Sparse indexing** — hash-based + keyword tokens instead of dense embeddings (faster, cheaper)

### File Structure

```
memory/
├── qa-index.json              # Main index: all Q's + significant A's
├── sessions/                  # Per-session detailed logs (optional)
│   └── discord-常规-20260130.json
├── archive/                   # Old sessions (>30 days)
│   └── ...
├── memory-cli.sh              # Shell CLI for queries
├── memory-log.py              # Python: add new Q-A pairs
├── memory-load.py             # Python: retrieve context
└── README.md                  # This file
```

### qa-index.json Structure

```json
{
  "version": 1,
  "structure": "sequence-indexed-qa",
  
  "sessions": [
    {
      "session_id": "discord-常规-20260130",
      "channel_id": "1466083818061566090",
      "created": "2026-01-30T18:16:00Z",
      "qa_sequence": [
        {
          "seq": 1,
          "timestamp": "2026-01-30T18:16:00Z",
          "user": "Evanchen",
          "q": "hi",
          "q_tokens": ["hi", "greeting"],
          "q_hash": "8f14e45fceea167a5a36dedd4bea2543",
          "a": null,
          "a_significance": 0.1,
          "a_tokens": 0,
          "topic_tags": []
        }
      ]
    }
  ],
  
  "index": {
    "by_topic": {
      "memory_design": [{"session": "...", "seq": 6}],
      "discord_config": [{"session": "...", "seq": 2}]
    },
    "by_recency": [
      {"session": "...", "seq": 6, "timestamp": "..."}
    ],
    "by_semantic_hash": {
      "8f14e45fceea167a5a36dedd4bea2543": {"session": "...", "seq": 1}
    }
  },
  
  "metadata": {
    "total_qa_pairs": 6,
    "stored_answers": 5,
    "average_significance": 0.748,
    "compression_ratio": 0.833
  }
}
```

## Usage

### 1. Add a New Q-A Pair (Python)

```bash
python3 memory/memory-log.py \
  --session discord-常规-20260130 \
  --user Evanchen \
  --q "How to configure Discord?" \
  --a "Go to settings..." \
  --topics discord_config messaging \
  --significance 0.85
```

Auto-significance scoring if not provided:
- Length (0-0.3): longer answers score higher
- Complexity (0-0.2): more keywords = more complex
- Technical (0-0.25): code/architecture/API content
- Important (0-0.15): security, critical keywords
- Actionable (0-0.1): how-to, steps, follow-through

### 2. Query Recent Context (Python)

```bash
python3 memory/memory-load.py recent \
  --session discord-常规-20260130 \
  --window 5
```

Output: Last 5 Q-A pairs from that session (for context injection)

### 3. Search by Topic

```bash
python3 memory/memory-load.py topic memory_design
```

Output: All Q-A pairs tagged with `memory_design`

### 4. Search by Query

```bash
python3 memory/memory-load.py query "how to use memory system" \
  --limit 5 \
  --min-sig 0.6
```

Output: Top 5 relevant Q-A pairs matching query tokens

### 5. Shell CLI for Quick Lookups

```bash
# List all topics
./memory/memory-cli.sh list-topics

# Get all Q-A for a topic
./memory/memory-cli.sh query-topic memory_design

# Get last 10 Q-A pairs
./memory/memory-cli.sh query-recent 10

# Update significance
./memory/memory-cli.sh set-significance 2 0.95

# Show memory stats
./memory/memory-cli.sh stats
```

## Significance Scoring

### Auto-Scoring (Applied by `memory-log.py`)

An answer scores high if:
- **Long** (200+ chars): +0.3
- **Complex question** (8+ keywords): +0.2
- **Technical content** (code, design, API): +0.25
- **Important keywords** (security, critical): +0.15
- **Actionable** (how-to, steps): +0.1

Default score = 0 if no answer (A=null)

### Manual Override

```bash
./memory/memory-cli.sh set-significance <seq> <0-1>
```

Set `--significance` flag when logging:
```bash
python3 memory/memory-log.py --q "..." --a "..." --significance 0.95
```

## Context Injection Strategy

When I wake up and receive a message:

1. **Extract tokens** from new message
2. **Lookup by semantic hash** if exact match exists
3. **Search by topic** if keywords match indexed topics
4. **Load recent context** — last 5 Q-A pairs from current session
5. **Inject into system prompt** — "Recent conversation context:"

Example:
```
User: "你觉得这个设计怎么样？"
→ Extract: ["设计", "评价"]
→ Lookup: topics["memory_design"]
→ Load: seq [4,5,6] from current session
→ Inject: "Recent: [Q4: memory mechanism] [A4: sequence-indexed...] [Q5: ...]"
```

## Performance Characteristics

| Operation | Time | Notes |
|-----------|------|-------|
| Add Q-A | O(1) | Append to session, update 3 indices |
| Query by topic | O(1) | Hash lookup |
| Query by semantic hash | O(1) | Direct hash match |
| Query recent (window=5) | O(1) | Array slice |
| Search by token overlap | O(n) | Linear scan, but n = unique Q-A pairs |
| Memory on disk | ~10KB per 100 QA | Sparse, only significant A's |

## Maintenance

### Pruning Old Sessions

```bash
# Archive sessions >30 days old
find memory/sessions -mtime +30 -exec mv {} memory/archive/ \;
```

### Merging Sessions (Optional)

If a user has multiple Discord channels, consider merging related topics:

```python
# Combine topics from different sessions
# Topics are already hashable, so manual merge of "by_topic" suffices
```

### Re-scoring Significance

Bulk update based on new criteria:

```python
# Read, iterate all qa's, recalculate, write back
```

## Examples

### Current State

6 Q-A pairs logged from 2026-01-30 18:16-18:26 UTC
- **Seq 1:** "hi" (greeting, no answer)
- **Seq 2:** Discord config question (significant: 0.8)
- **Seq 3:** Memory explanation (significant: 0.6)
- **Seq 4:** Architecture rationale (significant: 0.85)
- **Seq 5:** Relationship confirmation (significant: 0.7)
- **Seq 6:** Memory system design (significant: 0.95)

Topics indexed:
- `memory_design` → seq 6
- `discord_config` → seq 2
- `architecture` → seq 3, 4
- `llm_architecture` → seq 6

## Next Steps

1. **Real-time logging** — Each response I give, log it automatically
2. **User-curated significance** — Evanchen marks which answers matter most
3. **Cross-session learning** — Use topics to find related context from other sessions
4. **Context window optimization** — Inject only most relevant 2-3 pairs to save tokens

---

**Created:** 2026-01-30
**System:** Sequence-Indexed QA with Sparse Indexing
**Language:** JSON + Python + Shell
