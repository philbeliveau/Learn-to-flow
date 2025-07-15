#!/bin/bash

# Production Deployment Script for EZBI Analytics Platform
# DevOps Engineer Implementation - SPARC Production Deployment

set -euo pipefail

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
ENVIRONMENT="${1:-production}"
VERSION="${2:-latest}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check prerequisites
check_prerequisites() {
    log_info "Checking prerequisites..."
    
    # Check Docker
    if ! command -v docker &> /dev/null; then
        log_error "Docker is not installed or not in PATH"
        exit 1
    fi
    
    # Check Docker Compose
    if ! command -v docker-compose &> /dev/null; then
        log_error "Docker Compose is not installed or not in PATH"
        exit 1
    fi
    
    # Check environment file
    if [ ! -f "$PROJECT_ROOT/.env.$ENVIRONMENT" ]; then
        log_error "Environment file .env.$ENVIRONMENT not found"
        exit 1
    fi
    
    log_success "All prerequisites met"
}

# Backup current deployment
backup_deployment() {
    log_info "Creating backup of current deployment..."
    
    local backup_dir="$PROJECT_ROOT/backups/$(date +%Y%m%d_%H%M%S)"
    mkdir -p "$backup_dir"
    
    # Backup database
    docker exec ezbi-postgres-prod pg_dump -U ezbi_user ezbi_analytics > "$backup_dir/database_backup.sql"
    
    # Backup uploaded files
    if [ -d "$PROJECT_ROOT/uploads" ]; then
        cp -r "$PROJECT_ROOT/uploads" "$backup_dir/"
    fi
    
    # Backup configuration
    cp -r "$PROJECT_ROOT/deployment" "$backup_dir/"
    
    log_success "Backup created at $backup_dir"
}

# Health check function
health_check() {
    local service=$1
    local url=$2
    local max_attempts=30
    local attempt=0
    
    log_info "Performing health check for $service..."
    
    while [ $attempt -lt $max_attempts ]; do
        if curl -f -s "$url" > /dev/null 2>&1; then
            log_success "$service is healthy"
            return 0
        fi
        
        attempt=$((attempt + 1))
        log_info "Attempt $attempt/$max_attempts: $service not ready, waiting..."
        sleep 10
    done
    
    log_error "$service failed health check after $max_attempts attempts"
    return 1
}

# Deploy services
deploy_services() {
    log_info "Deploying services..."
    
    # Set environment variables
    export POSTGRES_PASSWORD="${POSTGRES_PASSWORD:-$(openssl rand -base64 32)}"
    export REDIS_PASSWORD="${REDIS_PASSWORD:-$(openssl rand -base64 32)}"
    export JWT_SECRET="${JWT_SECRET:-$(openssl rand -base64 32)}"
    export GRAFANA_PASSWORD="${GRAFANA_PASSWORD:-$(openssl rand -base64 32)}"
    export NEXTAUTH_SECRET="${NEXTAUTH_SECRET:-$(openssl rand -base64 32)}"
    
    # Pull latest images
    log_info "Pulling latest images..."
    docker-compose -f "$PROJECT_ROOT/production-docker-compose.yml" pull
    
    # Start services
    log_info "Starting services..."
    docker-compose -f "$PROJECT_ROOT/production-docker-compose.yml" up -d
    
    # Wait for services to be ready
    log_info "Waiting for services to be ready..."
    sleep 30
    
    # Health checks
    health_check "Backend API" "http://localhost:8000/health"
    health_check "Frontend" "http://localhost:3000/api/health"
    health_check "ML Engine" "http://localhost:8004/health"
    
    log_success "All services deployed successfully"
}

# Run database migrations
run_migrations() {
    log_info "Running database migrations..."
    
    # Wait for database to be ready
    docker exec ezbi-postgres-prod pg_isready -U ezbi_user -d ezbi_analytics
    
    # Run migrations
    docker exec ezbi-backend-prod python -m alembic upgrade head
    
    log_success "Database migrations completed"
}

# Configure monitoring
setup_monitoring() {
    log_info "Setting up monitoring..."
    
    # Configure Grafana dashboards
    docker exec ezbi-grafana-prod grafana-cli admin reset-admin-password "${GRAFANA_PASSWORD}"
    
    # Import dashboards
    for dashboard in "$PROJECT_ROOT/deployment/monitoring/grafana/dashboards"/*.json; do
        if [ -f "$dashboard" ]; then
            log_info "Importing dashboard: $(basename "$dashboard")"
            docker exec ezbi-grafana-prod grafana-cli --config /etc/grafana/grafana.ini admin import-dashboard "$dashboard"
        fi
    done
    
    log_success "Monitoring setup completed"
}

# Setup SSL certificates
setup_ssl() {
    log_info "Setting up SSL certificates..."
    
    local ssl_dir="$PROJECT_ROOT/deployment/nginx/ssl"
    mkdir -p "$ssl_dir"
    
    # Generate self-signed certificate for development
    if [ ! -f "$ssl_dir/cert.pem" ]; then
        openssl req -x509 -newkey rsa:4096 -keyout "$ssl_dir/key.pem" -out "$ssl_dir/cert.pem" -days 365 -nodes -subj "/CN=localhost"
    fi
    
    log_success "SSL certificates configured"
}

# Performance optimization
optimize_performance() {
    log_info "Optimizing performance..."
    
    # Docker system cleanup
    docker system prune -f
    
    # Optimize database
    docker exec ezbi-postgres-prod psql -U ezbi_user -d ezbi_analytics -c "VACUUM ANALYZE;"
    
    # Warm up caches
    curl -s "http://localhost:8000/api/v1/data/cache-warmup" || true
    
    log_success "Performance optimization completed"
}

# Main deployment function
main() {
    log_info "Starting production deployment for EZBI Analytics Platform"
    log_info "Environment: $ENVIRONMENT"
    log_info "Version: $VERSION"
    
    # Load environment variables
    source "$PROJECT_ROOT/.env.$ENVIRONMENT"
    
    # Execute deployment steps
    check_prerequisites
    
    if [ "$ENVIRONMENT" == "production" ]; then
        backup_deployment
    fi
    
    setup_ssl
    deploy_services
    run_migrations
    setup_monitoring
    optimize_performance
    
    log_success "Deployment completed successfully!"
    log_info "Services are available at:"
    log_info "  - Frontend: https://localhost:8443"
    log_info "  - Backend API: https://localhost:8443/api"
    log_info "  - ML Engine: https://localhost:8443/ml"
    log_info "  - Grafana: http://localhost:3001"
    log_info "  - Prometheus: http://localhost:9090"
    
    # Display important passwords
    if [ "$ENVIRONMENT" == "production" ]; then
        log_warning "Important: Save these generated passwords securely:"
        log_warning "  - Database: $POSTGRES_PASSWORD"
        log_warning "  - Redis: $REDIS_PASSWORD"
        log_warning "  - JWT Secret: $JWT_SECRET"
        log_warning "  - Grafana: $GRAFANA_PASSWORD"
    fi
}

# Error handling
trap 'log_error "Deployment failed at line $LINENO"' ERR

# Run main function
main "$@"