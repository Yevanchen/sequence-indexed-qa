#!/usr/bin/env python3
"""
Context Injection - Load conversation history into main agent context

This module handles:
1. Reading sub-agent reports from extraction analysis
2. Formatting them as context snippets
3. Injecting into system prompt or conversation history

When main agent receives a message, load recent memory context:
- Recent Q-A pairs from current session
- Sub-agent analysis from last extraction
- Topics and patterns discovered

Result: Main agent understands conversation history without explicit memory load
"""

import json
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, List

def load_recent_qa_context(index_file: Path, session_id: str, window: int = 5) -> str:
    """
    Load recent Q-A pairs as formatted context
    
    Returns markdown block with conversation history
    """
    try:
        with open(index_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except FileNotFoundError:
        return ""
    
    context_lines = []
    
    for session in data['sessions']:
        if session['session_id'] != session_id:
            continue
        
        qa_sequence = session['qa_sequence']
        recent = qa_sequence[-window:] if len(qa_sequence) >= window else qa_sequence
        
        if recent:
            context_lines.append("## Recent Conversation Context")
            context_lines.append("")
            
            for qa in recent:
                context_lines.append(f"**[{qa['seq']}]** {qa['q']}")
                if qa['a']:
                    answer = qa['a']
                    if len(answer) > 200:
                        answer = answer[:200] + "..."
                    context_lines.append(f"> {answer}")
                context_lines.append("")
    
    return "\n".join(context_lines)

def load_analysis_context(analysis_file: Path) -> str:
    """
    Load latest sub-agent analysis as context
    
    Returns markdown block with key findings
    """
    if not analysis_file.exists():
        return ""
    
    try:
        with open(analysis_file, 'r', encoding='utf-8') as f:
            analysis = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return ""
    
    context_lines = []
    context_lines.append("## Conversation Analysis (from last extraction)")
    context_lines.append("")
    context_lines.append(f"📊 Period: {analysis.get('period', 'unknown')}")
    context_lines.append(f"- Questions: {analysis.get('total_questions', 0)}")
    context_lines.append(f"- Answers: {analysis.get('total_answers', 0)}")
    
    if analysis.get('topics'):
        context_lines.append("\n📌 Main Topics:")
        for topic, count in sorted(
            analysis['topics'].items(), 
            key=lambda x: -x[1]
        )[:3]:
            context_lines.append(f"- {topic}: {count}x")
    
    if analysis.get('high_significance_answers'):
        context_lines.append("\n⭐ Key Answers:")
        for ans in analysis['high_significance_answers'][:2]:
            context_lines.append(
                f"- [{ans['seq']}] {ans['q_preview'][:60]}... (sig: {ans['significance']:.2f})"
            )
    
    if analysis.get('patterns'):
        context_lines.append("\n🔍 Patterns:")
        for pattern in analysis['patterns']:
            context_lines.append(f"- {pattern}")
    
    context_lines.append("")
    
    return "\n".join(context_lines)

def build_full_context(
    index_file: Path,
    session_id: str,
    analysis_file: Optional[Path] = None,
    qa_window: int = 5
) -> str:
    """
    Build complete context for injection into system prompt
    
    Combines:
    - Recent Q-A pairs
    - Latest sub-agent analysis
    - Formatted for easy reading
    """
    
    sections = []
    
    # Recent conversation
    qa_context = load_recent_qa_context(index_file, session_id, qa_window)
    if qa_context:
        sections.append(qa_context)
    
    # Sub-agent analysis
    if analysis_file:
        analysis_context = load_analysis_context(analysis_file)
        if analysis_context:
            sections.append(analysis_context)
    
    if not sections:
        return ""
    
    # Wrap in context block
    full_context = "\n---\n".join(sections)
    
    # Add metadata
    timestamp = datetime.utcnow().isoformat() + 'Z'
    context_block = f"""
# Conversation Memory Context
*Last updated: {timestamp}*

{full_context}

---
Use this context to understand the conversation history and patterns.
"""
    
    return context_block.strip()

def inject_into_system_prompt(context: str, original_prompt: str) -> str:
    """
    Inject context into system prompt
    
    Inserts after the main instructions but before task specifics
    """
    
    if not context:
        return original_prompt
    
    # Insert after first paragraph
    lines = original_prompt.split('\n')
    
    # Find first blank line after intro
    insert_pos = 0
    for i, line in enumerate(lines):
        if i > 0 and line.strip() == '':
            insert_pos = i + 1
            break
    
    # Build new prompt
    new_prompt = (
        '\n'.join(lines[:insert_pos]) +
        '\n\n' + context + '\n\n' +
        '\n'.join(lines[insert_pos:])
    )
    
    return new_prompt

def get_latest_analysis(extraction_dir: Path) -> Optional[Path]:
    """
    Find latest analysis.json from extraction directory
    
    Returns path to most recent analysis.json
    """
    
    extraction_dir = Path(extraction_dir)
    if not extraction_dir.exists():
        return None
    
    # Find all analysis.json files
    analysis_files = sorted(extraction_dir.glob('*/analysis.json'), reverse=True)
    
    return analysis_files[0] if analysis_files else None

if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Context injection for main agent')
    parser.add_argument('--index', type=Path, required=True, help='Path to qa-index.json')
    parser.add_argument('--session', required=True, help='Session ID')
    parser.add_argument('--extraction-dir', type=Path, help='Extraction directory for analysis')
    parser.add_argument('--qa-window', type=int, default=5, help='Recent QA window')
    parser.add_argument('--output', type=Path, help='Save context to file')
    
    args = parser.parse_args()
    
    # Get latest analysis if dir provided
    analysis_file = None
    if args.extraction_dir:
        analysis_file = get_latest_analysis(args.extraction_dir)
    
    # Build context
    context = build_full_context(
        args.index,
        args.session,
        analysis_file,
        args.qa_window
    )
    
    if context:
        print(context)
        
        if args.output:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            with open(args.output, 'w', encoding='utf-8') as f:
                f.write(context)
            print(f"\n📄 Context saved to {args.output}")
