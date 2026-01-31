#!/usr/bin/env python3
"""
Extract Conversations - Periodic conversation extraction for memory system

Usage:
  python3 extract-conversations.py \
    --index /path/to/qa-index.json \
    --output-dir /path/to/output \
    [--hours 1] \
    [--session SESSION_ID]

Extracts all Q-A pairs from the past N hours and saves them to files.
Returns summary for sub-agent to process.
"""

import json
import sys
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional, List, Dict
import re

def parse_timestamp(ts_str: str) -> datetime:
    """Parse ISO format timestamp"""
    # Remove trailing Z and parse
    return datetime.fromisoformat(ts_str.replace('Z', '+00:00'))

def get_conversations_since(index_file: Path, hours: int = 1, 
                           session_id: Optional[str] = None) -> Dict:
    """
    Extract all Q-A pairs from the past N hours
    
    Returns: {
        'count': total_qa_pairs,
        'questions': [list of Q with timestamps],
        'answers': [list of A with timestamps],
        'summary': str
    }
    """
    try:
        with open(index_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except FileNotFoundError:
        print(f"Error: Index file not found at {index_file}", file=sys.stderr)
        return {'count': 0, 'questions': [], 'answers': [], 'summary': 'No index found'}
    
    cutoff_time = datetime.utcnow() - timedelta(hours=hours)
    questions = []
    answers = []
    
    for session in data['sessions']:
        if session_id and session['session_id'] != session_id:
            continue
        
        for qa in session['qa_sequence']:
            qa_time = parse_timestamp(qa['timestamp'])
            
            # Include if within time window
            if qa_time >= cutoff_time:
                questions.append({
                    'seq': qa['seq'],
                    'timestamp': qa['timestamp'],
                    'user': qa['user'],
                    'q': qa['q'],
                    'q_tokens': qa['q_tokens'],
                    'topics': qa.get('topic_tags', [])
                })
                
                if qa['a']:
                    answers.append({
                        'seq': qa['seq'],
                        'timestamp': qa['timestamp'],
                        'user': qa['user'],
                        'q': qa['q'][:80],  # Reference to question
                        'a': qa['a'],
                        'significance': qa['a_significance'],
                        'a_tokens': qa['a_tokens']
                    })
    
    summary = f"Found {len(questions)} questions and {len(answers)} answers in past {hours} hour(s)"
    
    return {
        'count': len(questions),
        'questions': questions,
        'answers': answers,
        'summary': summary,
        'cutoff_time': cutoff_time.isoformat() + 'Z'
    }

def save_conversations(output_dir: Path, conversations: Dict, session_id: str) -> Dict:
    """
    Save conversations to files in output directory
    
    Structure:
    output_dir/
    ├── {session_id}-qa.json         (all Q-A metadata)
    ├── questions/
    │   └── {timestamp}-{seq}.txt    (question text)
    └── answers/
        └── {timestamp}-{seq}.txt    (answer text)
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    questions_dir = output_dir / 'questions'
    answers_dir = output_dir / 'answers'
    questions_dir.mkdir(exist_ok=True)
    answers_dir.mkdir(exist_ok=True)
    
    # Save Q-A metadata
    qa_file = output_dir / f'{session_id}-qa.json'
    with open(qa_file, 'w', encoding='utf-8') as f:
        json.dump(conversations, f, ensure_ascii=False, indent=2)
    
    # Save individual questions
    q_files = []
    for q in conversations['questions']:
        safe_ts = q['timestamp'].replace(':', '-').replace('Z', '')
        q_file = questions_dir / f'{safe_ts}-{q["seq"]}.txt'
        with open(q_file, 'w', encoding='utf-8') as f:
            f.write(f"[{q['seq']}] {q['user']} ({q['timestamp']})\n")
            f.write(f"Topics: {', '.join(q['topics']) if q['topics'] else 'none'}\n")
            f.write(f"Tokens: {len(q['q'].split())}\n\n")
            f.write(q['q'])
        q_files.append(str(q_file))
    
    # Save individual answers
    a_files = []
    for a in conversations['answers']:
        safe_ts = a['timestamp'].replace(':', '-').replace('Z', '')
        a_file = answers_dir / f'{safe_ts}-{a["seq"]}.txt'
        with open(a_file, 'w', encoding='utf-8') as f:
            f.write(f"[{a['seq']}] Response to: {a['q']}\n")
            f.write(f"Timestamp: {a['timestamp']}\n")
            f.write(f"Significance: {a['significance']:.2f}\n")
            f.write(f"Tokens: {a['a_tokens']}\n\n")
            f.write(a['a'])
        a_files.append(str(a_file))
    
    return {
        'metadata_file': str(qa_file),
        'questions_dir': str(questions_dir),
        'questions_count': len(q_files),
        'answers_dir': str(answers_dir),
        'answers_count': len(a_files),
        'files': {
            'qa_metadata': str(qa_file),
            'questions': q_files,
            'answers': a_files
        }
    }

if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Extract conversations from QA index')
    parser.add_argument('--index', type=Path, required=True, help='Path to qa-index.json')
    parser.add_argument('--output-dir', type=Path, required=True, help='Output directory for extracted files')
    parser.add_argument('--hours', type=int, default=1, help='Hours to look back (default: 1)')
    parser.add_argument('--session', help='Filter by session ID (optional)')
    
    args = parser.parse_args()
    
    # Extract conversations
    conversations = get_conversations_since(args.index, args.hours, args.session)
    
    if conversations['count'] == 0:
        print(f"No conversations found in past {args.hours} hour(s)")
        sys.exit(0)
    
    # Save to files
    session_id = args.session or 'all-sessions'
    result = save_conversations(args.output_dir, conversations, session_id)
    
    # Print summary for sub-agent
    print(f"\n📊 Conversation Extraction Summary")
    print(f"================================")
    print(f"Time window: {conversations['cutoff_time']} to now")
    print(f"Questions found: {result['questions_count']}")
    print(f"Answers found: {result['answers_count']}")
    print(f"\n📁 Files saved:")
    print(f"   Metadata: {result['metadata_file']}")
    print(f"   Questions: {result['questions_dir']}")
    print(f"   Answers: {result['answers_dir']}")
    print(f"\n✅ Ready for sub-agent to process")
