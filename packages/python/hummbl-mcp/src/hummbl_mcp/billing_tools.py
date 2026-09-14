"""MCP tools for billing and subscription management.

These tools provide tier management, API key validation, and usage metering
for the MCP server billing layer.
"""

from __future__ import annotations

import json
from typing import Any

from hummbl_mcp.protocol import ToolDefinition
try:
    from hummbl_integrations.cost_tracker import CostTracker
except ImportError:
    pass


def get_tool_definitions() -> list[ToolDefinition]:
    """Get tool definitions for billing tools."""
    return [
        ToolDefinition(
            name="billing_list_tiers",
            description="List all available subscription tiers with pricing and limits",
            input_schema={
                "type": "object",
                "properties": {},
            },
        ),
        ToolDefinition(
            name="billing_validate_api_key",
            description="Validate an API key and return associated tier information",
            input_schema={
                "type": "object",
                "properties": {
                    "api_key": {
                        "type": "string",
                        "description": "The API key to validate",
                    },
                },
                "required": ["api_key"],
            },
        ),
        ToolDefinition(
            name="billing_check_usage",
            description="Check current month's usage for an API key",
            input_schema={
                "type": "object",
                "properties": {
                    "api_key": {
                        "type": "string",
                        "description": "The API key to check usage for",
                    },
                },
                "required": ["api_key"],
            },
        ),
        ToolDefinition(
            name="billing_check_limits",
            description="Check if an API key is within its tier limits",
            input_schema={
                "type": "object",
                "properties": {
                    "api_key": {
                        "type": "string",
                        "description": "The API key to check limits for",
                    },
                },
                "required": ["api_key"],
            },
        ),
    ]


def get_handlers(cost_tracker: CostTracker) -> dict[str, Any]:
    """Get handler functions for billing tools."""
    
    def handle_list_tiers(args: dict[str, Any]) -> dict[str, Any]:
        """List all available subscription tiers."""
        tiers = cost_tracker.list_tiers()
        return {
            "tiers": tiers,
            "count": len(tiers),
        }
    
    def handle_validate_api_key(args: dict[str, Any]) -> dict[str, Any]:
        """Validate an API key and return tier information."""
        api_key = args.get("api_key")
        if not api_key:
            return {
                "valid": False,
                "error": "api_key is required",
            }
        
        key_info = cost_tracker.validate_api_key(api_key)
        if key_info is None:
            return {
                "valid": False,
                "error": "Invalid or expired API key",
            }
        
        return {
            "valid": True,
            "key_info": key_info,
        }
    
    def handle_check_usage(args: dict[str, Any]) -> dict[str, Any]:
        """Check current month's usage for an API key."""
        api_key = args.get("api_key")
        if not api_key:
            return {
                "error": "api_key is required",
            }
        
        key_info = cost_tracker.validate_api_key(api_key)
        if key_info is None:
            return {
                "error": "Invalid or expired API key",
            }
        
        from datetime import datetime, timezone
        now = datetime.now(timezone.utc)
        monthly_usage = cost_tracker.get_monthly_usage(
            api_key_id=key_info["key_id"],
            year=now.year,
            month=now.month,
        )
        
        return {
            "api_key_id": key_info["key_id"],
            "tier_id": key_info["tier_id"],
            "tier_name": key_info["tier_name"],
            "requests_per_month": key_info["requests_per_month"],
            "usage": monthly_usage,
        }
    
    def handle_check_limits(args: dict[str, Any]) -> dict[str, Any]:
        """Check if an API key is within its tier limits."""
        api_key = args.get("api_key")
        if not api_key:
            return {
                "error": "api_key is required",
            }
        
        key_info = cost_tracker.validate_api_key(api_key)
        if key_info is None:
            return {
                "error": "Invalid or expired API key",
            }
        
        limit_status = cost_tracker.check_tier_limits(key_info["key_id"])
        
        return {
            "api_key_id": key_info["key_id"],
            "tier_id": key_info["tier_id"],
            "tier_name": key_info["tier_name"],
            "limit_status": limit_status,
        }
    
    return {
        "billing_list_tiers": handle_list_tiers,
        "billing_validate_api_key": handle_validate_api_key,
        "billing_check_usage": handle_check_usage,
        "billing_check_limits": handle_check_limits,
    }