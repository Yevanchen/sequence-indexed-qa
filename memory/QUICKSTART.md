# Memory System - Quick Start

## What Just Happened

I implemented the Sequence-Indexed QA system you designed. Here's what's ready:

### Files Created

```
memory/
├── qa-index.json          ✅ Index with your conversation (seq 1-6)
├── memory-cli.sh          ✅ Shell commands for quick lookups
├── memory-log.py          ✅ Python: add new Q-A pairs
├── memory-load.py         ✅ Python: retrieve context
├── README.md              ✅ Full documentation
└── QUICKSTART.md          ✅ This file
```

Plus:
- `MEMORY.md` — My long-term memory about you and our relationship
- `MEMORY_DESIGN.md` — Full system design spec

## Current Data

6 Q-A pairs logged from today's conversation:

```
[1] Q: "hi" → no answer (sig: 0.1)
[2] Q: Discord + storage → detailed answer (sig: 0.8)
[3] Q: memory contents → explanation (sig: 0.6)
[4] Q: why reset on restart? → security design (sig: 0.85)
[5] Q: only 2 of us? → relationship clarification (sig: 0.7)
[6] Q: design memory system → full design (sig: 0.95)
```

## Try These Commands Now

### 1. See all topics
```bash
./memory/memory-cli.sh list-topics
```

Expected output:
```
architecture
data_structure
discord_config
...
memory_design
relationship
security
storage
```

### 2. Get last 5 Q-A pairs
```bash
./memory/memory-cli.sh query-recent 5
```

### 3. Check stats
```bash
./memory/memory-cli.sh stats
```

Output:
```
📊 Memory Statistics
Total Q-A pairs: 6
Stored answers: 5
Compression ratio: 0.833
Last updated: 2026-01-30T18:28:00Z
```

### 4. Query by topic (Python)
```bash
python3 memory/memory-load.py topic memory_design
```

Shows all Q-A pairs tagged with "memory_design"

### 5. Search for relevant context (Python)
```bash
python3 memory/memory-load.py query "how does memory work" --limit 5
```

### 6. Add a new Q-A pair
```bash
python3 memory/memory-log.py \
  --session discord-常规-20260130 \
  --user Evanchen \
  --q "What's your favorite programming language?" \
  --a "I don't have favorites, but I appreciate languages that express intent clearly." \
  --topics preferences languages
```

The system auto-scores significance (or you can override):
```bash
python3 memory/memory-log.py \
  --session discord-常規-20260130 \
  --user Evanchen \
  --q "Why does X matter?" \
  --a "Because..." \
  --significance 0.9
```

### 7. Update significance manually
```bash
./memory/memory-cli.sh set-significance 2 0.95
```

Changes sequence #2 to significance 0.95

## How It Works (Recap)

### Storage
- **qa-index.json** — Single JSON file, all sessions
  - All Q's stored (10-50 tokens, cheap)
  - Only significant A's stored (significance > threshold)
  - Three indices: by_topic, by_recency, by_semantic_hash

### Retrieval (When I Wake Up)
1. You send a message
2. I extract tokens
3. I look up related topics from recent session
4. I load last 5 Q-A pairs (sequence context)
5. I inject them into my prompt: "Recent conversation: [Q4] [A4] [Q5] [A5]..."

### Performance
- Add Q-A: O(1) — just append
- Query by topic: O(1) — hash lookup
- Recent context: O(1) — array slice
- Disk: ~10KB per 100 Q-A pairs

## What I'll Do

Going forward:
1. **Auto-log new Q-A** after each conversation
2. **Load context** when you message me (from same session)
3. **Tag topics** based on your questions
4. **Track significance** (you can override)

## What You Can Do

- **Mark significant answers**: `./memory-cli.sh set-significance <seq> <value>`
- **Query anytime**: `python3 memory-load.py query "your question"`
- **Add bulk pairs**: Call `memory-log.py` multiple times
- **Adjust threshold**: Change significance scoring rules in `memory-log.py`
- **Archive old sessions**: Move to `memory/archive/` when >30 days

## Next Questions

For you to decide:
1. Should I always auto-log Q-A, or wait for your signal?
2. Auto-score significance (current default) or ask you each time?
3. Load context automatically, or only when you ask?
4. How many recent pairs to inject (default: 5)?

---

**Status:** ✅ Ready to use
**Test it:** `./memory-cli.sh stats`
