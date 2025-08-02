#!/bin/bash

# ========================================
# Growth Hacker Stack - Deployment Script
# ========================================

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to check Docker and Docker Compose
check_docker() {
    print_status "Checking Docker installation..."
    
    if ! command_exists docker; then
        print_error "Docker is not installed. Please install Docker first."
        exit 1
    fi
    
    if ! command_exists docker-compose; then
        print_error "Docker Compose is not installed. Please install Docker Compose first."
        exit 1
    fi
    
    # Check if Docker daemon is running
    if ! docker info >/dev/null 2>&1; then
        print_error "Docker daemon is not running. Please start Docker first."
        exit 1
    fi
    
    print_success "Docker and Docker Compose are available"
}

# Function to check environment file
check_env_file() {
    print_status "Checking environment configuration..."
    
    if [ ! -f ".env" ]; then
        if [ -f "env.example" ]; then
            print_warning "No .env file found. Creating from env.example..."
            cp env.example .env
            print_warning "Please edit .env file with your configuration values before continuing."
            print_warning "Press Enter to continue or Ctrl+C to abort..."
            read -r
        else
            print_error "No .env file found and no env.example template available."
            exit 1
        fi
    else
        print_success "Environment file found"
    fi
}

# Function to validate environment variables
validate_env() {
    print_status "Validating environment variables..."
    
    # Source the .env file
    if [ -f ".env" ]; then
        set -a
        source .env
        set +a
    fi
    
    # Check required variables
    local missing_vars=()
    
    # Database variables
    if [ -z "$POSTGRES_PASSWORD" ] || [ "$POSTGRES_PASSWORD" = "your_secure_database_password_here" ]; then
        missing_vars+=("POSTGRES_PASSWORD")
    fi
    
    # LinkedIn API variables
    if [ -z "$LINKEDIN_API_KEY" ] || [ "$LINKEDIN_API_KEY" = "your_linkedin_api_key_here" ]; then
        missing_vars+=("LINKEDIN_API_KEY")
    fi
    
    if [ -z "$LINKEDIN_API_SECRET" ] || [ "$LINKEDIN_API_SECRET" = "your_linkedin_api_secret_here" ]; then
        missing_vars+=("LINKEDIN_API_SECRET")
    fi
    
    if [ -z "$LINKEDIN_PERSON_URN" ] || [ "$LINKEDIN_PERSON_URN" = "urn:li:person:your_person_id_here" ]; then
        missing_vars+=("LINKEDIN_PERSON_URN")
    fi
    
    # Security variables for enterprise deployment
    if [ "$ENVIRONMENT" = "production" ]; then
        if [ -z "$SECURITY_ENCRYPTION_KEY" ] || [ "$SECURITY_ENCRYPTION_KEY" = "your-32-byte-encryption-key-here" ]; then
            missing_vars+=("SECURITY_ENCRYPTION_KEY")
        fi
        
        if [ -z "$SECURITY_JWT_SECRET" ] || [ "$SECURITY_JWT_SECRET" = "your-jwt-secret-key-here" ]; then
            missing_vars+=("SECURITY_JWT_SECRET")
        fi
    fi
    
    if [ ${#missing_vars[@]} -ne 0 ]; then
        print_error "Missing or default environment variables:"
        for var in "${missing_vars[@]}"; do
            print_error "  - $var"
        done
        print_error "Please update your .env file with proper values."
        exit 1
    fi
    
    print_success "Environment variables validated"
}

# Function to create necessary directories
create_directories() {
    print_status "Creating necessary directories..."
    
    # Create logs and data directories for analytics fetcher
    mkdir -p service/analytics_fetcher/logs
    mkdir -p service/analytics_fetcher/data
    
    # Create custom directory if it doesn't exist
    mkdir -p custom
    
    # Create workflows directory if it doesn't exist
    mkdir -p workflows
    
    print_success "Directories created"
}

# Function to initialize database
initialize_database() {
    print_status "Initializing database..."
    
    # Start database service
    docker-compose up -d db
    
    # Wait for database to be ready
    print_status "Waiting for database to be ready..."
    sleep 10
    
    # Check if database is healthy
    if docker-compose exec db pg_isready -U "${POSTGRES_USER:-n8n_user}" -d "${POSTGRES_DB:-n8n_db}" >/dev/null 2>&1; then
        print_success "Database is ready"
    else
        print_warning "Database may not be fully ready, continuing anyway..."
    fi
    
    # Initialize database schema if SQL file exists
    if [ -f "sql/init.sql" ]; then
        print_status "Initializing database schema..."
        docker-compose exec -T db psql -U "${POSTGRES_USER:-n8n_user}" -d "${POSTGRES_DB:-n8n_db}" < sql/init.sql
        print_success "Database schema initialized"
    fi
}

# Function to deploy services
deploy_services() {
    print_status "Deploying all services..."
    
    # Stop any existing containers
    docker-compose down --remove-orphans
    
    # Build and start all services
    docker-compose up -d --build
    
    print_success "Services deployed"
}

# Function to wait for services to be healthy
wait_for_services() {
    print_status "Waiting for services to be healthy..."
    
    local max_attempts=30
    local attempt=1
    
    while [ $attempt -le $max_attempts ]; do
        print_status "Checking service health (attempt $attempt/$max_attempts)..."
        
        # Check if all services are running
        if docker-compose ps | grep -q "Up"; then
            print_success "All services are running"
            break
        fi
        
        if [ $attempt -eq $max_attempts ]; then
            print_error "Services failed to start properly"
            docker-compose logs
            exit 1
        fi
        
        sleep 10
        ((attempt++))
    done
}

# Function to check service health
check_service_health() {
    print_status "Checking service health..."
    
    # Check n8n health
    if curl -f http://localhost:5678/healthz >/dev/null 2>&1; then
        print_success "n8n is healthy"
    else
        print_warning "n8n health check failed"
    fi
    
    # Check trending service health
    if curl -f http://localhost:8000/health >/dev/null 2>&1; then
        print_success "Trending service is healthy"
    else
        print_warning "Trending service health check failed"
    fi
    
    # Check analytics fetcher health
    if curl -f http://localhost:8001/health >/dev/null 2>&1; then
        print_success "Analytics fetcher is healthy"
    else
        print_warning "Analytics fetcher health check failed"
    fi
    
    # Check metabase health
    if curl -f http://localhost:3000/api/health >/dev/null 2>&1; then
        print_success "Metabase is healthy"
    else
        print_warning "Metabase health check failed"
    fi
}

# Function to show deployment status
show_status() {
    print_status "Deployment Status:"
    echo ""
    
    # Show running containers
    docker-compose ps
    
    echo ""
    print_status "Service URLs:"
    echo "  - n8n UI: http://localhost:5678"
    echo "  - Trending API: http://localhost:8000"
    echo "  - Analytics Fetcher: http://localhost:8001"
    echo "  - Metabase: http://localhost:3000"
    echo "  - Traefik Dashboard: http://localhost:8080"
    
    echo ""
    print_status "Health Check URLs:"
    echo "  - n8n Health: http://localhost:5678/healthz"
    echo "  - Trending Health: http://localhost:8000/health"
    echo "  - Analytics Health: http://localhost:8001/health"
    echo "  - Analytics Metrics: http://localhost:8001/metrics"
    echo "  - Metabase Health: http://localhost:3000/api/health"
    
    echo ""
    print_status "Next Steps:"
    echo "  1. Import workflows/linkedin_workflow.json into n8n"
    echo "  2. Configure LinkedIn API credentials in n8n"
    echo "  3. Set up Metabase dashboards"
    echo "  4. Monitor service logs: docker-compose logs -f"
}

# Function to show logs
show_logs() {
    print_status "Recent logs from all services:"
    docker-compose logs --tail=50
}

# Function to clean up
cleanup() {
    print_status "Cleaning up..."
    docker-compose down --volumes --remove-orphans
    print_success "Cleanup completed"
}

# Function to show help
show_help() {
    echo "Usage: $0 [OPTION]"
    echo ""
    echo "Options:"
    echo "  deploy      Deploy all services (default)"
    echo "  status      Show deployment status"
    echo "  logs        Show recent logs"
    echo "  health      Check service health"
    echo "  cleanup     Stop and remove all containers"
    echo "  help        Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0 deploy    # Deploy all services"
    echo "  $0 status    # Show current status"
    echo "  $0 logs      # Show recent logs"
}

# Main deployment function
main_deploy() {
    print_status "Starting Growth Hacker Stack deployment..."
    
    check_docker
    check_env_file
    validate_env
    create_directories
    initialize_database
    deploy_services
    wait_for_services
    check_service_health
    show_status
    
    print_success "Deployment completed successfully!"
}

# Main script logic
case "${1:-deploy}" in
    "deploy")
        main_deploy
        ;;
    "status")
        show_status
        ;;
    "logs")
        show_logs
        ;;
    "health")
        check_service_health
        ;;
    "cleanup")
        cleanup
        ;;
    "help"|"-h"|"--help")
        show_help
        ;;
    *)
        print_error "Unknown option: $1"
        show_help
        exit 1
        ;;
esac 