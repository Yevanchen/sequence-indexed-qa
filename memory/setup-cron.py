#!/usr/bin/env python3
"""
Setup Cron Job - Configure persistent memory extraction

This script sets up a periodic cron job that:
1. Extracts conversations from the past hour
2. Spawns a sub-agent to analyze them
3. Stores results in persistent volume

Cron configuration is stored in /home/node/clawd/memory/cron-config.json
"""

import json
from pathlib import Path
from datetime import datetime

CRON_CONFIG_FILE = Path('/home/node/clawd/memory/cron-config.json')

def create_cron_config():
    """Create cron job configuration"""
    
    config = {
        "version": 1,
        "name": "memory-extraction-summarizer",
        "description": "Extract and summarize conversations hourly",
        "schedule": {
            "kind": "cron",
            "expr": "0 * * * *",  # Every hour at :00
            "tz": "UTC"
        },
        "payload": {
            "kind": "systemEvent",
            "text": "TRIGGER_MEMORY_EXTRACTION: Extract conversations from past hour and spawn summarizer sub-agent"
        },
        "config": {
            "index_file": "/home/node/clawd/memory/qa-index.json",
            "extraction_script": "/home/node/clawd/memory/extract-conversations.py",
            "summarizer_script": "/home/node/clawd/memory/subagent-summarize.py",
            "output_dir": "/home/node/clawd/memory/extractions",
            "hours": 1,
            "session_id": "discord-常規-20260130"
        },
        "enabled": True,
        "created": datetime.utcnow().isoformat() + 'Z'
    }
    
    return config

def save_cron_config(config: dict):
    """Save cron config to persistent volume"""
    
    CRON_CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
    
    with open(CRON_CONFIG_FILE, 'w', encoding='utf-8') as f:
        json.dump(config, f, ensure_ascii=False, indent=2)
    
    print(f"✅ Cron config saved to {CRON_CONFIG_FILE}")
    print(f"\nConfiguration:")
    print(f"  Schedule: Every hour (0 * * * *)")
    print(f"  Script: {config['config']['extraction_script']}")
    print(f"  Output: {config['config']['output_dir']}")
    print(f"  Session: {config['config']['session_id']}")

def register_cron_job():
    """
    Register the cron job with OpenClaw's cron system.
    
    This would be called by the main agent using the cron tool:
    
    cron.add(job={
        "name": "memory-extraction-summarizer",
        "schedule": {"kind": "cron", "expr": "0 * * * *", "tz": "UTC"},
        "payload": {"kind": "systemEvent", "text": "..."},
        "sessionTarget": "main",
        "enabled": True
    })
    """
    
    config = create_cron_config()
    save_cron_config(config)
    
    print("\n📋 To register with OpenClaw cron system, run:")
    print("""
cron add \\
  --name memory-extraction-summarizer \\
  --schedule "cron:0 * * * * UTC" \\
  --payload "systemEvent:TRIGGER_MEMORY_EXTRACTION"
""")
    
    return config

if __name__ == '__main__':
    print("🔧 Setting up persistent memory extraction cron job...\n")
    
    config = register_cron_job()
    
    print("\n✅ Setup complete!")
    print(f"\nCron config file: {CRON_CONFIG_FILE}")
    print(f"Persistent volume: /home/node/clawd/memory")
    print(f"\nNext steps:")
    print(f"1. Run this setup script")
    print(f"2. Main agent registers cron job")
    print(f"3. Every hour: conversations extracted and analyzed")
    print(f"4. Results stored in /home/node/clawd/memory/extractions")
