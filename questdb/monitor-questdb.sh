#!/bin/bash

# QuestDB Monitor Script - keeps QuestDB running 24/7
QUESTDB_DIR="/home/ezb0t/ezbot/questdb"
PIDFILE="$QUESTDB_DIR/questdb.pid"
LOGFILE="$QUESTDB_DIR/logs/monitor.log"

# Create log directory
mkdir -p "$QUESTDB_DIR/logs"

# Function to check if QuestDB is healthy
check_questdb() {
    # Check if process is running and responding to HTTP
    if [ -f "$PIDFILE" ] && kill -0 $(cat "$PIDFILE") 2>/dev/null; then
        if curl -s --max-time 5 http://localhost:9000/status > /dev/null 2>&1; then
            return 0  # QuestDB is healthy
        fi
    fi
    return 1  # QuestDB is not healthy
}

# Function to start QuestDB
start_questdb() {
    echo "$(date): Starting QuestDB..." | tee -a "$LOGFILE"

    # Kill any stale processes
    pkill -f questdb 2>/dev/null || true
    rm -f "$PIDFILE"
    sleep 2

    # Start QuestDB
    cd "$QUESTDB_DIR"
    export JAVA_HOME=/usr/lib/jvm/java-11-openjdk-amd64
    export PATH=$JAVA_HOME/bin:$PATH

    nohup java -cp questdb.jar io.questdb.ServerMain -d "$QUESTDB_DIR" > logs/questdb.log 2>&1 &
    echo $! > "$PIDFILE"

    echo "$(date): QuestDB started with PID $!" | tee -a "$LOGFILE"

    # Wait for QuestDB to start
    sleep 5
    for i in {1..12}; do
        if curl -s --max-time 5 http://localhost:9000/status > /dev/null 2>&1; then
            echo "$(date): QuestDB is ready!" | tee -a "$LOGFILE"
            return 0
        fi
        sleep 5
    done
    echo "$(date): WARNING: QuestDB may not have started correctly" | tee -a "$LOGFILE"
}

# Initial check and start if needed
if ! check_questdb; then
    start_questdb
fi

# Main monitoring loop
while true; do
    if ! check_questdb; then
        echo "$(date): QuestDB is down! Restarting..." | tee -a "$LOGFILE"
        start_questdb
    else
        echo "$(date): QuestDB is healthy" >> "$LOGFILE"
    fi

    # Check every 30 seconds
    sleep 30
done