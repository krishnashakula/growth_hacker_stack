import asyncio
import json
import logging
import os
import signal
import sys
import time
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from dataclasses import dataclass, asdict

import uvicorn
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse
from pydantic import BaseModel


@dataclass
class ServiceStatus:
    """Service status information."""
    service: str
    status: str
    timestamp: str
    uptime_seconds: float
    last_fetch_time: Optional[str] = None
    fetch_count: int = 0
    error_count: int = 0
    version: str = "1.0.0"


class HealthResponse(BaseModel):
    """Health check response model."""
    status: str
    timestamp: str
    service: str
    version: str
    uptime_seconds: float
    last_fetch_time: Optional[str] = None
    fetch_count: int = 0
    error_count: int = 0


class HealthServer:
    """Health check server for monitoring the analytics fetcher service."""
    
    def __init__(self, port: int = 8000):
        self.port = port
        self.app = FastAPI(title="Analytics Fetcher Health", version="1.0.0")
        self.start_time = time.time()
        self.service_status = ServiceStatus(
            service="analytics_fetcher",
            status="healthy",
            timestamp=datetime.utcnow().isoformat(),
            uptime_seconds=0.0
        )
        self._setup_routes()
        self._setup_logging()
    
    def _setup_logging(self):
        """Setup logging for the health server."""
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        self.logger = logging.getLogger("health_server")
    
    def _setup_routes(self):
        """Setup FastAPI routes."""
        
        @self.app.get("/health", response_model=HealthResponse)
        async def health_check():
            """Health check endpoint."""
            self.service_status.uptime_seconds = time.time() - self.start_time
            self.service_status.timestamp = datetime.utcnow().isoformat()
            
            return HealthResponse(**asdict(self.service_status))
        
        @self.app.get("/health/detailed")
        async def detailed_health():
            """Detailed health check with additional information."""
            self.service_status.uptime_seconds = time.time() - self.start_time
            self.service_status.timestamp = datetime.utcnow().isoformat()
            
            return {
                "status": "healthy",
                "service": "analytics_fetcher",
                "version": self.service_status.version,
                "timestamp": self.service_status.timestamp,
                "uptime_seconds": self.service_status.uptime_seconds,
                "uptime_formatted": str(timedelta(seconds=int(self.service_status.uptime_seconds))),
                "last_fetch_time": self.service_status.last_fetch_time,
                "fetch_count": self.service_status.fetch_count,
                "error_count": self.service_status.error_count,
                "environment": {
                    "python_version": sys.version,
                    "platform": sys.platform,
                    "env_vars": {
                        "LOG_LEVEL": os.getenv("LOG_LEVEL", "INFO"),
                        "FETCH_INTERVAL_SECONDS": os.getenv("FETCH_INTERVAL_SECONDS", "3600"),
                        "ANALYTICS_FETCHER_RUN_MODE": os.getenv("ANALYTICS_FETCHER_RUN_MODE", "loop")
                    }
                }
            }
        
        @self.app.post("/health/update")
        async def update_health_status(status_update: Dict[str, Any]):
            """Update health status (called by main service)."""
            try:
                if "last_fetch_time" in status_update:
                    self.service_status.last_fetch_time = status_update["last_fetch_time"]
                if "fetch_count" in status_update:
                    self.service_status.fetch_count = status_update["fetch_count"]
                if "error_count" in status_update:
                    self.service_status.error_count = status_update["error_count"]
                if "status" in status_update:
                    self.service_status.status = status_update["status"]
                
                self.logger.info(f"Health status updated: {status_update}")
                return {"status": "updated"}
            except Exception as e:
                self.logger.error(f"Failed to update health status: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.get("/metrics")
        async def metrics():
            """Prometheus-style metrics endpoint."""
            uptime = time.time() - self.start_time
            
            metrics = [
                f"# HELP analytics_fetcher_uptime_seconds Total uptime in seconds",
                f"# TYPE analytics_fetcher_uptime_seconds counter",
                f"analytics_fetcher_uptime_seconds {uptime}",
                "",
                f"# HELP analytics_fetcher_fetch_total Total number of fetch operations",
                f"# TYPE analytics_fetcher_fetch_total counter",
                f"analytics_fetcher_fetch_total {self.service_status.fetch_count}",
                "",
                f"# HELP analytics_fetcher_errors_total Total number of errors",
                f"# TYPE analytics_fetcher_errors_total counter",
                f"analytics_fetcher_errors_total {self.service_status.error_count}",
                "",
                f"# HELP analytics_fetcher_health_status Service health status (1=healthy, 0=unhealthy)",
                f"# TYPE analytics_fetcher_health_status gauge",
                f"analytics_fetcher_health_status {1 if self.service_status.status == 'healthy' else 0}"
            ]
            
            return "\n".join(metrics)
    
    def update_status(self, **kwargs):
        """Update service status."""
        for key, value in kwargs.items():
            if hasattr(self.service_status, key):
                setattr(self.service_status, key, value)
    
    async def start(self):
        """Start the health server."""
        config = uvicorn.Config(
            self.app,
            host="0.0.0.0",
            port=self.port,
            log_level="info",
            access_log=True
        )
        server = uvicorn.Server(config)
        await server.serve()
    
    def run(self):
        """Run the health server."""
        uvicorn.run(
            self.app,
            host="0.0.0.0",
            port=self.port,
            log_level="info"
        )


async def main():
    """Main entry point for health server."""
    port = int(os.getenv("HEALTH_PORT", "8000"))
    server = HealthServer(port=port)
    
    # Setup signal handlers
    def signal_handler(signum, frame):
        server.logger.info(f"Received signal {signum}, shutting down health server...")
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    server.logger.info(f"Starting health server on port {port}")
    await server.start()


if __name__ == "__main__":
    asyncio.run(main()) 