"""Statistics collection for ClawLayer."""

from collections import defaultdict, deque
import time


class StatsCollector:
    """Collect and track routing statistics."""
    
    def __init__(self, max_logs=1000):
        self.requests = 0
        self.router_hits = defaultdict(int)
        self.latencies = []
        self.logs = deque(maxlen=max_logs)
        self.start_time = time.time()
    
    def record(self, message, router_name, latency_ms, content=None):
        """Record a routing request."""
        self.requests += 1
        self.router_hits[router_name] += 1
        self.latencies.append(latency_ms)
        
        self.logs.append({
            'timestamp': time.time(),
            'message': message[:100],  # Truncate long messages
            'router': router_name,
            'latency_ms': round(latency_ms, 2),
            'content': content[:50] if content else None
        })
    
    def avg_latency(self):
        """Calculate average latency."""
        if not self.latencies:
            return 0
        return sum(self.latencies) / len(self.latencies)
    
    def to_dict(self):
        """Convert stats to dictionary."""
        return {
            'requests': self.requests,
            'router_hits': dict(self.router_hits),
            'avg_latency': round(self.avg_latency(), 2),
            'uptime': round(time.time() - self.start_time, 0)
        }
    
    def get_recent_logs(self, limit=50):
        """Get recent logs."""
        return list(self.logs)[-limit:]
