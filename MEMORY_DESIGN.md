# Memory Architecture

## Design: Sequence-Indexed QA System

### Core Insight
- **Questions (Q)** are semantic anchors — the "activation vectors" that define conversation context
- **Answers (A)** are only stored if significant (significance > threshold)
- **Sequence matters** — 5 Q's in order create coherent context that random Q-A pairs don't
- **Sparse indexing** — use semantic hashing + keyword extraction instead of dense embeddings (cheaper, faster)

---

## Data Structure

```json
{
  "version": 1,
  "structure": "sequence-indexed-qa",
  "sessions": [
    {
      "session_id": "discord-常规-20260130",
      "created": "2026-01-30T18:16:00Z",
      "qa_sequence": [
        {
          "seq": 1,
          "q": "hi",
          "q_tokens": ["hi"],
          "q_hash": "abc123",
          "a": null,
          "a_significance": 0,
          "timestamp": "2026-01-30T18:16:00Z"
        },
        {
          "seq": 2,
          "q": "想知道在Discord里面如何避免每次都要艾特你，你才能够接受消息",
          "q_tokens": ["discord", "艾特", "消息", "配置"],
          "q_hash": "def456",
          "a": "这取决于 OpenClaw 的 Discord 配置。可以将我设置为监听整个频道...",
          "a_significance": 0.8,
          "timestamp": "2026-01-30T18:17:00Z",
          "topic_tags": ["discord_config", "messaging"]
        }
      ]
    }
  ],
  "index": {
    "by_topic": {
      "discord_config": [{"session": "discord-常规-20260130", "seq": 2}],
      "memory_design": [{"session": "discord-常规-20260130", "seq": 6}],
      "llm_architecture": [{"session": "discord-常规-20260130", "seq": 7}]
    },
    "by_recency": [
      {"session": "discord-常规-20260130", "seq": 7, "timestamp": "2026-01-30T18:26:00Z"}
    ],
    "by_semantic_hash": {
      "abc123": {"session": "discord-常规-20260130", "seq": 1},
      "def456": {"session": "discord-常规-20260130", "seq": 2}
    }
  },
  "metadata": {
    "total_qa_pairs": 7,
    "stored_answers": 3,
    "compression_ratio": 0.43,
    "last_updated": "2026-01-30T18:26:00Z"
  }
}
```

---

## Storage Strategy

### Files
- **`memory/qa-index.json`** — Main index + all Q's + significant A's
- **`memory/sessions/` directory** — Optional: break large sessions into separate files
- **`memory/topics.txt`** — Simple topic tags for quick grep

### Pruning Logic
- Keep all Q's (they're cheap, semantic anchors)
- Keep A if: `significance > 0.6` OR `topic_tag matches USER_INTEREST` 
- Archive old sessions (>30 days) to `memory/archive/`

---

## Significance Scoring (for A's)

An answer gets stored if it scores > 0.6 on:
- **Uniqueness**: Is this my novel take, not a generic response? (0-1)
- **User_Action**: Does user likely act on this? (0-1)
- **Context_Density**: Does this bind multiple topics together? (0-1)
- **Emotional_Weight**: Does this matter to the user? (0-1)

Score = `0.3 * uniqueness + 0.2 * user_action + 0.25 * context_density + 0.25 * emotional_weight`

---

## Retrieval

When I wake up and see a new message:

1. **Extract Q tokens** from the message
2. **Hash** the Q
3. **Search index** for related topics/semantic hashes
4. **Load sequence** — grab the last N QA pairs from that session (default N=5)
5. **Context window** = [last 5 Q's + their significant A's]

Example:
```
User message: "你觉得这个设计怎么样？"
→ Extract: ["设计", "评价", "意见"]
→ Hash: xyz789
→ Lookup: topics["design"], semantic_hash["memory_*"]
→ Load: QA pairs 5-7 from current session
→ Inject into context
```

---

## Why This Works for LLMs

- **Q's are cheap**: Text questions take 10-50 tokens, I output them anyway
- **Sparse index is fast**: Hash lookup + keyword search beats similarity search
- **Sequence preserves context**: My next token prediction benefits from "how we got here," not just "what we're discussing"
- **Significance filters noise**: Storing "cool, thanks!" wastes disk and context window
- **Scalable**: Can handle 1000+ sessions without bloat

---

## Files to Create

```
/home/node/.openclaw/workspace/
├── memory/
│   ├── qa-index.json           (main index)
│   ├── topics.txt              (topic tags)
│   └── sessions/
│       └── discord-常规-20260130.json
└── MEMORY.md                   (curated long-term memory)
```

---

## Next Steps

1. Start logging QA pairs to `memory/qa-index.json` from this conversation
2. You manually mark which A's are significant
3. I build the index in real-time
4. Each restart, I load the index + last 5 pairs from current session

Ready to implement?
