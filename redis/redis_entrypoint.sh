#!/bin/bash

# Function to create Redis snapshot
create_redis_snapshot() {
    echo "Creating Redis snapshot..."
    redis-cli SAVE
    echo "Redis snapshot created."
}

# Function to load Redis snapshot if available
load_redis_snapshot() {
    if [ -f "/data/dump.rdb" ]; then
        echo "Loading Redis snapshot..."
        cp /data/dump.rdb /usr/local/var/lib/redis/dump.rdb
        echo "Redis snapshot loaded."
    else
        echo "No Redis snapshot found."
    fi
}

# Trap SIGTERM signal and call create_redis_snapshot function before shutting down
trap 'create_redis_snapshot; exit' SIGTERM

# Load Redis snapshot if available
load_redis_snapshot

# Start Redis server
exec redis-server etc/redis/redis.conf