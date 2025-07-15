#!/bin/bash

# Disaster Recovery Script for EZBI Analytics Platform
# DevOps Engineer Implementation - SPARC Production Deployment

set -euo pipefail

# Configuration
BACKUP_DIR="/backup"
RESTORE_DATE="${1:-$(date +%Y-%m-%d)}"
RESTORE_POINT="${2:-latest}"
ENCRYPTION_KEY="${BACKUP_ENCRYPTION_KEY:-}"
S3_BUCKET="${S3_BACKUP_BUCKET:-ezbi-analytics-backups}"

# Database configuration
DB_HOST="postgres"
DB_NAME="ezbi_analytics"
DB_USER="ezbi_user"
DB_PASSWORD="${POSTGRES_PASSWORD}"

# Redis configuration
REDIS_HOST="redis"
REDIS_PASSWORD="${REDIS_PASSWORD}"

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

# Show help
show_help() {
    cat << EOF
EZBI Analytics Disaster Recovery Script

Usage: $0 [RESTORE_DATE] [RESTORE_POINT]

Arguments:
  RESTORE_DATE    Date of backup to restore (YYYY-MM-DD, default: today)
  RESTORE_POINT   Backup point to restore (timestamp or 'latest', default: latest)

Examples:
  $0                           # Restore latest backup from today
  $0 2024-01-15                # Restore latest backup from 2024-01-15
  $0 2024-01-15 20240115_143000 # Restore specific backup point

Environment Variables:
  BACKUP_ENCRYPTION_KEY        # Encryption key for encrypted backups
  S3_BACKUP_BUCKET            # S3 bucket for backup storage
  POSTGRES_PASSWORD           # PostgreSQL password
  REDIS_PASSWORD              # Redis password

EOF
}

# Check if help is requested
if [[ "${1:-}" == "--help" ]] || [[ "${1:-}" == "-h" ]]; then
    show_help
    exit 0
fi

# Verify prerequisites
check_prerequisites() {
    log_info "Checking prerequisites..."
    
    if ! command -v psql &> /dev/null; then
        log_error "psql is required but not installed"
        exit 1
    fi
    
    if ! command -v redis-cli &> /dev/null; then
        log_error "redis-cli is required but not installed"
        exit 1
    fi
    
    if ! command -v docker &> /dev/null; then
        log_error "docker is required but not installed"
        exit 1
    fi
    
    log_success "Prerequisites check passed"
}

# Download backup from S3 if needed
download_from_s3() {
    if command -v aws &> /dev/null && [ -n "$S3_BUCKET" ]; then
        log_info "Downloading backup from S3..."
        
        mkdir -p "$BACKUP_DIR"
        aws s3 sync "s3://$S3_BUCKET/$RESTORE_DATE/" "$BACKUP_DIR/$RESTORE_DATE/" \
            --delete
        
        log_success "Backup downloaded from S3"
    else
        log_warning "S3 not configured or AWS CLI not available"
    fi
}

# Find backup files
find_backup_files() {
    log_info "Finding backup files for $RESTORE_DATE..."
    
    local backup_path="$BACKUP_DIR/$RESTORE_DATE"
    
    if [ ! -d "$backup_path" ]; then
        log_error "Backup directory not found: $backup_path"
        exit 1
    fi
    
    # Find database backup
    if [ "$RESTORE_POINT" == "latest" ]; then
        DB_BACKUP=$(find "$backup_path/database" -name "*.sql.gz*" | sort | tail -1)
    else
        DB_BACKUP=$(find "$backup_path/database" -name "*$RESTORE_POINT*.sql.gz*" | head -1)
    fi
    
    # Find Redis backup
    if [ "$RESTORE_POINT" == "latest" ]; then
        REDIS_BACKUP=$(find "$backup_path/redis" -name "*.rdb.gz*" | sort | tail -1)
    else
        REDIS_BACKUP=$(find "$backup_path/redis" -name "*$RESTORE_POINT*.rdb.gz*" | head -1)
    fi
    
    # Find uploads backup
    if [ "$RESTORE_POINT" == "latest" ]; then
        UPLOADS_BACKUP=$(find "$backup_path/uploads" -name "*.tar.gz*" | sort | tail -1)
    else
        UPLOADS_BACKUP=$(find "$backup_path/uploads" -name "*$RESTORE_POINT*.tar.gz*" | head -1)
    fi
    
    # Find config backup
    if [ "$RESTORE_POINT" == "latest" ]; then
        CONFIG_BACKUP=$(find "$backup_path/config" -name "*.tar.gz*" | sort | tail -1)
    else
        CONFIG_BACKUP=$(find "$backup_path/config" -name "*$RESTORE_POINT*.tar.gz*" | head -1)
    fi
    
    log_info "Found backup files:"
    log_info "  Database: ${DB_BACKUP:-Not found}"
    log_info "  Redis: ${REDIS_BACKUP:-Not found}"
    log_info "  Uploads: ${UPLOADS_BACKUP:-Not found}"
    log_info "  Config: ${CONFIG_BACKUP:-Not found}"
}

# Decrypt and decompress backup file
decrypt_decompress() {
    local file="$1"
    local output_dir="$2"
    
    if [ -z "$file" ] || [ ! -f "$file" ]; then
        log_warning "Backup file not found: $file"
        return 1
    fi
    
    local temp_file="/tmp/$(basename "$file")"
    
    # Decrypt if encrypted
    if [[ "$file" == *.enc ]]; then
        if [ -z "$ENCRYPTION_KEY" ]; then
            log_error "Encryption key required for encrypted backup"
            exit 1
        fi
        
        openssl enc -aes-256-cbc -d -in "$file" -out "$temp_file" -k "$ENCRYPTION_KEY"
        file="$temp_file"
    else
        cp "$file" "$temp_file"
    fi
    
    # Decompress
    if [[ "$temp_file" == *.gz ]]; then
        gunzip -c "$temp_file" > "$output_dir/$(basename "$temp_file" .gz)"
    elif [[ "$temp_file" == *.tar.gz ]]; then
        tar -xzf "$temp_file" -C "$output_dir"
    else
        cp "$temp_file" "$output_dir/"
    fi
    
    rm -f "$temp_file"
}

# Stop services
stop_services() {
    log_info "Stopping services..."
    
    docker-compose -f production-docker-compose.yml stop backend frontend ml-engine || true
    
    log_success "Services stopped"
}

# Restore database
restore_database() {
    if [ -z "$DB_BACKUP" ]; then
        log_warning "No database backup found"
        return 1
    fi
    
    log_info "Restoring database..."
    
    # Prepare restore directory
    local restore_dir="/tmp/restore_db"
    mkdir -p "$restore_dir"
    
    # Decrypt and decompress
    decrypt_decompress "$DB_BACKUP" "$restore_dir"
    
    local sql_file=$(find "$restore_dir" -name "*.sql" | head -1)
    
    if [ -z "$sql_file" ]; then
        log_error "No SQL file found in backup"
        exit 1
    fi
    
    # Drop existing database (if exists)
    PGPASSWORD="$DB_PASSWORD" psql -h "$DB_HOST" -U "$DB_USER" -d postgres \
        -c "DROP DATABASE IF EXISTS $DB_NAME;"
    
    # Create new database
    PGPASSWORD="$DB_PASSWORD" psql -h "$DB_HOST" -U "$DB_USER" -d postgres \
        -c "CREATE DATABASE $DB_NAME;"
    
    # Restore database
    PGPASSWORD="$DB_PASSWORD" psql -h "$DB_HOST" -U "$DB_USER" -d "$DB_NAME" \
        -f "$sql_file"
    
    # Cleanup
    rm -rf "$restore_dir"
    
    log_success "Database restored successfully"
}

# Restore Redis
restore_redis() {
    if [ -z "$REDIS_BACKUP" ]; then
        log_warning "No Redis backup found"
        return 1
    fi
    
    log_info "Restoring Redis..."
    
    # Prepare restore directory
    local restore_dir="/tmp/restore_redis"
    mkdir -p "$restore_dir"
    
    # Decrypt and decompress
    decrypt_decompress "$REDIS_BACKUP" "$restore_dir"
    
    local rdb_file=$(find "$restore_dir" -name "*.rdb" | head -1)
    
    if [ -z "$rdb_file" ]; then
        log_error "No RDB file found in backup"
        exit 1
    fi
    
    # Stop Redis temporarily
    docker exec ezbi-redis-prod redis-cli -a "$REDIS_PASSWORD" SHUTDOWN NOSAVE || true
    
    # Copy RDB file
    docker cp "$rdb_file" ezbi-redis-prod:/data/dump.rdb
    
    # Start Redis
    docker start ezbi-redis-prod || true
    
    # Wait for Redis to be ready
    sleep 5
    
    # Verify Redis is working
    if redis-cli -h "$REDIS_HOST" -a "$REDIS_PASSWORD" ping > /dev/null; then
        log_success "Redis restored successfully"
    else
        log_error "Redis restoration failed"
        exit 1
    fi
    
    # Cleanup
    rm -rf "$restore_dir"
}

# Restore uploads
restore_uploads() {
    if [ -z "$UPLOADS_BACKUP" ]; then
        log_warning "No uploads backup found"
        return 1
    fi
    
    log_info "Restoring uploads..."
    
    # Prepare restore directory
    local restore_dir="/tmp/restore_uploads"
    mkdir -p "$restore_dir"
    
    # Decrypt and decompress
    decrypt_decompress "$UPLOADS_BACKUP" "$restore_dir"
    
    # Remove existing uploads
    rm -rf /app/uploads/*
    
    # Restore uploads
    if [ -d "$restore_dir/uploads" ]; then
        cp -r "$restore_dir/uploads"/* /app/uploads/
        chown -R ezbi:ezbi /app/uploads
        log_success "Uploads restored successfully"
    else
        log_warning "No uploads directory found in backup"
    fi
    
    # Cleanup
    rm -rf "$restore_dir"
}

# Restore configuration
restore_config() {
    if [ -z "$CONFIG_BACKUP" ]; then
        log_warning "No configuration backup found"
        return 1
    fi
    
    log_info "Restoring configuration..."
    
    # Prepare restore directory
    local restore_dir="/tmp/restore_config"
    mkdir -p "$restore_dir"
    
    # Decrypt and decompress
    decrypt_decompress "$CONFIG_BACKUP" "$restore_dir"
    
    # Restore configuration files
    if [ -d "$restore_dir/deployment" ]; then
        cp -r "$restore_dir/deployment"/* /app/deployment/
        log_success "Configuration restored successfully"
    else
        log_warning "No deployment directory found in backup"
    fi
    
    # Cleanup
    rm -rf "$restore_dir"
}

# Start services
start_services() {
    log_info "Starting services..."
    
    docker-compose -f production-docker-compose.yml up -d
    
    # Wait for services to be ready
    sleep 30
    
    # Health checks
    local max_attempts=10
    local attempt=0
    
    while [ $attempt -lt $max_attempts ]; do
        if curl -f -s "http://localhost:8000/health" > /dev/null 2>&1; then
            log_success "Services started successfully"
            return 0
        fi
        
        attempt=$((attempt + 1))
        log_info "Attempt $attempt/$max_attempts: Services not ready, waiting..."
        sleep 10
    done
    
    log_error "Services failed to start after $max_attempts attempts"
    exit 1
}

# Verify restoration
verify_restoration() {
    log_info "Verifying restoration..."
    
    # Check database
    local db_tables=$(PGPASSWORD="$DB_PASSWORD" psql -h "$DB_HOST" -U "$DB_USER" -d "$DB_NAME" \
        -t -c "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public';")
    
    if [ "$db_tables" -gt 0 ]; then
        log_success "Database verification passed ($db_tables tables found)"
    else
        log_error "Database verification failed"
        exit 1
    fi
    
    # Check Redis
    if redis-cli -h "$REDIS_HOST" -a "$REDIS_PASSWORD" ping > /dev/null; then
        log_success "Redis verification passed"
    else
        log_error "Redis verification failed"
        exit 1
    fi
    
    # Check API endpoints
    if curl -f -s "http://localhost:8000/health" > /dev/null; then
        log_success "API verification passed"
    else
        log_error "API verification failed"
        exit 1
    fi
    
    log_success "All verifications passed"
}

# Generate restoration report
generate_report() {
    log_info "Generating restoration report..."
    
    local report_file="/tmp/restoration_report_$(date +%Y%m%d_%H%M%S).json"
    
    cat > "$report_file" << EOF
{
    "timestamp": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
    "restore_date": "$RESTORE_DATE",
    "restore_point": "$RESTORE_POINT",
    "status": "success",
    "components": {
        "database": {
            "status": "$([ -n "$DB_BACKUP" ] && echo "restored" || echo "skipped")",
            "backup_file": "${DB_BACKUP:-none}"
        },
        "redis": {
            "status": "$([ -n "$REDIS_BACKUP" ] && echo "restored" || echo "skipped")",
            "backup_file": "${REDIS_BACKUP:-none}"
        },
        "uploads": {
            "status": "$([ -n "$UPLOADS_BACKUP" ] && echo "restored" || echo "skipped")",
            "backup_file": "${UPLOADS_BACKUP:-none}"
        },
        "config": {
            "status": "$([ -n "$CONFIG_BACKUP" ] && echo "restored" || echo "skipped")",
            "backup_file": "${CONFIG_BACKUP:-none}"
        }
    },
    "verification": {
        "database_tables": $(PGPASSWORD="$DB_PASSWORD" psql -h "$DB_HOST" -U "$DB_USER" -d "$DB_NAME" -t -c "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public';" 2>/dev/null || echo "0"),
        "redis_status": "$(redis-cli -h "$REDIS_HOST" -a "$REDIS_PASSWORD" ping 2>/dev/null || echo "FAILED")",
        "api_status": "$(curl -f -s "http://localhost:8000/health" > /dev/null && echo "OK" || echo "FAILED")"
    }
}
EOF
    
    log_success "Restoration report generated: $report_file"
}

# Main disaster recovery function
main() {
    log_info "Starting EZBI Analytics disaster recovery"
    log_info "Restore date: $RESTORE_DATE"
    log_info "Restore point: $RESTORE_POINT"
    
    # Execute recovery steps
    check_prerequisites
    download_from_s3
    find_backup_files
    
    # Confirm restoration
    log_warning "This will restore the system to the state from $RESTORE_DATE ($RESTORE_POINT)"
    log_warning "Current data will be lost. Are you sure? (y/N)"
    read -r confirmation
    
    if [[ "$confirmation" != "y" && "$confirmation" != "Y" ]]; then
        log_info "Restoration cancelled by user"
        exit 0
    fi
    
    stop_services
    restore_database
    restore_redis
    restore_uploads
    restore_config
    start_services
    verify_restoration
    generate_report
    
    log_success "Disaster recovery completed successfully"
    log_info "System has been restored to the state from $RESTORE_DATE ($RESTORE_POINT)"
}

# Error handling
trap 'log_error "Disaster recovery failed at line $LINENO"' ERR

# Run main function
main "$@"