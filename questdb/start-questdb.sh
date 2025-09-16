#!/bin/bash

# QuestDB startup script
QUESTDB_DIR="/home/ezb0t/ezbot/questdb"
PIDFILE="$QUESTDB_DIR/questdb.pid"
LOGFILE="$QUESTDB_DIR/logs/questdb.log"

# Check if QuestDB is already running
if [ -f "$PIDFILE" ] && kill -0 $(cat "$PIDFILE") 2>/dev/null; then
    echo "QuestDB is already running (PID: $(cat $PIDFILE))"
    exit 0
fi

# Ensure directories exist
mkdir -p "$QUESTDB_DIR/logs"
mkdir -p "$QUESTDB_DIR/data"

# Start QuestDB
cd "$QUESTDB_DIR"
export JAVA_HOME=/usr/lib/jvm/java-11-openjdk-amd64
export PATH=$JAVA_HOME/bin:$PATH

nohup java -cp questdb.jar io.questdb.ServerMain -d "$QUESTDB_DIR" > "$LOGFILE" 2>&1 &
echo $! > "$PIDFILE"

echo "QuestDB started (PID: $!)"
echo "Web Console: http://localhost:9000"
echo "Log file: $LOGFILE"