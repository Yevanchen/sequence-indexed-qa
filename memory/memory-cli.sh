#!/bin/bash

# Memory CLI - Manage QA-indexed memory system
# Usage: ./memory-cli.sh [command] [args]

INDEX_FILE="/home/node/.openclaw/workspace/memory/qa-index.json"

show_help() {
  cat << 'EOF'
Memory CLI - QA-Indexed Memory Management

Commands:
  list-topics                 - Show all indexed topics
  query-topic <topic>         - Get all Q-A pairs for a topic
  query-recent [n]            - Get last N Q-A pairs (default: 5)
  query-hash <hash>           - Look up Q by semantic hash
  set-significance <seq> <val>- Update answer significance (0-1)
  dump-session <session_id>   - Show all Q-A for a session
  stats                       - Show memory statistics
  help                        - Show this help

Examples:
  ./memory-cli.sh list-topics
  ./memory-cli.sh query-topic memory_design
  ./memory-cli.sh query-recent 10
  ./memory-cli.sh set-significance 2 0.9
EOF
}

# Check if jq is available
if ! command -v jq &> /dev/null; then
  echo "Error: jq is required but not installed. Install it with: apt install jq"
  exit 1
fi

# Check if index file exists
if [ ! -f "$INDEX_FILE" ]; then
  echo "Error: Index file not found at $INDEX_FILE"
  exit 1
fi

case "$1" in
  list-topics)
    jq -r '.index.by_topic | keys | .[]' "$INDEX_FILE" | sort
    ;;
  
  query-topic)
    if [ -z "$2" ]; then
      echo "Error: topic name required"
      exit 1
    fi
    topic="$2"
    session_seq=$(jq -r ".index.by_topic[\"$topic\"][0] | \"\(.session)|\(.seq)\"" "$INDEX_FILE")
    if [ "$session_seq" = "null|null" ]; then
      echo "Topic not found: $topic"
      exit 1
    fi
    
    # Extract session and seq
    session=$(echo "$session_seq" | cut -d'|' -f1)
    
    # Print all Q-A pairs for this topic
    jq -r ".sessions[] | select(.session_id==\"$session\") | .qa_sequence[] | 
            select(.topic_tags[] == \"$topic\") | 
            \"[\(.seq)] Q: \(.q | .[0:100])\" + (if .a then \"\\nA (sig: \(.a_significance)): \(.a | .[0:150])...\\n\" else \"\\n\" end)" \
      "$INDEX_FILE"
    ;;
  
  query-recent)
    n=${2:-5}
    jq -r ".index.by_recency[:$n] as \$refs |
            .sessions[] | .qa_sequence[] as \$qa |
            select(\$refs[] | select(.seq == \$qa.seq)) |
            \"[\(.seq)] Q: \(.q | .[0:80])\" + (if .a then \"\\nA (sig: \(.a_significance)): \(.a | .[0:150])...\\n\" else \"\\n\" end)" \
      "$INDEX_FILE"
    ;;
  
  query-hash)
    if [ -z "$2" ]; then
      echo "Error: hash required"
      exit 1
    fi
    hash="$2"
    jq -r ".index.by_semantic_hash[\"$hash\"] as \$ref |
            .sessions[] | select(.session_id == \$ref.session) | 
            .qa_sequence[] | select(.seq == \$ref.seq) |
            \"Q: \(.q)\\nA: \(.a)\\nSignificance: \(.a_significance)\\nTokens: \(.a_tokens)\"" \
      "$INDEX_FILE"
    ;;
  
  set-significance)
    if [ -z "$2" ] || [ -z "$3" ]; then
      echo "Error: usage: set-significance <seq> <value>"
      exit 1
    fi
    seq="$2"
    value="$3"
    
    # Validate value is between 0 and 1
    if ! echo "$value" | grep -qE '^(0(\.[0-9]+)?|1(\.0+)?)$'; then
      echo "Error: significance must be between 0 and 1"
      exit 1
    fi
    
    # Update significance in place
    jq ".sessions[].qa_sequence[] |= (if .seq == $seq then .a_significance = $value else . end)" \
      "$INDEX_FILE" > "$INDEX_FILE.tmp" && mv "$INDEX_FILE.tmp" "$INDEX_FILE"
    
    echo "Updated sequence $seq with significance $value"
    ;;
  
  dump-session)
    if [ -z "$2" ]; then
      echo "Error: session_id required"
      exit 1
    fi
    session="$2"
    jq -r ".sessions[] | select(.session_id==\"$session\") | 
            .qa_sequence[] |
            \"[\(.seq)] [\(.timestamp)] Q: \(.q | .[0:80])\" + 
            (if .a then \"\\n    A (tokens: \(.a_tokens), sig: \(.a_significance)): \(.a | .[0:200])...\\n\" else \"\\n\" end)" \
      "$INDEX_FILE"
    ;;
  
  stats)
    jq -r '.metadata | 
            "📊 Memory Statistics\\n" +
            "Total Q-A pairs: \(.total_qa_pairs)\\n" +
            "Stored answers: \(.stored_answers)\\n" +
            "Empty answers: \(.empty_answers_count)\\n" +
            "Average significance: \(.average_significance)\\n" +
            "Compression ratio: \(.compression_ratio)\\n" +
            "Last updated: \(.last_updated)\\n" +
            "Sessions: \(.sessions // 1)"' "$INDEX_FILE" 2>/dev/null || \
    jq '.metadata' "$INDEX_FILE"
    ;;
  
  help | "")
    show_help
    ;;
  
  *)
    echo "Unknown command: $1"
    show_help
    exit 1
    ;;
esac
