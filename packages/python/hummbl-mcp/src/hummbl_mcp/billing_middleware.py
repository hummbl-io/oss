"""Billing middleware for MCP server.

This middleware intercepts tool calls, validates API keys, checks tier limits,
and records usage for billing purposes.
"""

from __future__ import annotations

from typing import Any, Callable

try:

    from hummbl_integrations.cost_tracker import CostTracker

except ImportError:

    pass


class BillingMiddleware:
    """Middleware for API key validation and usage metering."""
    
    def __init__(
        self,
        cost_tracker: CostTracker,
        require_api_key: bool = True,
    ) -> None:
        """Initialize billing middleware.
        
        Parameters
        ----------
        cost_tracker : CostTracker
            Cost tracker instance for billing operations.
        require_api_key : bool
            If True, require valid API key for all tool calls.
            If False, allow anonymous access (for free tier or testing).
        """
        self.cost_tracker = cost_tracker
        self.require_api_key = require_api_key
    
    def wrap_handler(
        self,
        tool_name: str,
        handler: Callable[[dict[str, Any]], Any],
    ) -> Callable[[dict[str, Any]], Any]:
        """Wrap a tool handler with billing middleware.
        
        Parameters
        ----------
        tool_name : str
            Name of the tool being wrapped.
        handler : Callable
            Original tool handler function.
            
        Returns
        -------
        Callable
            Wrapped handler with billing logic.
        """
        def wrapped_handler(args: dict[str, Any]) -> Any:
            # Extract API key from arguments if present
            api_key = args.get("api_key")
            
            # Skip billing for billing tools themselves (avoid recursion)
            if tool_name.startswith("billing_"):
                return handler(args)
            
            # Validate API key if required
            if self.require_api_key:
                if not api_key:
                    return {
                        "error": "API key required",
                        "error_code": "MISSING_API_KEY",
                    }
                
                key_info = self.cost_tracker.validate_api_key(api_key)
                if key_info is None:
                    return {
                        "error": "Invalid or expired API key",
                        "error_code": "INVALID_API_KEY",
                    }
                
                # Check tier limits
                limit_status = self.cost_tracker.check_tier_limits(key_info["key_id"])
                if not limit_status["allowed"]:
                    return {
                        "error": limit_status["reason"],
                        "error_code": "TIER_LIMIT_EXCEEDED",
                        "limit_status": limit_status,
                    }
                
                # Execute the original handler
                result = handler(args)
                
                # Record usage (estimate tokens based on result size)
                # In production, this would use actual token counts from the LLM
                estimated_tokens = self._estimate_tokens(result)
                estimated_cost = self._estimate_cost(estimated_tokens, key_info["tier_id"])
                
                self.cost_tracker.record_usage_metering(
                    api_key_id=key_info["key_id"],
                    endpoint=f"/tools/{tool_name}",
                    tokens_used=estimated_tokens,
                    cost_usd=estimated_cost,
                )
                
                return result
            else:
                # No API key required - execute handler directly
                return handler(args)
        
        return wrapped_handler
    
    def _estimate_tokens(self, result: Any) -> int:
        """Estimate token count from result.
        
        This is a rough estimate. In production, use actual token counts
        from the LLM API response.
        
        Parameters
        ----------
        result : Any
            Tool result.
            
        Returns
        -------
        int
            Estimated token count.
        """
        import json
        
        if result is None:
            return 0
        
        # Convert result to string and estimate tokens
        result_str = json.dumps(result, default=str)
        # Rough estimate: 1 token ≈ 4 characters
        return len(result_str) // 4
    
    def _estimate_cost(self, tokens: int, tier_id: str) -> float:
        """Estimate cost based on token count and tier.
        
        Parameters
        ----------
        tokens : int
            Number of tokens used.
        tier_id : str
            Tier identifier for pricing.
            
        Returns
        -------
        float
            Estimated cost in USD.
        """
        # Get tier info to determine pricing
        tier = self.cost_tracker.get_tier(tier_id)
        if tier is None:
            # Default pricing if tier not found
            return (tokens / 1000) * 0.001  # $0.001 per 1K tokens
        
        # Free tier has no cost
        if tier["monthly_price_usd"] == 0:
            return 0.0
        
        # Pro tier: $0.002 per 1K tokens
        if tier["tier_id"] == "pro":
            return (tokens / 1000) * 0.002
        
        # Enterprise tier: $0.001 per 1K tokens (volume discount)
        if tier["tier_id"] == "enterprise":
            return (tokens / 1000) * 0.001
        
        # Default pricing
        return (tokens / 1000) * 0.001


def apply_billing_middleware(
    tool_definitions: list[Any],
    handlers: dict[str, Callable[[dict[str, Any]], Any]],
    middleware: BillingMiddleware,
) -> tuple[list[Any], dict[str, Callable[[dict[str, Any]], Any]]]:
    """Apply billing middleware to all tool handlers.
    
    Parameters
    ----------
    tool_definitions : list
        List of tool definitions.
    handlers : dict
        Dictionary of tool name → handler.
    middleware : BillingMiddleware
        Billing middleware instance.
        
    Returns
    -------
    tuple
        Updated tool definitions and wrapped handlers.
    """
    wrapped_handlers = {}
    
    for tool_name, handler in handlers.items():
        wrapped_handlers[tool_name] = middleware.wrap_handler(tool_name, handler)
    
    return tool_definitions, wrapped_handlers