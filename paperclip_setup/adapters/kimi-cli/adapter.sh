#!/bin/bash
# Paperclip Adapter for Kimi CLI
# Usage: ./adapter.sh "<task_json>"

set -e

# Config
KIMI_BIN="${PAPERCLIP_KIMI_CLI_PATH:-kimi}"
WORK_DIR="${PAPERCLIP_WORK_DIR:-/tmp/paperclip-kimi-work}"
LOG_FILE="${PAPERCLIP_LOG_FILE:-/var/log/paperclip-kimi.log}"

# Parse input
TASK_JSON="$1"
TASK_ID=$(echo "$TASK_JSON" | jq -r '.task_id // "unknown"')
TASK_TYPE=$(echo "$TASK_JSON" | jq -r '.task_type // "general"')
PROMPT=$(echo "$TASK_JSON" | jq -r '.prompt // empty')
FILE_PATH=$(echo "$TASK_JSON" | jq -r '.file_path // empty')
PROJECT_DIR=$(echo "$TASK_JSON" | jq -r '.project_dir // empty')

# Logging
log() {
    echo "[$(date -Iseconds)] [Kimi:$TASK_ID] $*" >> "$LOG_FILE"
}

log "Starting task: $TASK_TYPE"

# Create work directory
mkdir -p "$WORK_DIR/$TASK_ID"
cd "$WORK_DIR/$TASK_ID"

# Handle different task types
case "$TASK_TYPE" in
    "code")
        # Generate code with Kimi
        if [ -n "$FILE_PATH" ]; then
            log "Generating code for $FILE_PATH"
            echo "$PROMPT" | $KIMI_BIN -c "Please generate the code and output ONLY the code, no markdown fences" > "$FILE_PATH" 2>> "$LOG_FILE"
            RESULT=$(cat "$FILE_PATH")
        else
            RESULT=$(echo "$PROMPT" | $KIMI_BIN -c "Please generate the code and output ONLY the code, no markdown fences" 2>> "$LOG_FILE")
        fi
        ;;
    
    "analyze")
        # Analyze code/files
        if [ -n "$FILE_PATH" ] && [ -f "$PROJECT_DIR/$FILE_PATH" ]; then
            log "Analyzing file: $FILE_PATH"
            FILE_CONTENT=$(cat "$PROJECT_DIR/$FILE_PATH")
            RESULT=$(echo -e "$PROMPT\n\nFile content:\n$FILE_CONTENT" | $KIMI_BIN 2>> "$LOG_FILE")
        else
            RESULT=$(echo "$PROMPT" | $KIMI_BIN 2>> "$LOG_FILE")
        fi
        ;;
    
    "fix")
        # Fix/improve code
        if [ -n "$FILE_PATH" ] && [ -f "$PROJECT_DIR/$FILE_PATH" ]; then
            log "Fixing file: $FILE_PATH"
            FILE_CONTENT=$(cat "$PROJECT_DIR/$FILE_PATH")
            RESULT=$(echo -e "$PROMPT\n\nCurrent code:\n\`\`\`\n$FILE_CONTENT\n\`\`\`" | $KIMI_BIN -c "Output ONLY the fixed code, no markdown fences" 2>> "$LOG_FILE")
        else
            RESULT=$(echo "$PROMPT" | $KIMI_BIN -c "Output ONLY the fixed code, no markdown fences" 2>> "$LOG_FILE")
        fi
        ;;
    
    "review")
        # Code review
        if [ -n "$PROJECT_DIR" ]; then
            log "Reviewing project at: $PROJECT_DIR"
            FILES=$(find "$PROJECT_DIR" -type f \( -name "*.py" -o -name "*.js" -o -name "*.ts" -o -name "*.tsx" -o -name "*.jsx" \) 2>/dev/null | head -20)
            FILE_CONTEXT=""
            for f in $FILES; do
                FILE_CONTEXT="$FILE_CONTEXT\n=== $f ===\n$(cat "$f" | head -50)"
            done
            RESULT=$(echo -e "$PROMPT\n\nFiles to review:\n$FILE_CONTEXT" | $KIMI_BIN 2>> "$LOG_FILE")
        else
            RESULT=$(echo "$PROMPT" | $KIMI_BIN 2>> "$LOG_FILE")
        fi
        ;;
    
    "shell")
        # Execute shell commands
        log "Executing shell command via Kimi"
        RESULT=$(echo "$PROMPT" | $KIMI_BIN 2>> "$LOG_FILE")
        ;;
    
    *)
        # General task
        log "General task"
        RESULT=$(echo "$PROMPT" | $KIMI_BIN 2>> "$LOG_FILE")
        ;;
esac

# Return JSON result
cat <<EOF
{
  "status": "success",
  "task_id": "$TASK_ID",
  "task_type": "$TASK_TYPE",
  "result": $(echo "$RESULT" | jq -Rs '.'),
  "timestamp": "$(date -Iseconds)"
}
EOF

log "Task completed: $TASK_ID"
