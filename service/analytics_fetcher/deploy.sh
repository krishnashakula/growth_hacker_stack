#!/bin/bash

# Production Deployment Script for Analytics Fetcher Service
# Usage: ./deploy.sh [environment]

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default environment
ENVIRONMENT=${1:-production}

echo -e "${BLUE}🚀 Analytics Fetcher Service - Production Deployment${NC}"
echo -e "${BLUE}Environment: ${ENVIRONMENT}${NC}"
echo ""

# Function to print colored output
print_status() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Check if Docker is installed
check_docker() {
    if ! command -v docker &> /dev/null; then
        print_error "Docker is not installed. Please install Docker first."
        exit 1
    fi
    
    if ! command -v docker-compose &> /dev/null; then
        print_error "Docker Compose is not installed. Please install Docker Compose first."
        exit 1
    fi
    
    print_status "Docker and Docker Compose are available"
}

# Check if .env file exists
check_env_file() {
    if [ ! -f ".env" ]; then
        print_warning ".env file not found. Creating from template..."
        if [ -f "env.example" ]; then
            cp env.example .env
            print_warning "Please update .env file with your production values"
            print_warning "Required variables:"
            print_warning "  - DB_PASS (database password)"
            print_warning "  - LINKEDIN_API_KEY"
            print_warning "  - LINKEDIN_API_SECRET"
            print_warning "  - LINKEDIN_PERSON_URN"
            exit 1
        else
            print_error "env.example file not found. Please create .env file manually."
            exit 1
        fi
    fi
    
    print_status ".env file found"
}

# Validate required environment variables
validate_env() {
    print_status "Validating environment variables..."
    
    # Source .env file
    set -a
    source .env
    set +a
    
    # Check required variables
    local missing_vars=()
    
    if [ -z "$DB_PASS" ]; then
        missing_vars+=("DB_PASS")
    fi
    
    if [ -z "$LINKEDIN_API_KEY" ]; then
        missing_vars+=("LINKEDIN_API_KEY")
    fi
    
    if [ -z "$LINKEDIN_API_SECRET" ]; then
        missing_vars+=("LINKEDIN_API_SECRET")
    fi
    
    if [ -z "$LINKEDIN_PERSON_URN" ]; then
        missing_vars+=("LINKEDIN_PERSON_URN")
    fi
    
    if [ ${#missing_vars[@]} -ne 0 ]; then
        print_error "Missing required environment variables:"
        for var in "${missing_vars[@]}"; do
            print_error "  - $var"
        done
        exit 1
    fi
    
    print_status "All required environment variables are set"
}

# Create necessary directories
create_directories() {
    print_status "Creating necessary directories..."
    
    mkdir -p logs data grafana/provisioning
    
    print_status "Directories created"
}

# Build and deploy services
deploy_services() {
    print_status "Building and deploying services..."
    
    # Stop existing containers
    docker-compose -f docker-compose.prod.yml down --remove-orphans
    
    # Build and start services
    docker-compose -f docker-compose.prod.yml up -d --build
    
    print_status "Services deployed successfully"
}

# Wait for services to be healthy
wait_for_health() {
    print_status "Waiting for services to be healthy..."
    
    local max_attempts=30
    local attempt=1
    
    while [ $attempt -le $max_attempts ]; do
        if curl -f http://localhost:8000/health &> /dev/null; then
            print_status "Analytics Fetcher Service is healthy"
            break
        fi
        
        if [ $attempt -eq $max_attempts ]; then
            print_error "Service failed to become healthy after $max_attempts attempts"
            docker-compose -f docker-compose.prod.yml logs analytics-fetcher
            exit 1
        fi
        
        print_warning "Waiting for service to be healthy... (attempt $attempt/$max_attempts)"
        sleep 10
        ((attempt++))
    done
}

# Show service status
show_status() {
    print_status "Service Status:"
    echo ""
    
    # Show running containers
    docker-compose -f docker-compose.prod.yml ps
    
    echo ""
    print_status "Service URLs:"
    echo "  - Analytics Fetcher Health: http://localhost:8000/health"
    echo "  - Analytics Fetcher Metrics: http://localhost:8000/metrics"
    echo "  - Prometheus: http://localhost:9090"
    echo "  - Grafana: http://localhost:3000 (admin/admin)"
    
    echo ""
    print_status "Logs:"
    echo "  - View logs: docker-compose -f docker-compose.prod.yml logs -f"
    echo "  - View specific service: docker-compose -f docker-compose.prod.yml logs -f analytics-fetcher"
}

# Main deployment function
main() {
    echo "Starting deployment process..."
    echo ""
    
    check_docker
    check_env_file
    validate_env
    create_directories
    deploy_services
    wait_for_health
    show_status
    
    echo ""
    print_status "🎉 Deployment completed successfully!"
    print_status "The Analytics Fetcher Service is now running in production mode."
}

# Run main function
main "$@" 