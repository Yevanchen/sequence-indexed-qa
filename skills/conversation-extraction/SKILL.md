---
name: conversation-extraction
description: Automatic conversation extraction and analysis using cron jobs. Periodically extract Q-A pairs from memory index, analyze them with sub-agents, and generate insights. Use when implementing persistent memory systems that need automatic summarization, topic analysis, or conversation pattern detection across sessions.
---

# Conversation Extraction & Analysis Skill

Automatic periodic extraction and analysis of conversations from the Sequence-Indexed QA memory system.

## Overview

This skill provides:
- **Periodic extraction** — Extract conversations at regular intervals (hourly, daily, etc.)
- **File-based storage** — Save all Q-A pairs to individual files for sub-agent browsing
- **Sub-agent analysis** — Spawn worker agents to analyze and summarize
- **Persistent configuration** — Store cron job config in persistent volume (survives restarts)
- **Report generation** — Create insights and recommendations for main agent

## Architecture

```
Cron Job (hourly)
    ↓
[trigger-extraction.py]
    ├─→ [extract-conversations.py]
    │   └─→ Creates files:
    │       questions/{timestamp}-{seq}.txt
    │       answers/{timestamp}-{seq}.txt
    │       {session_id}-qa.json
    │
    └─→ [sessions_spawn] → sub-agent
        └─→ [subagent-summarize.py]
            ├─ Reads extracted files
            ├─ Analyzes patterns
            └─ Returns report
```

## Quick Start

### 1. Setup Cron Job (One-time)

```bash
python3 setup-cron.py
```

This creates persistent config at:
```
/home/node/clawd/memory/cron-config.json
```

### 2. Register with OpenClaw Cron

```bash
cron add \
  --name memory-extraction-summarizer \
  --schedule "cron:0 * * * * UTC" \
  --payload "systemEvent:TRIGGER_MEMORY_EXTRACTION"
```

Or use the command printed by `setup-cron.py`.

### 3. Every Hour (Automatic)

Cron fires → `TRIGGER_MEMORY_EXTRACTION` → Extracts conversations → Spawns sub-agent → Reports

## Configuration

### Persistent Config File

Location: `/home/node/clawd/memory/cron-config.json`

```json
{
  "version": 1,
  "name": "memory-extraction-summarizer",
  "schedule": {
    "kind": "cron",
    "expr": "0 * * * *",
    "tz": "UTC"
  },
  "config": {
    "index_file": "/home/node/clawd/memory/qa-index.json",
    "extraction_script": "/home/node/clawd/memory/extract-conversations.py",
    "output_dir": "/home/node/clawd/memory/extractions",
    "hours": 1,
    "session_id": "discord-常規-20260130"
  }
}
```

### Adjustable Parameters

Edit `cron-config.json`:

- `schedule.expr` — Cron expression (e.g., `0 * * * *` = hourly)
- `config.hours` — How far back to look (1 = last hour)
- `config.session_id` — Which session to extract from

## Scripts

### extract-conversations.py

Extracts Q-A pairs from index file for a time window.

**Usage:**
```bash
python3 extract-conversations.py \
  --index /home/node/clawd/memory/qa-index.json \
  --output-dir /tmp/extraction \
  --hours 1 \
  --session discord-常規-20260130
```

**Output structure:**
```
/tmp/extraction/
├── discord-常規-20260130-qa.json     (metadata)
├── questions/
│   ├── 2026-01-31T09-00-00-1.txt     (Q text)
│   ├── 2026-01-31T09-05-00-2.txt
│   └── ...
└── answers/
    ├── 2026-01-31T09-00-00-1.txt     (A text)
    ├── 2026-01-31T09-05-00-2.txt
    └── ...
```

### subagent-summarize.py

Sub-agent script that reads extracted files and generates analysis.

**Usage:**
```bash
python3 subagent-summarize.py /tmp/extraction
```

**Output:**
- Console report (human-readable)
- `analysis.json` (structured data)

**Analysis includes:**
- Question/answer counts
- Topic frequencies
- High-significance answers
- Missing answers
- Conversation patterns

### setup-cron.py

One-time setup script that creates persistent config.

**Usage:**
```bash
python3 setup-cron.py
```

Creates `/home/node/clawd/memory/cron-config.json`.

### trigger-extraction.py

Main script called by cron job. Coordinates extraction and sub-agent spawning.

**Usage (via cron systemEvent):**
```
TRIGGER_MEMORY_EXTRACTION
```

Or manual:
```bash
python3 trigger-extraction.py
```

## Integration with OpenClaw Agent

### In your agent loop:

```python
# Option 1: Simple logging (no extraction yet)
# Just before returning response to user:
memory_log.add_qa(
    session_id="discord-常規-20260130",
    user="Evanchen",
    q=user_message,
    a=agent_response,
    topic_tags=extract_topics(agent_response)
)

# Option 2: Trigger extraction manually
# When user asks to summarize:
subprocess.run([
    'python3', 
    '/home/node/clawd/memory/trigger-extraction.py'
])

# Option 3: Full automation (spawns sub-agent)
# Cron automatically triggers, sub-agent processes
```

## Data Persistence

### Permanent Locations

All data stored in `/home/node/clawd/memory/` (NFS persistent volume):

- `qa-index.json` — Q-A index (main)
- `cron-config.json` — Cron configuration
- `extractions/` — Timestamped extraction folders
  - `2026-01-31-0900/`
  - `2026-01-31-1000/`
  - etc.

Survives container restarts ✅

### Temporary Locations (do NOT use)

- `/home/node/.openclaw/workspace/` — Docker overlay (deleted on restart) ❌

## Performance

For 6 Q-A pairs per hour:

| Operation | Time | Size |
|-----------|------|------|
| Extract | ~50ms | 5 KB |
| Summarize | ~100ms | 2 KB |
| Store | ~50ms | 7 KB |

Scales linearly with conversation volume.

## Troubleshooting

### Cron not firing?

Check OpenClaw cron system:
```bash
cron list
```

Verify config exists:
```bash
ls -l /home/node/clawd/memory/cron-config.json
```

### Extraction directory empty?

Check if conversations in time window:
```bash
python3 /home/node/clawd/memory/memory-load.py recent \
  --index /home/node/clawd/memory/qa-index.json \
  --session discord-常規-20260130 \
  --window 10
```

### Sub-agent not running?

Ensure it's spawned by main agent via:
```python
sessions_spawn(
    task="Analyze conversations in /home/node/clawd/memory/extractions/latest",
    agentId="summarizer",
    label="memory-analysis"
)
```

## References

- **Sequence-Indexed QA:** See `sequence-indexed-qa` skill for memory core
- **Agent Design:** See OpenClaw docs for sessions_spawn integration
