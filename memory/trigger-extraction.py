#!/usr/bin/env python3
"""
Trigger Memory Extraction - Called by cron job every hour

This script:
1. Reads cron config
2. Extracts conversations using extract-conversations.py
3. Spawns sub-agent to analyze
4. Reports results to main agent

To be triggered by cron or systemEvent
"""

import json
import subprocess
import sys
from pathlib import Path
from datetime import datetime

CONFIG_FILE = Path('/home/node/clawd/memory/cron-config.json')

def load_config():
    """Load cron configuration"""
    if not CONFIG_FILE.exists():
        print(f"⚠️  Config file not found: {CONFIG_FILE}")
        print(f"Run setup-cron.py first")
        return None
    
    with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)

def run_extraction(config: dict) -> Path:
    """Run conversation extraction script"""
    
    script = config['config']['extraction_script']
    index_file = config['config']['index_file']
    output_dir = Path(config['config']['output_dir']) / datetime.utcnow().strftime('%Y%m%d-%H%M%S')
    hours = config['config']['hours']
    
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"📥 Extracting conversations...")
    print(f"   Script: {script}")
    print(f"   Index: {index_file}")
    print(f"   Output: {output_dir}")
    print(f"   Hours: {hours}")
    
    cmd = [
        'python3', script,
        '--index', index_file,
        '--output-dir', str(output_dir),
        '--hours', str(hours),
        '--session', config['config']['session_id']
    ]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        if result.returncode == 0:
            print(f"\n✅ Extraction complete")
            print(result.stdout)
            return output_dir
        else:
            print(f"\n❌ Extraction failed:")
            print(result.stderr)
            return None
    except subprocess.TimeoutExpired:
        print(f"❌ Extraction timed out")
        return None
    except Exception as e:
        print(f"❌ Error running extraction: {e}")
        return None

def report_to_main_agent(extraction_dir: Path):
    """
    Report results to main agent.
    
    In a real implementation, this would use sessions_send to notify
    the main agent, or return structured data for agent to process.
    """
    
    report = {
        'timestamp': datetime.utcnow().isoformat() + 'Z',
        'status': 'completed',
        'extraction_dir': str(extraction_dir),
        'message': f'Conversations extracted to {extraction_dir}. Ready for sub-agent analysis.'
    }
    
    print(f"\n📤 Report to main agent:")
    print(json.dumps(report, indent=2))
    
    # In real OpenClaw integration:
    # sessions_send(
    #     message=f"Memory extraction complete. Extraction dir: {extraction_dir}",
    #     label="main"
    # )
    
    return report

def main():
    config = load_config()
    if not config:
        sys.exit(1)
    
    # Run extraction
    extraction_dir = run_extraction(config)
    if not extraction_dir:
        sys.exit(1)
    
    # Report to main agent
    report_to_main_agent(extraction_dir)
    
    print(f"\n✅ Trigger complete")
    print(f"   Extraction dir: {extraction_dir}")
    print(f"   Next: Sub-agent analyzes files")

if __name__ == '__main__':
    main()
