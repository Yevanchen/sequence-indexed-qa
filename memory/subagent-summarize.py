#!/usr/bin/env python3
"""
Sub-Agent Summarizer - Browse extracted conversations and report

This script is designed to be called by the main agent via sessions_spawn.
It:
1. Reads extracted conversation files
2. Analyzes questions and answers
3. Generates summary report
4. Updates memory system with significance adjustments

Usage (from main agent):
  sessions_spawn(
    task='Analyze conversations from /path/to/extraction',
    agentId='summarizer'
  )
"""

import json
import sys
from pathlib import Path
from typing import List, Dict

def read_extracted_files(extraction_dir: Path) -> Dict:
    """Read all extracted Q-A files from directory"""
    
    extraction_dir = Path(extraction_dir)
    if not extraction_dir.exists():
        return {'error': f'Directory not found: {extraction_dir}'}
    
    # Load metadata
    metadata_file = list(extraction_dir.glob('*-qa.json'))
    if not metadata_file:
        return {'error': f'No metadata file found in {extraction_dir}'}
    
    with open(metadata_file[0], 'r', encoding='utf-8') as f:
        metadata = json.load(f)
    
    # Read question files
    questions_dir = extraction_dir / 'questions'
    questions = {}
    if questions_dir.exists():
        for q_file in sorted(questions_dir.glob('*.txt')):
            with open(q_file, 'r', encoding='utf-8') as f:
                questions[q_file.name] = f.read()
    
    # Read answer files
    answers_dir = extraction_dir / 'answers'
    answers = {}
    if answers_dir.exists():
        for a_file in sorted(answers_dir.glob('*.txt')):
            with open(a_file, 'r', encoding='utf-8') as f:
                answers[a_file.name] = f.read()
    
    return {
        'metadata': metadata,
        'questions': questions,
        'answers': answers,
        'question_count': len(questions),
        'answer_count': len(answers)
    }

def analyze_conversations(data: Dict) -> Dict:
    """
    Analyze extracted conversations and generate insights
    
    Returns summary of:
    - Topics discussed
    - Answer quality assessment
    - Recommendations for memory significance
    - Any patterns or issues
    """
    
    if 'error' in data:
        return data
    
    metadata = data['metadata']
    analysis = {
        'period': metadata.get('cutoff_time'),
        'total_questions': len(data['questions']),
        'total_answers': len(data['answers']),
        'topics': {},
        'high_significance_answers': [],
        'low_significance_answers': [],
        'missing_answers': [],
        'patterns': []
    }
    
    # Analyze from metadata
    if 'questions' in metadata and isinstance(metadata['questions'], list):
        for q in metadata['questions']:
            # Count topics
            for topic in q.get('topics', []):
                analysis['topics'][topic] = analysis['topics'].get(topic, 0) + 1
    
    if 'answers' in metadata and isinstance(metadata['answers'], list):
        for a in metadata['answers']:
            sig = a.get('significance', 0)
            if sig >= 0.85:
                analysis['high_significance_answers'].append({
                    'seq': a['seq'],
                    'q_preview': a['q'],
                    'significance': sig,
                    'tokens': a['a_tokens']
                })
            elif sig < 0.5:
                analysis['low_significance_answers'].append({
                    'seq': a['seq'],
                    'q_preview': a['q'],
                    'significance': sig
                })
    
    # Find questions without answers
    if 'questions' in metadata:
        q_seqs = {q['seq'] for q in metadata['questions']}
        a_seqs = {a['seq'] for a in metadata.get('answers', [])}
        missing = q_seqs - a_seqs
        if missing:
            analysis['missing_answers'] = sorted(list(missing))
    
    # Detect patterns
    if analysis['total_answers'] > 5:
        avg_significance = sum(
            a.get('significance', 0) 
            for a in metadata.get('answers', [])
        ) / len(metadata.get('answers', []))
        if avg_significance > 0.8:
            analysis['patterns'].append("High quality conversation period")
        if avg_significance < 0.5:
            analysis['patterns'].append("Low quality/off-topic conversation")
    
    if analysis['topics']:
        top_topic = max(analysis['topics'], key=analysis['topics'].get)
        analysis['patterns'].append(f"Focus topic: {top_topic}")
    
    return analysis

def generate_report(analysis: Dict) -> str:
    """Generate human-readable report for main agent"""
    
    if 'error' in analysis:
        return f"❌ Error: {analysis['error']}"
    
    report = f"""
📊 CONVERSATION ANALYSIS REPORT
================================

⏰ Period: {analysis['period']}

📈 Statistics:
   Questions: {analysis['total_questions']}
   Answers: {analysis['total_answers']}
   Topics: {len(analysis['topics'])}

🏆 High Quality Answers (sig > 0.85):
"""
    
    for ans in analysis['high_significance_answers'][:5]:
        report += f"\n   [{ans['seq']}] {ans['q_preview'][:60]}... (sig: {ans['significance']:.2f})"
    
    if analysis['topics']:
        report += "\n\n📌 Topics Discussed:"
        for topic, count in sorted(analysis['topics'].items(), key=lambda x: -x[1])[:5]:
            report += f"\n   {topic}: {count} question(s)"
    
    if analysis['missing_answers']:
        report += f"\n\n⚠️  Questions without answers: {len(analysis['missing_answers'])}"
        for seq in analysis['missing_answers'][:3]:
            report += f"\n   [Seq {seq}]"
    
    if analysis['patterns']:
        report += "\n\n🔍 Patterns:"
        for pattern in analysis['patterns']:
            report += f"\n   - {pattern}"
    
    report += "\n\n✅ Analysis complete. Ready for memory system update."
    
    return report

if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Sub-agent: Summarize extracted conversations')
    parser.add_argument('extraction_dir', type=Path, help='Directory with extracted conversations')
    
    args = parser.parse_args()
    
    # Read files
    data = read_extracted_files(args.extraction_dir)
    
    # Analyze
    analysis = analyze_conversations(data)
    
    # Generate report
    report = generate_report(analysis)
    print(report)
    
    # Save analysis as JSON for main agent
    analysis_file = Path(args.extraction_dir) / 'analysis.json'
    with open(analysis_file, 'w', encoding='utf-8') as f:
        json.dump(analysis, f, ensure_ascii=False, indent=2)
    
    print(f"\n📄 Analysis saved to {analysis_file}")
