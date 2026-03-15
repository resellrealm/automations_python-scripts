#!/bin/bash
# PaperclipAI VPS Installation Script
# Run this on your VPS to set everything up

set -e

PAPERCLIP_DIR="$HOME/.paperclip"
PROJECT_DIR="$HOME/python-scripts/paperclip_setup"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

log() {
    echo -e "${GREEN}[PAPERCLIP]${NC} $1"
}

warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1"
    exit 1
}

# Check prerequisites
check_prereqs() {
    log "Checking prerequisites..."
    
    command -v node >/dev/null 2>&1 || error "Node.js is required but not installed"
    command -v npm >/dev/null 2>&1 || error "npm is required but not installed"
    command -v kimi >/dev/null 2>&1 || warn "Kimi CLI not found - install it first"
    command -v claude >/dev/null 2>&1 || warn "Claude CLI not found - install it first"
    
    log "Prerequisites check complete"
}

# Install Paperclip
install_paperclip() {
    log "Installing Paperclip..."
    
    # Run Paperclip onboard
    npx paperclipai onboard --yes
    
    log "Paperclip installed to $PAPERCLIP_DIR"
}

# Setup adapters
setup_adapters() {
    log "Setting up Kimi and Claude adapters..."
    
    mkdir -p "$PAPERCLIP_DIR/agents"
    
    # Copy adapters
    cp -r "$PROJECT_DIR/adapters/kimi-cli" "$PAPERCLIP_DIR/agents/"
    cp -r "$PROJECT_DIR/adapters/claude-cli" "$PAPERCLIP_DIR/agents/"
    
    # Make executable
    chmod +x "$PAPERCLIP_DIR/agents/kimi-cli/adapter.sh"
    chmod +x "$PAPERCLIP_DIR/agents/claude-cli/adapter.sh"
    
    # Install jq if not present
    if ! command -v jq >/dev/null 2>&1; then
        log "Installing jq..."
        sudo apt-get update && sudo apt-get install -y jq
    fi
    
    log "Adapters configured"
}

# Setup company config
setup_company() {
    log "Setting up Dev Agency company..."
    
    mkdir -p "$PAPERCLIP_DIR/companies/autonomous-app-studio"
    cp "$PROJECT_DIR/company_configs/dev_agency.json" "$PAPERCLIP_DIR/companies/autonomous-app-studio/config.json"
    
    log "Company 'Autonomous App Studio' created"
}

# Setup skills
setup_skills() {
    log "Installing skills..."
    
    mkdir -p "$PAPERCLIP_DIR/skills"
    cp -r "$PROJECT_DIR/skills/"* "$PAPERCLIP_DIR/skills/"
    
    log "Skills installed"
}

# Setup logging
setup_logging() {
    log "Setting up logging..."
    
    sudo mkdir -p /var/log/paperclip
    sudo touch /var/log/paperclip/paperclip.log
    sudo touch /var/log/paperclip/paperclip-error.log
    sudo touch /var/log/paperclip/paperclip-kimi.log
    sudo touch /var/log/paperclip/paperclip-claude.log
    sudo chown -R "$USER:$USER" /var/log/paperclip
    
    log "Logging configured"
}

# Setup systemd service
setup_systemd() {
    log "Setting up systemd service..."
    
    # Copy service file
    sudo cp "$PROJECT_DIR/scripts/paperclip.service" /etc/systemd/system/paperclip@.service
    sudo systemctl daemon-reload
    
    log "Systemd service created"
    log "Start with: sudo systemctl start paperclip@$USER"
    log "Enable on boot: sudo systemctl enable paperclip@$USER"
}

# Create environment file
create_env() {
    log "Creating environment configuration..."
    
    cat > "$PAPERCLIP_DIR/.env" <<EOF
# Paperclip Configuration
PAPERCLIP_PORT=3000
PAPERCLIP_API_PORT=3001
PAPERCLIP_DATA_DIR=$PAPERCLIP_DIR/data
PAPERCLIP_LOG_LEVEL=info

# CLI Paths
PAPERCLIP_KIMI_CLI_PATH=$(which kimi)
PAPERCLIP_CLAUDE_CLI_PATH=$(which claude)
PAPERCLIP_WORK_DIR=/tmp/paperclip-work
PAPERCLIP_LOG_FILE=/var/log/paperclip/paperclip.log

# Agent Budgets (USD)
PAPERCLIP_DEFAULT_BUDGET=30
PAPERCLIP_BUDGET_WARNING=0.8
EOF
    
    log "Environment file created at $PAPERCLIP_DIR/.env"
}

# Create helper scripts
create_helpers() {
    log "Creating helper scripts..."
    
    mkdir -p "$HOME/bin"
    
    # Paperclip control script
    cat > "$HOME/bin/paperclip-ctl" <<'EOF'
#!/bin/bash
# Paperclip control helper

case "$1" in
    start)
        sudo systemctl start paperclip@$USER
        echo "Paperclip started"
        ;;
    stop)
        sudo systemctl stop paperclip@$USER
        echo "Paperclip stopped"
        ;;
    restart)
        sudo systemctl restart paperclip@$USER
        echo "Paperclip restarted"
        ;;
    status)
        sudo systemctl status paperclip@$USER
        ;;
    logs)
        sudo tail -f /var/log/paperclip/paperclip.log
        ;;
    dashboard)
        echo "Dashboard available at: http://localhost:3000"
        echo "If on remote VPS, run: ssh -L 3000:localhost:3000 your-vps"
        ;;
    ticket)
        # Create a new ticket via CLI
        shift
        curl -X POST http://localhost:3001/api/tickets \
            -H "Content-Type: application/json" \
            -d "{\"title\":\"$1\",\"description\":\"${2:-}\"}"
        ;;
    *)
        echo "Usage: paperclip-ctl {start|stop|restart|status|logs|dashboard|ticket 'title'}"
        exit 1
        ;;
esac
EOF
    chmod +x "$HOME/bin/paperclip-ctl"
    
    log "Helper script created: paperclip-ctl"
}

# Main installation
main() {
    log "Starting PaperclipAI installation..."
    
    check_prereqs
    install_paperclip
    setup_adapters
    setup_company
    setup_skills
    setup_logging
    setup_systemd
    create_env
    create_helpers
    
    log ""
    log "========================================"
    log "Installation Complete!"
    log "========================================"
    log ""
    log "Next steps:"
    log "1. Start Paperclip: paperclip-ctl start"
    log "2. Check status: paperclip-ctl status"
    log "3. View logs: paperclip-ctl logs"
    log "4. Open dashboard: paperclip-ctl dashboard"
    log ""
    log "To access dashboard from your Mac:"
    log "  ssh -L 3000:localhost:3000 your-vps"
    log "  Then open http://localhost:3000"
    log ""
    log "Create your first app:"
    log "  paperclip-ctl ticket 'Build a todo app with projects'"
    log ""
}

main "$@"
