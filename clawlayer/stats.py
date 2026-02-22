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
    
    def record(self, message, router_name, latency_ms, content=None, request_data=None, response_data=None, tried_routers=None, route_result=None):
        """Record a routing request."""
        self.requests += 1
        self.router_hits[router_name] += 1
        self.latencies.append(latency_ms)
        
        # Extract stage data from route result
        stage_data = []
        if route_result:
            if hasattr(route_result, 'all_stage_data') and route_result.all_stage_data:
                stage_data = route_result.all_stage_data
            elif hasattr(route_result, 'stage_details') and route_result.stage_details:
                stage_data = route_result.stage_details
        
        self.logs.append({
            'timestamp': time.time(),
            'message': message[:100],  # Truncate for list view
            'router': router_name,
            'latency_ms': round(latency_ms, 2),
            'content': content[:50] if content else None,
            'full_message': message,  # Full message for detail view
            'full_content': content,  # Full content for detail view
            'request': request_data,  # Full request data
            'response': response_data,  # Full response data
            'tried_routers': tried_routers or [],  # List of routers tried
            'stage_data': stage_data  # Structured stage data
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
