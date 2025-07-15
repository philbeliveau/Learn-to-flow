#!/bin/bash

# Production Backup Script for EZBI Analytics Platform
# DevOps Engineer Implementation - SPARC Production Deployment

set -euo pipefail

# Configuration
BACKUP_DIR="/backup"
RETENTION_DAYS=30
NOTIFICATION_URL="${SLACK_WEBHOOK_URL:-}"
S3_BUCKET="${S3_BACKUP_BUCKET:-ezbi-analytics-backups}"
ENCRYPTION_KEY="${BACKUP_ENCRYPTION_KEY:-}"

# Database configuration
DB_HOST="postgres"
DB_NAME="ezbi_analytics"
DB_USER="ezbi_user"
DB_PASSWORD="${POSTGRES_PASSWORD}"

# Redis configuration
REDIS_HOST="redis"
REDIS_PASSWORD="${REDIS_PASSWORD}"

# Timestamp for backup files
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_DATE=$(date +%Y-%m-%d)

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $(date '+%Y-%m-%d %H:%M:%S') - $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $(date '+%Y-%m-%d %H:%M:%S') - $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $(date '+%Y-%m-%d %H:%M:%S') - $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $(date '+%Y-%m-%d %H:%M:%S') - $1"
}

# Send notification
send_notification() {
    local message="$1"
    local level="${2:-info}"
    
    if [ -n "$NOTIFICATION_URL" ]; then
        curl -X POST -H 'Content-type: application/json' \
            --data "{\"text\":\"[BACKUP] $level: $message\"}" \
            "$NOTIFICATION_URL" 2>/dev/null || true
    fi
}

# Create backup directories
create_backup_dirs() {
    log_info "Creating backup directories..."
    
    mkdir -p "$BACKUP_DIR/database/$BACKUP_DATE"
    mkdir -p "$BACKUP_DIR/redis/$BACKUP_DATE"
    mkdir -p "$BACKUP_DIR/uploads/$BACKUP_DATE"
    mkdir -p "$BACKUP_DIR/logs/$BACKUP_DATE"
    mkdir -p "$BACKUP_DIR/config/$BACKUP_DATE"
    
    log_success "Backup directories created"
}

# Backup PostgreSQL database
backup_database() {
    log_info "Starting database backup..."
    
    local backup_file="$BACKUP_DIR/database/$BACKUP_DATE/database_$TIMESTAMP.sql"
    local backup_file_gz="$backup_file.gz"
    
    # Create database dump
    PGPASSWORD="$DB_PASSWORD" pg_dump \
        -h "$DB_HOST" \
        -U "$DB_USER" \
        -d "$DB_NAME" \
        --verbose \
        --clean \
        --if-exists \
        --create \
        --format=plain \
        > "$backup_file"
    
    # Compress the backup
    gzip "$backup_file"
    
    # Encrypt if encryption key is provided
    if [ -n "$ENCRYPTION_KEY" ]; then
        openssl enc -aes-256-cbc -salt -in "$backup_file_gz" -out "$backup_file_gz.enc" -k "$ENCRYPTION_KEY"
        rm "$backup_file_gz"
        backup_file_gz="$backup_file_gz.enc"
    fi
    
    # Verify backup integrity
    if [ -f "$backup_file_gz" ] && [ -s "$backup_file_gz" ]; then
        local size=$(du -h "$backup_file_gz" | cut -f1)
        log_success "Database backup completed: $backup_file_gz ($size)"
        
        # Update metrics
        echo "last_backup_timestamp $(date +%s)" > /tmp/backup_metrics.prom
        echo "backup_size_bytes $(stat -c%s "$backup_file_gz")" >> /tmp/backup_metrics.prom
    else
        log_error "Database backup failed or is empty"
        send_notification "Database backup failed" "error"
        exit 1
    fi
}

# Backup Redis data
backup_redis() {
    log_info "Starting Redis backup..."
    
    local backup_file="$BACKUP_DIR/redis/$BACKUP_DATE/redis_$TIMESTAMP.rdb"
    
    # Create Redis backup using BGSAVE
    redis-cli -h "$REDIS_HOST" -a "$REDIS_PASSWORD" BGSAVE > /dev/null
    
    # Wait for background save to complete
    local save_in_progress=1
    while [ $save_in_progress -eq 1 ]; do
        sleep 1
        local lastsave=$(redis-cli -h "$REDIS_HOST" -a "$REDIS_PASSWORD" LASTSAVE)
        local current_time=$(date +%s)
        
        if [ $((current_time - lastsave)) -lt 10 ]; then
            save_in_progress=0
        fi
    done
    
    # Copy RDB file
    docker exec ezbi-redis-prod cp /data/dump.rdb /tmp/dump.rdb
    docker cp ezbi-redis-prod:/tmp/dump.rdb "$backup_file"
    
    # Compress and encrypt
    gzip "$backup_file"
    if [ -n "$ENCRYPTION_KEY" ]; then
        openssl enc -aes-256-cbc -salt -in "$backup_file.gz" -out "$backup_file.gz.enc" -k "$ENCRYPTION_KEY"
        rm "$backup_file.gz"
    fi
    
    log_success "Redis backup completed"
}

# Backup uploaded files
backup_uploads() {
    log_info "Starting uploads backup..."
    
    local backup_file="$BACKUP_DIR/uploads/$BACKUP_DATE/uploads_$TIMESTAMP.tar.gz"
    
    if [ -d "/app/uploads" ]; then
        tar -czf "$backup_file" -C /app uploads/
        
        # Encrypt if encryption key is provided
        if [ -n "$ENCRYPTION_KEY" ]; then
            openssl enc -aes-256-cbc -salt -in "$backup_file" -out "$backup_file.enc" -k "$ENCRYPTION_KEY"
            rm "$backup_file"
        fi
        
        log_success "Uploads backup completed"
    else
        log_warning "No uploads directory found"
    fi
}

# Backup logs
backup_logs() {
    log_info "Starting logs backup..."
    
    local backup_file="$BACKUP_DIR/logs/$BACKUP_DATE/logs_$TIMESTAMP.tar.gz"
    
    if [ -d "/app/logs" ]; then
        tar -czf "$backup_file" -C /app logs/
        
        # Encrypt if encryption key is provided
        if [ -n "$ENCRYPTION_KEY" ]; then
            openssl enc -aes-256-cbc -salt -in "$backup_file" -out "$backup_file.enc" -k "$ENCRYPTION_KEY"
            rm "$backup_file"
        fi
        
        log_success "Logs backup completed"
    else
        log_warning "No logs directory found"
    fi
}

# Backup configuration files
backup_config() {
    log_info "Starting configuration backup..."
    
    local backup_file="$BACKUP_DIR/config/$BACKUP_DATE/config_$TIMESTAMP.tar.gz"
    
    tar -czf "$backup_file" \
        -C /app \
        deployment/ \
        .env.production \
        production-docker-compose.yml \
        2>/dev/null || true
    
    # Encrypt if encryption key is provided
    if [ -n "$ENCRYPTION_KEY" ]; then
        openssl enc -aes-256-cbc -salt -in "$backup_file" -out "$backup_file.enc" -k "$ENCRYPTION_KEY"
        rm "$backup_file"
    fi
    
    log_success "Configuration backup completed"
}

# Upload to S3 (if configured)
upload_to_s3() {
    if command -v aws &> /dev/null && [ -n "$S3_BUCKET" ]; then
        log_info "Uploading backups to S3..."
        
        aws s3 sync "$BACKUP_DIR/$BACKUP_DATE" "s3://$S3_BUCKET/$BACKUP_DATE/" \
            --storage-class STANDARD_IA \
            --server-side-encryption AES256
        
        log_success "Backups uploaded to S3"
    else
        log_warning "S3 upload not configured or AWS CLI not available"
    fi
}

# Clean old backups
cleanup_old_backups() {
    log_info "Cleaning up old backups..."
    
    find "$BACKUP_DIR" -type d -name "*_*" -mtime +$RETENTION_DAYS -exec rm -rf {} \; 2>/dev/null || true
    
    # Clean old S3 backups
    if command -v aws &> /dev/null && [ -n "$S3_BUCKET" ]; then
        local cutoff_date=$(date -d "-$RETENTION_DAYS days" +%Y-%m-%d)
        aws s3 ls "s3://$S3_BUCKET/" | while read -r line; do
            local backup_date=$(echo "$line" | awk '{print $2}' | sed 's/\///')
            if [[ "$backup_date" < "$cutoff_date" ]]; then
                aws s3 rm "s3://$S3_BUCKET/$backup_date/" --recursive
            fi
        done
    fi
    
    log_success "Old backups cleaned up"
}

# Generate backup report
generate_report() {
    log_info "Generating backup report..."
    
    local report_file="$BACKUP_DIR/reports/backup_report_$TIMESTAMP.json"
    mkdir -p "$BACKUP_DIR/reports"
    
    cat > "$report_file" << EOF
{
    "timestamp": "$TIMESTAMP",
    "date": "$BACKUP_DATE",
    "status": "success",
    "components": {
        "database": {
            "status": "completed",
            "size": "$(du -h "$BACKUP_DIR/database/$BACKUP_DATE" | tail -1 | cut -f1)"
        },
        "redis": {
            "status": "completed",
            "size": "$(du -h "$BACKUP_DIR/redis/$BACKUP_DATE" | tail -1 | cut -f1)"
        },
        "uploads": {
            "status": "completed",
            "size": "$(du -h "$BACKUP_DIR/uploads/$BACKUP_DATE" | tail -1 | cut -f1)"
        },
        "logs": {
            "status": "completed",
            "size": "$(du -h "$BACKUP_DIR/logs/$BACKUP_DATE" | tail -1 | cut -f1)"
        },
        "config": {
            "status": "completed",
            "size": "$(du -h "$BACKUP_DIR/config/$BACKUP_DATE" | tail -1 | cut -f1)"
        }
    },
    "total_size": "$(du -h "$BACKUP_DIR/$BACKUP_DATE" | tail -1 | cut -f1)",
    "retention_days": $RETENTION_DAYS,
    "encryption_enabled": $([ -n "$ENCRYPTION_KEY" ] && echo "true" || echo "false"),
    "s3_upload": $([ -n "$S3_BUCKET" ] && echo "true" || echo "false")
}
EOF
    
    log_success "Backup report generated: $report_file"
}

# Main backup function
main() {
    log_info "Starting EZBI Analytics production backup"
    send_notification "Starting production backup" "info"
    
    # Verify prerequisites
    if ! command -v pg_dump &> /dev/null; then
        log_error "pg_dump is required but not installed"
        exit 1
    fi
    
    if ! command -v redis-cli &> /dev/null; then
        log_error "redis-cli is required but not installed"
        exit 1
    fi
    
    # Execute backup steps
    create_backup_dirs
    backup_database
    backup_redis
    backup_uploads
    backup_logs
    backup_config
    upload_to_s3
    cleanup_old_backups
    generate_report
    
    log_success "Backup completed successfully"
    send_notification "Production backup completed successfully" "success"
    
    # Display summary
    log_info "Backup Summary:"
    log_info "  - Date: $BACKUP_DATE"
    log_info "  - Timestamp: $TIMESTAMP"
    log_info "  - Location: $BACKUP_DIR/$BACKUP_DATE"
    log_info "  - Total Size: $(du -h "$BACKUP_DIR/$BACKUP_DATE" | tail -1 | cut -f1)"
    log_info "  - Retention: $RETENTION_DAYS days"
}

# Error handling
trap 'log_error "Backup failed at line $LINENO"; send_notification "Backup failed" "error"; exit 1' ERR

# Run main function
main "$@"