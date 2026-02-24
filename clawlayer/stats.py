"""Statistics collection for ClawLayer."""

from collections import defaultdict, deque
import time

# Cost per 1M tokens (approximate industry averages)
COST_FAST = 0.0  # Quick/echo routers - zero cost
COST_SEMANTIC = 0.02  # Embedding models - $0.02/1M tokens
COST_LLM = 0.50  # LLM fallback - $0.50/1M tokens (avg of cheap models)


class StatsCollector:
    """Collect and track routing statistics."""
    
    def __init__(self, max_logs=1000):
        self.requests = 0
        self.router_hits = defaultdict(int)
        self.latencies = []
        self.logs = deque(maxlen=max_logs)
        self.start_time = time.time()
        self.log_id_counter = 0
        self.cost_saved = 0.0  # Total cost saved vs always using LLM
    
    def record(self, message, router_name, latency_ms, content=None, request_data=None, response_data=None, tried_routers=None, route_result=None):
        """Record a routing request."""
        self.requests += 1
        self.router_hits[router_name] += 1
        self.latencies.append(latency_ms)
        
        # Calculate cost savings
        tokens = len(message.split()) * 1.3  # Rough token estimate
        cost_actual = self._calculate_cost(router_name, tokens)
        cost_llm = (tokens / 1_000_000) * COST_LLM
        self.cost_saved += (cost_llm - cost_actual)
        
        # Extract stage data from route result
        stage_data = []
        if route_result:
            if hasattr(route_result, 'all_stage_data') and route_result.all_stage_data:
                stage_data = route_result.all_stage_data
            elif hasattr(route_result, 'stage_details') and route_result.stage_details:
                stage_data = route_result.stage_details
        
        self.log_id_counter += 1
        self.logs.append({
            'id': self.log_id_counter,
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
    
    def _calculate_cost(self, router_name, tokens):
        """Calculate cost for a router."""
        if router_name in ['quick', 'echo', 'command', 'EchoHandler', 'CommandHandler', 'QuickHandler']:
            return 0.0
        elif router_name in ['greeting', 'summarize', 'GreetingRouter', 'SummarizeRouter']:
            return (tokens / 1_000_000) * COST_SEMANTIC
        else:  # LLM fallback
            return (tokens / 1_000_000) * COST_LLM
    
    def to_dict(self):
        """Convert stats to dictionary."""
        # Calculate distribution
        total = self.requests or 1
        handlers_hits = sum(self.router_hits.get(r, 0) for r in ['quick', 'echo', 'command', 'EchoHandler', 'CommandHandler', 'QuickHandler'])
        semantic_hits = sum(self.router_hits.get(r, 0) for r in ['greeting', 'summarize', 'GreetingRouter', 'SummarizeRouter'])
        llm_hits = total - handlers_hits - semantic_hits
        
        return {
            'requests': self.requests,
            'router_hits': dict(self.router_hits),
            'avg_latency': round(self.avg_latency(), 2),
            'uptime': round(time.time() - self.start_time, 0),
            'cost_saved': round(self.cost_saved, 4),
            'distribution': {
                'handlers_pct': round(100 * handlers_hits / total, 1),
                'semantic_pct': round(100 * semantic_hits / total, 1),
                'llm_pct': round(100 * llm_hits / total, 1)
            }
        }
    
    def delete_log(self, log_id: int) -> bool:
        """Delete a log entry by ID."""
        for i, log in enumerate(self.logs):
            if log['id'] == log_id:
                del self.logs[i]
                return True
        return False
    
    def get_recent_logs(self, limit=50):
        """Get recent logs."""
        return list(self.logs)[-limit:]
