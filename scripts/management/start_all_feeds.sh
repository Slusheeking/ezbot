#!/bin/bash
#
# EzBot Feed Startup Script
# Orchestrated startup of all data feeds with proper staggering and health checks
#

set -euo pipefail

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="/home/ezb0t/ezbot"
PYTHON_CMD="/usr/bin/python3"
FEED_MANAGER="${PROJECT_ROOT}/scripts/management/feed_manager.py"
LOG_FILE="/home/ezb0t/ezbot/logs/startup.log"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging function
log() {
    echo -e "${BLUE}[$(date '+%Y-%m-%d %H:%M:%S')]${NC} $1" | tee -a "$LOG_FILE"
}

error() {
    echo -e "${RED}[$(date '+%Y-%m-%d %H:%M:%S')] ERROR:${NC} $1" | tee -a "$LOG_FILE"
}

success() {
    echo -e "${GREEN}[$(date '+%Y-%m-%d %H:%M:%S')] SUCCESS:${NC} $1" | tee -a "$LOG_FILE"
}

warning() {
    echo -e "${YELLOW}[$(date '+%Y-%m-%d %H:%M:%S')] WARNING:${NC} $1" | tee -a "$LOG_FILE"
}

# Check prerequisites
check_prerequisites() {
    log "Checking prerequisites..."

    # Check if QuestDB is running
    if ! systemctl is-active --quiet questdb.service; then
        warning "QuestDB service is not running. Attempting to start..."
        sudo systemctl start questdb.service
        sleep 5

        if ! systemctl is-active --quiet questdb.service; then
            error "Failed to start QuestDB service"
            return 1
        fi
    fi

    # Check Python environment
    if ! command -v "$PYTHON_CMD" >/dev/null 2>&1; then
        error "Python3 not found at $PYTHON_CMD"
        return 1
    fi

    # Check project directory
    if [ ! -d "$PROJECT_ROOT" ]; then
        error "Project root directory not found: $PROJECT_ROOT"
        return 1
    fi

    # Check feed manager script
    if [ ! -f "$FEED_MANAGER" ]; then
        error "Feed manager script not found: $FEED_MANAGER"
        return 1
    fi

    success "Prerequisites check completed"
    return 0
}

# Discover feeds
discover_feeds() {
    log "Discovering feeds..."

    cd "$PROJECT_ROOT"
    if $PYTHON_CMD "$FEED_MANAGER" discover > /tmp/ezbot_discovery.json 2>&1; then
        local discovered=$(jq -r '.discovered | length' /tmp/ezbot_discovery.json 2>/dev/null || echo "unknown")
        local registered=$(jq -r '.registered | length' /tmp/ezbot_discovery.json 2>/dev/null || echo "unknown")
        success "Feed discovery completed: $discovered discovered, $registered registered"
        return 0
    else
        error "Feed discovery failed"
        cat /tmp/ezbot_discovery.json
        return 1
    fi
}

# Start feeds by priority
start_feeds_by_priority() {
    log "Starting feeds by priority..."

    local priorities=("critical" "high" "medium" "low")
    local stagger_delays=(10 15 20 30)

    for i in "${!priorities[@]}"; do
        local priority="${priorities[$i]}"
        local delay="${stagger_delays[$i]}"

        log "Starting $priority priority feeds with ${delay}s stagger..."

        cd "$PROJECT_ROOT"
        if $PYTHON_CMD "$FEED_MANAGER" start "$priority" --stagger "$delay" > /tmp/ezbot_start_${priority}.json 2>&1; then
            success "$priority priority feeds started"
        else
            warning "Some $priority priority feeds failed to start"
            cat /tmp/ezbot_start_${priority}.json
        fi

        # Wait between priority groups
        if [ $i -lt $((${#priorities[@]} - 1)) ]; then
            log "Waiting ${delay}s before starting next priority group..."
            sleep "$delay"
        fi
    done
}

# Health check
perform_health_check() {
    log "Performing system health check..."

    cd "$PROJECT_ROOT"
    if $PYTHON_CMD "$FEED_MANAGER" health > /tmp/ezbot_health.json 2>&1; then
        local total_feeds=$(jq -r '.registry_metrics.total_feeds' /tmp/ezbot_health.json 2>/dev/null || echo "0")
        local running_feeds=$(jq -r '.registry_metrics.running_feeds' /tmp/ezbot_health.json 2>/dev/null || echo "0")
        local healthy_feeds=$(jq -r '.registry_metrics.healthy_feeds' /tmp/ezbot_health.json 2>/dev/null || echo "0")

        success "Health check completed: $running_feeds/$total_feeds running, $healthy_feeds healthy"

        # Display feed status summary
        log "Feed Status Summary:"
        $PYTHON_CMD "$FEED_MANAGER" list | jq -r '.[] | "\(.name): \(.status)"' | while read -r line; do
            log "  $line"
        done

        return 0
    else
        error "Health check failed"
        cat /tmp/ezbot_health.json
        return 1
    fi
}

# Monitor startup
monitor_startup() {
    log "Monitoring startup progress..."

    local max_attempts=30
    local attempt=1

    while [ $attempt -le $max_attempts ]; do
        log "Startup check $attempt/$max_attempts..."

        cd "$PROJECT_ROOT"
        if $PYTHON_CMD "$FEED_MANAGER" health > /tmp/ezbot_monitor.json 2>&1; then
            local running_feeds=$(jq -r '.registry_metrics.running_feeds' /tmp/ezbot_monitor.json 2>/dev/null || echo "0")
            local total_feeds=$(jq -r '.registry_metrics.total_feeds' /tmp/ezbot_monitor.json 2>/dev/null || echo "1")

            if [ "$running_feeds" -gt 0 ] && [ "$running_feeds" -eq "$total_feeds" ]; then
                success "All feeds started successfully ($running_feeds/$total_feeds)"
                return 0
            fi

            log "Startup in progress: $running_feeds/$total_feeds feeds running"
        fi

        sleep 10
        ((attempt++))
    done

    warning "Startup monitoring timeout - not all feeds may be running"
    return 1
}

# Main execution
main() {
    log "Starting EzBot Feed System..."

    # Create log directory
    mkdir -p "$(dirname "$LOG_FILE")"

    # Check prerequisites
    if ! check_prerequisites; then
        error "Prerequisites check failed"
        exit 1
    fi

    # Discover feeds
    if ! discover_feeds; then
        error "Feed discovery failed"
        exit 1
    fi

    # Start feeds
    start_feeds_by_priority

    # Monitor startup
    monitor_startup

    # Final health check
    if perform_health_check; then
        success "EzBot Feed System startup completed successfully"
    else
        warning "EzBot Feed System started with some issues"
    fi

    log "Startup script completed"
}

# Signal handlers
trap 'error "Startup interrupted"; exit 130' INT
trap 'error "Startup terminated"; exit 143' TERM

# Execute main function
main "$@"