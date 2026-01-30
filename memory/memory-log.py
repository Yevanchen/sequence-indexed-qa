#!/usr/bin/env python3
"""
Memory Logger - Add new QA pairs to the index
Usage: python3 memory-log.py [options]
"""

import json
import hashlib
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional, List

INDEX_FILE = Path("/home/node/.openclaw/workspace/memory/qa-index.json")

def hash_text(text: str) -> str:
    """Generate MD5 hash of text for semantic reference"""
    return hashlib.md5(text.encode()).hexdigest()

def extract_tokens(text: str) -> List[str]:
    """Simple token extraction: split by whitespace and punctuation"""
    import re
    # Split by whitespace and punctuation, keep words > 2 chars
    tokens = re.findall(r'\b\w{2,}\b', text.lower())
    return list(set(tokens))[:20]  # Top 20 unique tokens

def score_significance(q: str, a: Optional[str], prev_topic: Optional[str] = None) -> float:
    """
    Auto-score answer significance (0-1)
    
    Factors:
    - Answer length (answers > 200 chars get points)
    - Question complexity (more keywords = more complex)
    - Contains code/technical content (+0.2)
    - Follows-up on same topic (+0.1)
    """
    if a is None:
        return 0.0
    
    score = 0.0
    
    # Length factor (0-0.3)
    length_factor = min(len(a) / 500, 1.0) * 0.3
    score += length_factor
    
    # Question complexity (0-0.2)
    q_tokens = len(extract_tokens(q))
    complexity_factor = min(q_tokens / 8, 1.0) * 0.2
    score += complexity_factor
    
    # Technical content (0-0.25)
    technical_keywords = ['code', 'function', 'api', 'database', 'design', 'architecture', 
                         'config', 'system', 'algorithm', 'implement', 'optimization']
    if any(kw in a.lower() for kw in technical_keywords):
        score += 0.25
    
    # Emotional/importance weight (0-0.15)
    important_keywords = ['important', '重要', 'critical', 'must', '必须', 'security', '安全']
    if any(kw in a.lower() or kw in q.lower() for kw in important_keywords):
        score += 0.15
    
    # Actionable (0-0.1)
    action_keywords = ['how to', '怎样', '如何', 'follow these', '按照', 'step']
    if any(kw in a.lower() or kw in q.lower() for kw in action_keywords):
        score += 0.1
    
    return min(score, 1.0)

def get_next_seq(session_id: str) -> int:
    """Get next sequence number for a session"""
    try:
        with open(INDEX_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        for session in data.get('sessions', []):
            if session['session_id'] == session_id:
                return max([qa['seq'] for qa in session['qa_sequence']], default=0) + 1
        
        # New session
        return 1
    except (FileNotFoundError, json.JSONDecodeError):
        return 1

def add_qa(session_id: str, user: str, q: str, a: Optional[str] = None, 
           topic_tags: Optional[List[str]] = None, significance: Optional[float] = None) -> bool:
    """Add a new Q-A pair to the index"""
    
    if significance is None:
        significance = score_significance(q, a)
    
    # Clamp significance to [0, 1]
    significance = max(0.0, min(1.0, significance))
    
    try:
        with open(INDEX_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except FileNotFoundError:
        print(f"Error: Index file not found at {INDEX_FILE}")
        sys.exit(1)
    
    now = datetime.utcnow().isoformat() + 'Z'
    next_seq = get_next_seq(session_id)
    
    qa_entry = {
        "seq": next_seq,
        "timestamp": now,
        "user": user,
        "q": q,
        "q_tokens": extract_tokens(q),
        "q_hash": hash_text(q),
        "a": a,
        "a_significance": significance,
        "a_tokens": len(a.split()) if a else 0,
        "topic_tags": topic_tags or []
    }
    
    # Find or create session
    session_found = False
    for session in data['sessions']:
        if session['session_id'] == session_id:
            session['qa_sequence'].append(qa_entry)
            session['last_updated'] = now
            session_found = True
            break
    
    if not session_found:
        print(f"Error: Session {session_id} not found")
        return False
    
    # Update indices
    if topic_tags:
        for tag in topic_tags:
            if tag not in data['index']['by_topic']:
                data['index']['by_topic'][tag] = []
            data['index']['by_topic'][tag].append({
                "session": session_id,
                "seq": next_seq
            })
    
    # by_recency (prepend)
    data['index']['by_recency'].insert(0, {
        "session": session_id,
        "seq": next_seq,
        "timestamp": now
    })
    
    # by_semantic_hash
    data['index']['by_semantic_hash'][hash_text(q)] = {
        "session": session_id,
        "seq": next_seq
    }
    
    # Update metadata
    data['metadata']['total_qa_pairs'] += 1
    if a:
        data['metadata']['stored_answers'] += 1
        data['metadata']['stored_answers_count'] = data['metadata'].get('stored_answers_count', 0) + 1
    else:
        data['metadata']['empty_answers_count'] = data['metadata'].get('empty_answers_count', 0) + 1
    
    data['metadata']['last_updated'] = now
    
    # Save back
    try:
        with open(INDEX_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"✅ Added Q-A pair #{next_seq} to {session_id}")
        print(f"   Significance: {significance:.2f} | Topics: {topic_tags or 'none'}")
        return True
    except IOError as e:
        print(f"Error: Could not write to {INDEX_FILE}: {e}")
        return False

if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Memory Logger - Add Q-A pairs')
    parser.add_argument('--session', required=True, help='Session ID')
    parser.add_argument('--user', default='unknown', help='Username')
    parser.add_argument('--q', required=True, help='Question text')
    parser.add_argument('--a', help='Answer text (optional)')
    parser.add_argument('--topics', nargs='+', help='Topic tags')
    parser.add_argument('--significance', type=float, help='Override significance score (0-1)')
    
    args = parser.parse_args()
    
    success = add_qa(
        session_id=args.session,
        user=args.user,
        q=args.q,
        a=args.a,
        topic_tags=args.topics,
        significance=args.significance
    )
    
    sys.exit(0 if success else 1)
