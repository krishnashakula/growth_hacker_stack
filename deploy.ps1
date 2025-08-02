# ========================================
# Growth Hacker Stack - PowerShell Deployment Script
# ========================================

param(
    [Parameter(Position=0)]
    [ValidateSet("deploy", "status", "logs", "health", "cleanup", "help")]
    [string]$Action = "deploy"
)

# Colors for output
$Red = "Red"
$Green = "Green"
$Yellow = "Yellow"
$Blue = "Blue"
$White = "White"

# Function to print colored output
function Write-Status {
    param([string]$Message)
    Write-Host "[INFO] $Message" -ForegroundColor $Blue
}

function Write-Success {
    param([string]$Message)
    Write-Host "[SUCCESS] $Message" -ForegroundColor $Green
}

function Write-Warning {
    param([string]$Message)
    Write-Host "[WARNING] $Message" -ForegroundColor $Yellow
}

function Write-Error {
    param([string]$Message)
    Write-Host "[ERROR] $Message" -ForegroundColor $Red
}

# Function to check if command exists
function Test-Command {
    param([string]$Command)
    return [bool](Get-Command $Command -ErrorAction SilentlyContinue)
}

# Function to check Docker and Docker Compose
function Test-Docker {
    Write-Status "Checking Docker installation..."
    
    if (-not (Test-Command "docker")) {
        Write-Error "Docker is not installed. Please install Docker Desktop first."
        exit 1
    }
    
    if (-not (Test-Command "docker-compose")) {
        Write-Error "Docker Compose is not installed. Please install Docker Compose first."
        exit 1
    }
    
    # Check if Docker daemon is running
    try {
        docker info | Out-Null
    }
    catch {
        Write-Error "Docker daemon is not running. Please start Docker Desktop first."
        exit 1
    }
    
    Write-Success "Docker and Docker Compose are available"
}

# Function to check environment file
function Test-EnvFile {
    Write-Status "Checking environment configuration..."
    
    if (-not (Test-Path ".env")) {
        if (Test-Path "env.example") {
            Write-Warning "No .env file found. Creating from env.example..."
            Copy-Item "env.example" ".env"
            Write-Warning "Please edit .env file with your configuration values before continuing."
            Write-Warning "Press Enter to continue or Ctrl+C to abort..."
            Read-Host
        }
        else {
            Write-Error "No .env file found and no env.example template available."
            exit 1
        }
    }
    else {
        Write-Success "Environment file found"
    }
}

# Function to validate environment variables
function Test-EnvVariables {
    Write-Status "Validating environment variables..."
    
    # Load environment variables from .env file
    if (Test-Path ".env") {
        Get-Content ".env" | ForEach-Object {
            if ($_ -match "^([^#][^=]+)=(.*)$") {
                $name = $matches[1]
                $value = $matches[2]
                Set-Variable -Name $name -Value $value -Scope Global
            }
        }
    }
    
    # Check required variables
    $missingVars = @()
    
    # Database variables
    if ([string]::IsNullOrEmpty($env:POSTGRES_PASSWORD) -or $env:POSTGRES_PASSWORD -eq "your_secure_database_password_here") {
        $missingVars += "POSTGRES_PASSWORD"
    }
    
    # LinkedIn API variables
    if ([string]::IsNullOrEmpty($env:LINKEDIN_API_KEY) -or $env:LINKEDIN_API_KEY -eq "your_linkedin_api_key_here") {
        $missingVars += "LINKEDIN_API_KEY"
    }
    
    if ([string]::IsNullOrEmpty($env:LINKEDIN_API_SECRET) -or $env:LINKEDIN_API_SECRET -eq "your_linkedin_api_secret_here") {
        $missingVars += "LINKEDIN_API_SECRET"
    }
    
    if ([string]::IsNullOrEmpty($env:LINKEDIN_PERSON_URN) -or $env:LINKEDIN_PERSON_URN -eq "urn:li:person:your_person_id_here") {
        $missingVars += "LINKEDIN_PERSON_URN"
    }
    
    # Security variables for enterprise deployment
    if ($env:ENVIRONMENT -eq "production") {
        if ([string]::IsNullOrEmpty($env:SECURITY_ENCRYPTION_KEY) -or $env:SECURITY_ENCRYPTION_KEY -eq "your-32-byte-encryption-key-here") {
            $missingVars += "SECURITY_ENCRYPTION_KEY"
        }
        
        if ([string]::IsNullOrEmpty($env:SECURITY_JWT_SECRET) -or $env:SECURITY_JWT_SECRET -eq "your-jwt-secret-key-here") {
            $missingVars += "SECURITY_JWT_SECRET"
        }
    }
    
    if ($missingVars.Count -gt 0) {
        Write-Error "Missing or default environment variables:"
        foreach ($var in $missingVars) {
            Write-Error "  - $var"
        }
        Write-Error "Please update your .env file with proper values."
        exit 1
    }
    
    Write-Success "Environment variables validated"
}

# Function to create necessary directories
function New-Directories {
    Write-Status "Creating necessary directories..."
    
    # Create logs and data directories for analytics fetcher
    New-Item -ItemType Directory -Force -Path "service/analytics_fetcher/logs" | Out-Null
    New-Item -ItemType Directory -Force -Path "service/analytics_fetcher/data" | Out-Null
    
    # Create custom directory if it doesn't exist
    New-Item -ItemType Directory -Force -Path "custom" | Out-Null
    
    # Create workflows directory if it doesn't exist
    New-Item -ItemType Directory -Force -Path "workflows" | Out-Null
    
    Write-Success "Directories created"
}

# Function to initialize database
function Initialize-Database {
    Write-Status "Initializing database..."
    
    # Start database service
    docker-compose up -d db
    
    # Wait for database to be ready
    Write-Status "Waiting for database to be ready..."
    Start-Sleep -Seconds 10
    
    # Check if database is healthy
    try {
        docker-compose exec db pg_isready -U $env:POSTGRES_USER -d $env:POSTGRES_DB | Out-Null
        Write-Success "Database is ready"
    }
    catch {
        Write-Warning "Database may not be fully ready, continuing anyway..."
    }
    
    # Initialize database schema if SQL file exists
    if (Test-Path "sql/init.sql") {
        Write-Status "Initializing database schema..."
        Get-Content "sql/init.sql" | docker-compose exec -T db psql -U $env:POSTGRES_USER -d $env:POSTGRES_DB
        Write-Success "Database schema initialized"
    }
}

# Function to deploy services
function Deploy-Services {
    Write-Status "Deploying all services..."
    
    # Stop any existing containers
    docker-compose down --remove-orphans
    
    # Build and start all services
    docker-compose up -d --build
    
    Write-Success "Services deployed"
}

# Function to wait for services to be healthy
function Wait-ForServices {
    Write-Status "Waiting for services to be healthy..."
    
    $maxAttempts = 30
    $attempt = 1
    
    while ($attempt -le $maxAttempts) {
        Write-Status "Checking service health (attempt $attempt/$maxAttempts)..."
        
        # Check if all services are running
        $services = docker-compose ps
        if ($services -match "Up") {
            Write-Success "All services are running"
            break
        }
        
        if ($attempt -eq $maxAttempts) {
            Write-Error "Services failed to start properly"
            docker-compose logs
            exit 1
        }
        
        Start-Sleep -Seconds 10
        $attempt++
    }
}

# Function to check service health
function Test-ServiceHealth {
    Write-Status "Checking service health..."
    
    # Check n8n health
    try {
        Invoke-WebRequest -Uri "http://localhost:5678/healthz" -UseBasicParsing | Out-Null
        Write-Success "n8n is healthy"
    }
    catch {
        Write-Warning "n8n health check failed"
    }
    
    # Check trending service health
    try {
        Invoke-WebRequest -Uri "http://localhost:8000/health" -UseBasicParsing | Out-Null
        Write-Success "Trending service is healthy"
    }
    catch {
        Write-Warning "Trending service health check failed"
    }
    
    # Check analytics fetcher health
    try {
        Invoke-WebRequest -Uri "http://localhost:8001/health" -UseBasicParsing | Out-Null
        Write-Success "Analytics fetcher is healthy"
    }
    catch {
        Write-Warning "Analytics fetcher health check failed"
    }
    
    # Check metabase health
    try {
        Invoke-WebRequest -Uri "http://localhost:3000/api/health" -UseBasicParsing | Out-Null
        Write-Success "Metabase is healthy"
    }
    catch {
        Write-Warning "Metabase health check failed"
    }
}

# Function to show deployment status
function Show-Status {
    Write-Status "Deployment Status:"
    Write-Host ""
    
    # Show running containers
    docker-compose ps
    
    Write-Host ""
    Write-Status "Service URLs:"
    Write-Host "  - n8n UI: http://localhost:5678"
    Write-Host "  - Trending API: http://localhost:8000"
    Write-Host "  - Analytics Fetcher: http://localhost:8001"
    Write-Host "  - Metabase: http://localhost:3000"
    Write-Host "  - Traefik Dashboard: http://localhost:8080"
    
    Write-Host ""
    Write-Status "Health Check URLs:"
    Write-Host "  - n8n Health: http://localhost:5678/healthz"
    Write-Host "  - Trending Health: http://localhost:8000/health"
    Write-Host "  - Analytics Health: http://localhost:8001/health"
    Write-Host "  - Analytics Metrics: http://localhost:8001/metrics"
    Write-Host "  - Metabase Health: http://localhost:3000/api/health"
    
    Write-Host ""
    Write-Status "Next Steps:"
    Write-Host "  1. Import workflows/linkedin_workflow.json into n8n"
    Write-Host "  2. Configure LinkedIn API credentials in n8n"
    Write-Host "  3. Set up Metabase dashboards"
    Write-Host "  4. Monitor service logs: docker-compose logs -f"
}

# Function to show logs
function Show-Logs {
    Write-Status "Recent logs from all services:"
    docker-compose logs --tail=50
}

# Function to clean up
function Remove-All {
    Write-Status "Cleaning up..."
    docker-compose down --volumes --remove-orphans
    Write-Success "Cleanup completed"
}

# Function to show help
function Show-Help {
    Write-Host "Usage: .\deploy.ps1 [OPTION]"
    Write-Host ""
    Write-Host "Options:"
    Write-Host "  deploy      Deploy all services (default)"
    Write-Host "  status      Show deployment status"
    Write-Host "  logs        Show recent logs"
    Write-Host "  health      Check service health"
    Write-Host "  cleanup     Stop and remove all containers"
    Write-Host "  help        Show this help message"
    Write-Host ""
    Write-Host "Examples:"
    Write-Host "  .\deploy.ps1 deploy    # Deploy all services"
    Write-Host "  .\deploy.ps1 status    # Show current status"
    Write-Host "  .\deploy.ps1 logs      # Show recent logs"
}

# Main deployment function
function Start-Deployment {
    Write-Status "Starting Growth Hacker Stack deployment..."
    
    Test-Docker
    Test-EnvFile
    Test-EnvVariables
    New-Directories
    Initialize-Database
    Deploy-Services
    Wait-ForServices
    Test-ServiceHealth
    Show-Status
    
    Write-Success "Deployment completed successfully!"
}

# Main script logic
switch ($Action) {
    "deploy" {
        Start-Deployment
    }
    "status" {
        Show-Status
    }
    "logs" {
        Show-Logs
    }
    "health" {
        Test-ServiceHealth
    }
    "cleanup" {
        Remove-All
    }
    "help" {
        Show-Help
    }
    default {
        Write-Error "Unknown option: $Action"
        Show-Help
        exit 1
    }
} 