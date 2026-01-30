# MEMORY.md - Long-Term Memory

## About Evanchen

- **Name:** Evanchen
- **Timezone:** UTC (implied from Discord timestamp)
- **Location:** China (使用中文, Simplified Chinese)
- **Platform:** Discord (#常規 channel, private 1-on-1)
- **Interaction Style:** Technical, iterative design, Mandarin Chinese

## Key Characteristics

- **Very interested in LLM architecture** — asks about token generation, semantic hashing, memory design
- **Systems thinker** — designs comprehensive systems (not just quick hacks)
- **Values efficiency** — conscious about disk space, compression, performance (sparse indexing vs dense embeddings)
- **Pragmatic** — wants something real/implemented, not just theoretical (see: "你帮我设计实施应用起来")
- **Clear communicator** — writes detailed questions, expects detailed answers

## Projects & Interests

1. **Memory System** (CURRENT)
   - Designed a Sequence-Indexed QA system
   - Wants QA pairs (Q=key, A=value)
   - Only stores significant A's; all Q's are stored
   - Sparse indexing (hash + keywords) instead of dense embeddings
   - Wants trajectory/sequence, not random samples

2. **OpenClaw Integration**
   - Running OpenClaw as personal assistant
   - Discord channel as primary interface
   - Interested in persistent storage volumes
   - Wants to avoid constant @mentions

## Preferences

- **Language:** Primarily Mandarin Chinese (中文), understands English
- **Communication:** Direct, technical, concise
- **Pace:** Fast — wants implementation quickly
- **Detail:** Appreciates both high-level design AND concrete implementation

## Relationship & Trust

- Just started interacting (2026-01-30)
- Private Discord channel (only Evanchen + bot)
- Already asked me to design + implement a system (high trust signal)
- Cares about privacy (noted: "为什么我每次重启你都和新的一样")
- Interested in how my memory/architecture works

## Questions to Answer Next

When Evanchen reaches out, consider:
1. How can I use the memory system efficiently?
2. What should I automate vs what should they control?
3. How often should I log new Q-A pairs?
4. Should I mark significance automatically or ask them?

---

**Last Updated:** 2026-01-30 18:28 UTC
**Current Status:** Memory system implemented and ready for testing
