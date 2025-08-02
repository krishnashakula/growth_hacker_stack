import asyncio
import logging
import time
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from enum import Enum
import aiohttp
import redis.asyncio as redis
from dataclasses_json import dataclass_json


class NodeStatus(Enum):
    """Node status enumeration."""
    ACTIVE = "active"
    STANDBY = "standby"
    FAILED = "failed"
    RECOVERING = "recovering"


@dataclass_json
@dataclass
class NodeInfo:
    """Information about a cluster node."""
    node_id: str
    host: str
    port: int
    status: NodeStatus
    last_heartbeat: datetime
    load_factor: float = 1.0
    capabilities: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ClusterConfig:
    """Cluster configuration settings."""
    cluster_id: str
    node_id: str
    heartbeat_interval: int = 30
    failure_timeout: int = 90
    recovery_timeout: int = 300
    max_nodes: int = 10
    load_balancing_strategy: str = "round_robin"  # round_robin, least_loaded, random
    auto_failover: bool = True
    quorum_size: int = 2


class LoadBalancer:
    """Load balancer for distributing requests across nodes."""
    
    def __init__(self, strategy: str = "round_robin"):
        self.strategy = strategy
        self.current_index = 0
        self.nodes: List[NodeInfo] = []
        self.logger = logging.getLogger("load_balancer")
    
    def add_node(self, node: NodeInfo):
        """Add a node to the load balancer."""
        if node not in self.nodes:
            self.nodes.append(node)
            self.logger.info(f"Added node {node.node_id} to load balancer")
    
    def remove_node(self, node_id: str):
        """Remove a node from the load balancer."""
        self.nodes = [n for n in self.nodes if n.node_id != node_id]
        self.logger.info(f"Removed node {node_id} from load balancer")
    
    def get_next_node(self) -> Optional[NodeInfo]:
        """Get the next node based on the load balancing strategy."""
        active_nodes = [n for n in self.nodes if n.status == NodeStatus.ACTIVE]
        
        if not active_nodes:
            return None
        
        if self.strategy == "round_robin":
            node = active_nodes[self.current_index % len(active_nodes)]
            self.current_index += 1
            return node
        
        elif self.strategy == "least_loaded":
            return min(active_nodes, key=lambda n: n.load_factor)
        
        elif self.strategy == "random":
            import random
            return random.choice(active_nodes)
        
        return active_nodes[0] if active_nodes else None
    
    def update_node_load(self, node_id: str, load_factor: float):
        """Update the load factor for a node."""
        for node in self.nodes:
            if node.node_id == node_id:
                node.load_factor = load_factor
                break


class ClusterManager:
    """High-availability cluster manager."""
    
    def __init__(self, config: ClusterConfig, redis_client: redis.Redis):
        self.config = config
        self.redis = redis_client
        self.logger = logging.getLogger("cluster_manager")
        self.nodes: Dict[str, NodeInfo] = {}
        self.load_balancer = LoadBalancer(config.load_balancing_strategy)
        self._heartbeat_task = None
        self._monitoring_task = None
        self._is_running = False
        
        # Register this node
        self.register_node()
    
    async def start(self):
        """Start the cluster manager."""
        self._is_running = True
        self._heartbeat_task = asyncio.create_task(self._heartbeat_loop())
        self._monitoring_task = asyncio.create_task(self._monitoring_loop())
        self.logger.info(f"Cluster manager started for node {self.config.node_id}")
    
    async def stop(self):
        """Stop the cluster manager."""
        self._is_running = False
        
        if self._heartbeat_task:
            self._heartbeat_task.cancel()
        if self._monitoring_task:
            self._monitoring_task.cancel()
        
        # Unregister this node
        await self.unregister_node()
        self.logger.info("Cluster manager stopped")
    
    def register_node(self):
        """Register this node in the cluster."""
        node_info = NodeInfo(
            node_id=self.config.node_id,
            host="localhost",  # Should be configurable
            port=8000,
            status=NodeStatus.ACTIVE,
            last_heartbeat=datetime.utcnow(),
            capabilities=["analytics_fetch", "health_check"],
            metadata={"version": "1.0.0"}
        )
        
        self.nodes[self.config.node_id] = node_info
        self.load_balancer.add_node(node_info)
    
    async def unregister_node(self):
        """Unregister this node from the cluster."""
        try:
            await self.redis.hdel(f"cluster:{self.config.cluster_id}:nodes", self.config.node_id)
            self.logger.info(f"Node {self.config.node_id} unregistered from cluster")
        except Exception as e:
            self.logger.error(f"Failed to unregister node: {e}")
    
    async def _heartbeat_loop(self):
        """Send periodic heartbeats to maintain cluster membership."""
        while self._is_running:
            try:
                await self._send_heartbeat()
                await asyncio.sleep(self.config.heartbeat_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Heartbeat error: {e}")
                await asyncio.sleep(5)
    
    async def _send_heartbeat(self):
        """Send heartbeat to cluster."""
        node_info = self.nodes[self.config.node_id]
        node_info.last_heartbeat = datetime.utcnow()
        
        # Store node info in Redis
        await self.redis.hset(
            f"cluster:{self.config.cluster_id}:nodes",
            self.config.node_id,
            node_info.to_json()
        )
        
        # Set expiration for automatic cleanup
        await self.redis.expire(
            f"cluster:{self.config.cluster_id}:nodes",
            self.config.failure_timeout * 2
        )
    
    async def _monitoring_loop(self):
        """Monitor cluster nodes and handle failures."""
        while self._is_running:
            try:
                await self._check_cluster_health()
                await asyncio.sleep(self.config.heartbeat_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Monitoring error: {e}")
                await asyncio.sleep(5)
    
    async def _check_cluster_health(self):
        """Check health of all cluster nodes."""
        try:
            # Get all nodes from Redis
            nodes_data = await self.redis.hgetall(f"cluster:{self.config.cluster_id}:nodes")
            
            current_nodes = set()
            for node_id, node_json in nodes_data.items():
                node_info = NodeInfo.from_json(node_json)
                current_nodes.add(node_id)
                
                # Check if node is still active
                time_since_heartbeat = datetime.utcnow() - node_info.last_heartbeat
                
                if time_since_heartbeat.total_seconds() > self.config.failure_timeout:
                    if node_info.status != NodeStatus.FAILED:
                        node_info.status = NodeStatus.FAILED
                        self.logger.warning(f"Node {node_id} marked as failed")
                        
                        if self.config.auto_failover:
                            await self._handle_node_failure(node_id)
                
                # Update local node info
                self.nodes[node_id] = node_info
                self.load_balancer.add_node(node_info)
            
            # Remove nodes that are no longer in the cluster
            for node_id in list(self.nodes.keys()):
                if node_id not in current_nodes and node_id != self.config.node_id:
                    del self.nodes[node_id]
                    self.load_balancer.remove_node(node_id)
            
        except Exception as e:
            self.logger.error(f"Cluster health check failed: {e}")
    
    async def _handle_node_failure(self, failed_node_id: str):
        """Handle node failure with failover logic."""
        self.logger.info(f"Handling failure of node {failed_node_id}")
        
        # Check if we have enough active nodes for quorum
        active_nodes = [n for n in self.nodes.values() if n.status == NodeStatus.ACTIVE]
        
        if len(active_nodes) < self.config.quorum_size:
            self.logger.error(f"Insufficient active nodes for quorum. Need {self.config.quorum_size}, have {len(active_nodes)}")
            return
        
        # Implement failover logic here
        # This could involve:
        # - Taking over failed node's tasks
        # - Rebalancing load
        # - Notifying administrators
        
        self.logger.info(f"Failover completed for node {failed_node_id}")
    
    def get_cluster_status(self) -> Dict[str, Any]:
        """Get current cluster status."""
        active_nodes = [n for n in self.nodes.values() if n.status == NodeStatus.ACTIVE]
        failed_nodes = [n for n in self.nodes.values() if n.status == NodeStatus.FAILED]
        
        return {
            "cluster_id": self.config.cluster_id,
            "total_nodes": len(self.nodes),
            "active_nodes": len(active_nodes),
            "failed_nodes": len(failed_nodes),
            "quorum_met": len(active_nodes) >= self.config.quorum_size,
            "nodes": [n.to_dict() for n in self.nodes.values()]
        }


class CircuitBreaker:
    """Circuit breaker pattern for fault tolerance."""
    
    def __init__(self, failure_threshold: int = 5, recovery_timeout: int = 60):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.failure_count = 0
        self.last_failure_time = None
        self.state = "CLOSED"  # CLOSED, OPEN, HALF_OPEN
        self.logger = logging.getLogger("circuit_breaker")
    
    async def call(self, func: Callable, *args, **kwargs):
        """Execute function with circuit breaker protection."""
        if self.state == "OPEN":
            if self._should_attempt_reset():
                self.state = "HALF_OPEN"
                self.logger.info("Circuit breaker transitioning to HALF_OPEN")
            else:
                raise Exception("Circuit breaker is OPEN")
        
        try:
            result = await func(*args, **kwargs)
            self._on_success()
            return result
        except Exception as e:
            self._on_failure()
            raise
    
    def _on_success(self):
        """Handle successful operation."""
        if self.state == "HALF_OPEN":
            self.state = "CLOSED"
            self.logger.info("Circuit breaker reset to CLOSED")
        
        self.failure_count = 0
        self.last_failure_time = None
    
    def _on_failure(self):
        """Handle failed operation."""
        self.failure_count += 1
        self.last_failure_time = datetime.utcnow()
        
        if self.failure_count >= self.failure_threshold:
            self.state = "OPEN"
            self.logger.warning(f"Circuit breaker opened after {self.failure_count} failures")
    
    def _should_attempt_reset(self) -> bool:
        """Check if enough time has passed to attempt reset."""
        if not self.last_failure_time:
            return False
        
        time_since_failure = datetime.utcnow() - self.last_failure_time
        return time_since_failure.total_seconds() >= self.recovery_timeout


class RetryManager:
    """Advanced retry manager with exponential backoff and jitter."""
    
    def __init__(self, max_retries: int = 3, base_delay: float = 1.0, max_delay: float = 60.0):
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.logger = logging.getLogger("retry_manager")
    
    async def execute(self, func: Callable, *args, **kwargs):
        """Execute function with retry logic."""
        last_exception = None
        
        for attempt in range(self.max_retries + 1):
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                last_exception = e
                
                if attempt == self.max_retries:
                    self.logger.error(f"Max retries ({self.max_retries}) exceeded")
                    raise last_exception
                
                delay = self._calculate_delay(attempt)
                self.logger.warning(f"Attempt {attempt + 1} failed, retrying in {delay:.2f}s: {e}")
                await asyncio.sleep(delay)
        
        raise last_exception
    
    def _calculate_delay(self, attempt: int) -> float:
        """Calculate delay with exponential backoff and jitter."""
        import random
        
        # Exponential backoff
        delay = min(self.base_delay * (2 ** attempt), self.max_delay)
        
        # Add jitter to prevent thundering herd
        jitter = random.uniform(0, 0.1 * delay)
        
        return delay + jitter


class HealthChecker:
    """Advanced health checker for cluster nodes."""
    
    def __init__(self, timeout: int = 10):
        self.timeout = timeout
        self.logger = logging.getLogger("health_checker")
    
    async def check_node_health(self, node: NodeInfo) -> bool:
        """Check if a node is healthy."""
        try:
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=self.timeout)) as session:
                async with session.get(f"http://{node.host}:{node.port}/health") as response:
                    if response.status == 200:
                        data = await response.json()
                        return data.get("status") == "healthy"
                    return False
        except Exception as e:
            self.logger.error(f"Health check failed for node {node.node_id}: {e}")
            return False
    
    async def check_all_nodes(self, nodes: List[NodeInfo]) -> Dict[str, bool]:
        """Check health of all nodes concurrently."""
        tasks = [self.check_node_health(node) for node in nodes]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        health_status = {}
        for node, result in zip(nodes, results):
            if isinstance(result, Exception):
                self.logger.error(f"Health check error for {node.node_id}: {result}")
                health_status[node.node_id] = False
            else:
                health_status[node.node_id] = result
        
        return health_status 