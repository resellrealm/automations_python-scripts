#!/bin/bash
# Paperclip Adapter for Claude CLI
# Usage: ./adapter.sh "<task_json>"

set -e

# Config
CLAUDE_BIN="${PAPERCLIP_CLAUDE_CLI_PATH:-claude}"
WORK_DIR="${PAPERCLIP_WORK_DIR:-/tmp/paperclip-claude-work}"
LOG_FILE="${PAPERCLIP_LOG_FILE:-/var/log/paperclip-claude.log}"

# Parse input
TASK_JSON="$1"
TASK_ID=$(echo "$TASK_JSON" | jq -r '.task_id // "unknown"')
TASK_TYPE=$(echo "$TASK_JSON" | jq -r '.task_type // "general"')
PROMPT=$(echo "$TASK_JSON" | jq -r '.prompt // empty')
FILE_PATH=$(echo "$TASK_JSON" | jq -r '.file_path // empty')
PROJECT_DIR=$(echo "$TASK_JSON" | jq -r '.project_dir // empty')

# Logging
log() {
    echo "[$(date -Iseconds)] [Claude:$TASK_ID] $*" >> "$LOG_FILE"
}

log "Starting task: $TASK_TYPE"

# Create work directory
mkdir -p "$WORK_DIR/$TASK_ID"
cd "$WORK_DIR/$TASK_ID"

# Handle different task types
case "$TASK_TYPE" in
    "architecture")
        log "Designing architecture"
        RESULT=$(echo "$PROMPT" | $CLAUDE_BIN -p "You are a system architect. Design a clean, scalable architecture. Be concise but thorough." 2>> "$LOG_FILE")
        ;;
    
    "frontend")
        if [ -n "$FILE_PATH" ]; then
            log "Building frontend component: $FILE_PATH"
            mkdir -p "$(dirname "$FILE_PATH")"
            echo "$PROMPT" | $CLAUDE_BIN -p "You are an expert React/Next.js developer. Generate clean, modern code with proper TypeScript types. Output ONLY the code, no markdown fences." > "$FILE_PATH" 2>> "$LOG_FILE"
            RESULT=$(cat "$FILE_PATH")
        else
            RESULT=$(echo "$PROMPT" | $CLAUDE_BIN -p "You are an expert React/Next.js developer. Output ONLY the code, no markdown fences." 2>> "$LOG_FILE")
        fi
        ;;
    
    "design")
        log "Making design decisions"
        RESULT=$(echo "$PROMPT" | $CLAUDE_BIN -p "You are a UI/UX designer. Provide design recommendations with rationale. Consider accessibility and modern design patterns." 2>> "$LOG_FILE")
        ;;
    
    "api")
        log "Designing API"
        RESULT=$(echo "$PROMPT" | $CLAUDE_BIN -p "You are a backend API designer. Design RESTful or GraphQL endpoints with clear specs. Include request/response examples." 2>> "$LOG_FILE")
        ;;
    
    "database")
        log "Designing database schema"
        RESULT=$(echo "$PROMPT" | $CLAUDE_BIN -p "You are a database architect. Design efficient schemas with proper indexing and relationships. Use PostgreSQL best practices." 2>> "$LOG_FILE")
        ;;
    
    "review")
        if [ -n "$PROJECT_DIR" ]; then
            log "Reviewing project at: $PROJECT_DIR"
            PROJECT_TREE=$(find "$PROJECT_DIR" -type f \( -name "*.ts" -o -name "*.tsx" -o -name "*.js" -o -name "*.jsx" -o -name "*.py" \) 2>/dev/null | head -30)
            RESULT=$(echo -e "Review this project structure:\n\n$PROJECT_TREE\n\n$PROMPT" | $CLAUDE_BIN -p "You are a senior code reviewer. Focus on architecture, security, and maintainability." 2>> "$LOG_FILE")
        else
            RESULT=$(echo "$PROMPT" | $CLAUDE_BIN -p "You are a senior code reviewer." 2>> "$LOG_FILE")
        fi
        ;;
    
    "planning")
        log "Creating project plan"
        RESULT=$(echo "$PROMPT" | $CLAUDE_BIN -p "You are a technical project manager. Break down tasks into actionable items with estimates. Consider dependencies." 2>> "$LOG_FILE")
        ;;
    
    *)
        log "General task"
        RESULT=$(echo "$PROMPT" | $CLAUDE_BIN 2>> "$LOG_FILE")
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
