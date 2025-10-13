#!/bin/bash
#
# CodeRabbit Continuous Monitoring Agent
#
# Automatically runs CodeRabbit review on every git commit
# Runs as a background daemon process
#
# Usage:
#   ./coderabbit-monitor.sh start   # Start monitoring
#   ./coderabbit-monitor.sh stop    # Stop monitoring
#   ./coderabbit-monitor.sh status  # Check status

set -euo pipefail

REPO_DIR="/home/agent0/hx-citadel-ansible"
LOG_FILE="/tmp/coderabbit-monitor.log"
PID_FILE="/tmp/coderabbit-monitor.pid"
LAST_COMMIT_FILE="/tmp/coderabbit-last-commit"

# Add coderabbit to PATH
export PATH="$HOME/.local/bin:$PATH"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*" | tee -a "$LOG_FILE"
}

get_current_commit() {
    cd "$REPO_DIR"
    git rev-parse HEAD
}

run_coderabbit_review() {
    local commit=$1
    log "🔍 Running CodeRabbit review for commit: ${commit:0:7}"
    
    cd "$REPO_DIR"
    
    # Run CodeRabbit in prompt-only mode
    if coderabbit --prompt-only --base-commit "$(git rev-parse HEAD~1)" 2>&1 | tee -a "$LOG_FILE"; then
        log "✅ CodeRabbit review completed for ${commit:0:7}"
    else
        log "⚠️  CodeRabbit review had warnings for ${commit:0:7}"
    fi
}

monitor_loop() {
    log "🚀 Starting CodeRabbit monitoring daemon"
    log "📁 Repository: $REPO_DIR"
    log "📝 Log file: $LOG_FILE"
    
    # Initialize last commit
    get_current_commit > "$LAST_COMMIT_FILE"
    local last_commit=$(cat "$LAST_COMMIT_FILE")
    log "📌 Initial commit: ${last_commit:0:7}"
    
    while true; do
        sleep 10  # Check every 10 seconds
        
        current_commit=$(get_current_commit)
        
        if [[ "$current_commit" != "$last_commit" ]]; then
            log "🆕 New commit detected: ${current_commit:0:7}"
            
            # Run CodeRabbit review
            run_coderabbit_review "$current_commit"
            
            # Update last commit
            echo "$current_commit" > "$LAST_COMMIT_FILE"
            last_commit=$current_commit
        fi
    done
}

start_daemon() {
    if [[ -f "$PID_FILE" ]] && kill -0 $(cat "$PID_FILE") 2>/dev/null; then
        log "⚠️  CodeRabbit monitor already running (PID: $(cat "$PID_FILE"))"
        exit 1
    fi
    
    log "🚀 Starting CodeRabbit monitor daemon..."
    
    # Start monitor in background
    nohup bash -c "$(declare -f log get_current_commit run_coderabbit_review monitor_loop); monitor_loop" >> "$LOG_FILE" 2>&1 &
    
    local pid=$!
    echo $pid > "$PID_FILE"
    
    log "✅ CodeRabbit monitor started (PID: $pid)"
    log "📝 Logs: tail -f $LOG_FILE"
}

stop_daemon() {
    if [[ ! -f "$PID_FILE" ]]; then
        log "⚠️  CodeRabbit monitor not running"
        exit 1
    fi
    
    local pid=$(cat "$PID_FILE")
    
    if kill -0 "$pid" 2>/dev/null; then
        log "🛑 Stopping CodeRabbit monitor (PID: $pid)"
        kill "$pid"
        rm -f "$PID_FILE"
        log "✅ CodeRabbit monitor stopped"
    else
        log "⚠️  CodeRabbit monitor not running (stale PID file)"
        rm -f "$PID_FILE"
    fi
}

status_daemon() {
    if [[ -f "$PID_FILE" ]]; then
        local pid=$(cat "$PID_FILE")
        if kill -0 "$pid" 2>/dev/null; then
            log "✅ CodeRabbit monitor running (PID: $pid)"
            log "📝 Log file: $LOG_FILE"
            log "📌 Last lines:"
            tail -5 "$LOG_FILE"
        else
            log "❌ CodeRabbit monitor not running (stale PID)"
            rm -f "$PID_FILE"
        fi
    else
        log "❌ CodeRabbit monitor not running"
    fi
}

# Main
case "${1:-}" in
    start)
        start_daemon
        ;;
    stop)
        stop_daemon
        ;;
    status)
        status_daemon
        ;;
    *)
        echo "Usage: $0 {start|stop|status}"
        exit 1
        ;;
esac

