"""Router chain for managing multiple routers."""

from typing import List
from clawlayer.routers import Router, RouteResult


class RouterChain:
    """Chains multiple routers with priority order."""
    
    def __init__(self, routers: List[Router]):
        self.routers = routers
    
    def route(self, message: str, context: dict) -> RouteResult:
        """Try each router in order until one matches."""
        tried_routers = []
        all_stage_data = []
        
        for router in self.routers:
            router_name = router.__class__.__name__
            result = router.route(message, context)
            
            # Collect stage details if available
            stage_info = ""
            router_stage_data = []
            
            if result and hasattr(result, 'stage_details') and result.stage_details:
                # Convert structured stage details to display format
                stage_summaries = []
                for detail in result.stage_details:
                    if isinstance(detail, dict):
                        summary = f"Stage {detail['stage']} ({detail['type']})"
                        if 'latency_ms' in detail:
                            summary += f": {detail['latency_ms']}ms"
                        if 'model' in detail:
                            summary += f", model={detail['model']}"
                        if 'confidence' in detail:
                            summary += f", confidence={detail['confidence']:.3f}"
                        summary += f", {detail.get('result', 'unknown')}"
                        stage_summaries.append(summary)
                    else:
                        stage_summaries.append(str(detail))
                stage_info = f" [{'; '.join(stage_summaries)}]"
                router_stage_data = result.stage_details
            elif not result and hasattr(router, '_last_stage_details') and router._last_stage_details:
                # For failed semantic routers, get stored stage details
                stage_summaries = []
                for detail in router._last_stage_details:
                    if isinstance(detail, dict):
                        summary = f"Stage {detail['stage']} ({detail['type']})"
                        if 'latency_ms' in detail:
                            summary += f": {detail['latency_ms']}ms"
                        if 'model' in detail:
                            summary += f", model={detail['model']}"
                        if 'confidence' in detail:
                            summary += f", confidence={detail['confidence']:.3f}"
                        summary += f", {detail.get('result', 'unknown')}"
                        stage_summaries.append(summary)
                    else:
                        stage_summaries.append(str(detail))
                stage_info = f" [{'; '.join(stage_summaries)}]"
                router_stage_data = router._last_stage_details
            
            tried_routers.append(f"{router_name}{stage_info}")
            all_stage_data.extend(router_stage_data)
            
            if result:
                result.tried_routers = tried_routers
                result.all_stage_data = all_stage_data
                return result
        
        # Default: proxy to LLM
        fallback = RouteResult(name="fallback", should_proxy=True)
        fallback.tried_routers = tried_routers
        fallback.all_stage_data = all_stage_data
        return fallback
