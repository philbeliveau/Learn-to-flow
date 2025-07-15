#!/usr/bin/env python3
"""
Redis Setup Script for EZBI Analytics
Configures Redis server with optimal settings for caching
"""

import os
import sys
import subprocess
import json
from pathlib import Path

def check_redis_installed():
    """Check if Redis is installed."""
    try:
        result = subprocess.run(['redis-server', '--version'], capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✓ Redis is installed: {result.stdout.strip()}")
            return True
        else:
            print("✗ Redis is not installed")
            return False
    except FileNotFoundError:
        print("✗ Redis is not installed")
        return False

def install_redis():
    """Install Redis based on the operating system."""
    import platform
    
    system = platform.system().lower()
    
    if system == "darwin":  # macOS
        print("Installing Redis on macOS using Homebrew...")
        try:
            subprocess.run(['brew', 'install', 'redis'], check=True)
            print("✓ Redis installed successfully")
            return True
        except subprocess.CalledProcessError:
            print("✗ Failed to install Redis via Homebrew")
            print("Please install Homebrew first: https://brew.sh/")
            return False
    
    elif system == "linux":
        print("Installing Redis on Linux...")
        try:
            # Try apt-get first (Ubuntu/Debian)
            subprocess.run(['sudo', 'apt-get', 'update'], check=True)
            subprocess.run(['sudo', 'apt-get', 'install', '-y', 'redis-server'], check=True)
            print("✓ Redis installed successfully")
            return True
        except subprocess.CalledProcessError:
            try:
                # Try yum (CentOS/RHEL)
                subprocess.run(['sudo', 'yum', 'install', '-y', 'redis'], check=True)
                print("✓ Redis installed successfully")
                return True
            except subprocess.CalledProcessError:
                print("✗ Failed to install Redis. Please install manually.")
                return False
    
    else:
        print(f"✗ Unsupported operating system: {system}")
        print("Please install Redis manually: https://redis.io/download")
        return False

def create_redis_config():
    """Create optimized Redis configuration."""
    config_content = """# Redis Configuration for EZBI Analytics
# Optimized for caching and performance

# Network
port 6379
bind 127.0.0.1
timeout 0
tcp-keepalive 60

# General
daemonize yes
supervised no
pidfile /var/run/redis/redis-server.pid
loglevel notice
logfile /var/log/redis/redis-server.log
databases 16

# Snapshotting (disabled for cache-only usage)
save ""

# Replication
# replicaof <masterip> <masterport>

# Security
requirepass your_secure_password_here
# rename-command FLUSHDB ""
# rename-command FLUSHALL ""

# Memory Management
maxmemory 256mb
maxmemory-policy allkeys-lru

# Lazy freeing
lazyfree-lazy-eviction yes
lazyfree-lazy-expire yes
lazyfree-lazy-server-del yes

# Append only file (disabled for cache-only usage)
appendonly no

# Slow log
slowlog-log-slower-than 10000
slowlog-max-len 128

# Latency monitoring
latency-monitor-threshold 100

# Client output buffer limits
client-output-buffer-limit normal 0 0 0
client-output-buffer-limit replica 256mb 64mb 60
client-output-buffer-limit pubsub 32mb 8mb 60

# TCP listen backlog
tcp-backlog 511

# Unix socket
# unixsocket /tmp/redis.sock
# unixsocketperm 700

# Slow log
slowlog-log-slower-than 10000
slowlog-max-len 128

# Compression
# rdbcompression yes
# rdbchecksum yes

# Stop writing on background save error
stop-writes-on-bgsave-error yes

# Hash threshold
hash-max-ziplist-entries 512
hash-max-ziplist-value 64

# List threshold
list-max-ziplist-size -2
list-compress-depth 0

# Set threshold
set-max-intset-entries 512

# Sorted set threshold
zset-max-ziplist-entries 128
zset-max-ziplist-value 64

# HyperLogLog threshold
hll-sparse-max-bytes 3000

# Streams threshold
stream-node-max-bytes 4096
stream-node-max-entries 100

# Active rehashing
activerehashing yes

# Key expiration
hz 10

# Dynamic HZ
dynamic-hz yes

# AOF rewrite
aof-rewrite-incremental-fsync yes

# RDB/AOF file permissions
rdb-save-incremental-fsync yes
"""
    
    config_path = Path("/etc/redis/redis.conf")
    
    try:
        # Create directory if it doesn't exist
        config_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Write configuration
        with open(config_path, 'w') as f:
            f.write(config_content)
        
        print(f"✓ Redis configuration created at {config_path}")
        return True
        
    except PermissionError:
        print("✗ Permission denied. Run with sudo or create config manually.")
        return False

def start_redis_server():
    """Start Redis server."""
    try:
        # Check if Redis is already running
        result = subprocess.run(['redis-cli', 'ping'], capture_output=True, text=True)
        if result.returncode == 0 and result.stdout.strip() == "PONG":
            print("✓ Redis server is already running")
            return True
        
        # Start Redis server
        print("Starting Redis server...")
        subprocess.run(['redis-server', '/etc/redis/redis.conf'], check=True)
        print("✓ Redis server started")
        return True
        
    except subprocess.CalledProcessError:
        print("✗ Failed to start Redis server")
        return False

def test_redis_connection():
    """Test Redis connection."""
    try:
        result = subprocess.run(['redis-cli', 'ping'], capture_output=True, text=True)
        if result.returncode == 0 and result.stdout.strip() == "PONG":
            print("✓ Redis connection test successful")
            return True
        else:
            print("✗ Redis connection test failed")
            return False
    except subprocess.CalledProcessError:
        print("✗ Redis connection test failed")
        return False

def create_env_config():
    """Create environment configuration for Redis."""
    env_config = {
        "REDIS_URL": "redis://localhost:6379/0",
        "REDIS_PASSWORD": "your_secure_password_here",
        "REDIS_MAX_CONNECTIONS": "10"
    }
    
    env_file = Path(".env")
    
    if env_file.exists():
        print("✓ .env file already exists")
        with open(env_file, 'r') as f:
            content = f.read()
        
        # Update Redis configuration
        updated_content = content
        for key, value in env_config.items():
            if key not in content:
                updated_content += f"\n{key}={value}"
        
        with open(env_file, 'w') as f:
            f.write(updated_content)
        
        print("✓ Redis configuration added to .env")
    else:
        with open(env_file, 'w') as f:
            f.write("# Redis Configuration\n")
            for key, value in env_config.items():
                f.write(f"{key}={value}\n")
        
        print("✓ .env file created with Redis configuration")

def setup_redis_monitoring():
    """Set up Redis monitoring scripts."""
    monitoring_script = """#!/bin/bash
# Redis Monitoring Script

echo "Redis Server Status:"
redis-cli ping

echo "Redis Info:"
redis-cli info server

echo "Redis Memory Usage:"
redis-cli info memory | grep used_memory_human

echo "Redis Keyspace:"
redis-cli info keyspace

echo "Redis Stats:"
redis-cli info stats | grep keyspace
"""
    
    script_path = Path("scripts/monitor_redis.sh")
    script_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(script_path, 'w') as f:
        f.write(monitoring_script)
    
    # Make executable
    os.chmod(script_path, 0o755)
    
    print(f"✓ Redis monitoring script created at {script_path}")

def main():
    """Main setup function."""
    print("EZBI Analytics Redis Setup")
    print("=" * 40)
    
    # Check if Redis is installed
    if not check_redis_installed():
        print("\nInstalling Redis...")
        if not install_redis():
            print("✗ Redis installation failed")
            sys.exit(1)
    
    # Create Redis configuration
    print("\nCreating Redis configuration...")
    create_redis_config()
    
    # Start Redis server
    print("\nStarting Redis server...")
    start_redis_server()
    
    # Test connection
    print("\nTesting Redis connection...")
    if test_redis_connection():
        print("✓ Redis setup completed successfully")
    else:
        print("✗ Redis setup failed")
        sys.exit(1)
    
    # Create environment configuration
    print("\nCreating environment configuration...")
    create_env_config()
    
    # Setup monitoring
    print("\nSetting up Redis monitoring...")
    setup_redis_monitoring()
    
    print("\n" + "=" * 40)
    print("Redis Setup Complete!")
    print("=" * 40)
    
    print("\nNext steps:")
    print("1. Update your .env file with the correct Redis password")
    print("2. Run: python -m app.main to start the API with Redis caching")
    print("3. Use scripts/monitor_redis.sh to monitor Redis performance")
    print("4. Check Redis logs at /var/log/redis/redis-server.log")

if __name__ == "__main__":
    main()