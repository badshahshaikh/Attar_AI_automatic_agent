"""
agents/tool_registry.py
-----------------------
Tool registry for registering and executing agent tools.
"""

import json
import logging
from typing import Any, Callable

from attar_ai.app.core.exceptions import ValidationError
from attar_ai.app.core.logging import get_logger

logger = get_logger(__name__)


class ToolRegistry:
    """Register tools and execute tool calls."""

    def __init__(self):
        self._tools: dict[str, Callable[[dict[str, Any]], str]] = {}
        self._schemas: dict[str, dict[str, Any]] = {}

    def register(self, name: str, func: Callable[[dict[str, Any]], str], schema: dict[str, Any]) -> None:
        """Register a tool with its execution function and OpenAI schema."""
        # Validate schema has required function.name
        self._validate_tool_schema(name, schema)
        self._tools[name] = func
        self._schemas[name] = schema
        logger.debug("Registered tool: %s", name)

    def _validate_tool_schema(self, name: str, schema: dict[str, Any]) -> None:
        """Validate that a tool schema has a valid function.name."""
        if not isinstance(schema, dict):
            raise ValidationError(f"Tool schema must be a dict, got {type(schema).__name__}", field="schema")
        
        function = schema.get("function")
        if not isinstance(function, dict):
            raise ValidationError(f"Tool '{name}': schema must have 'function' object", field="function")
        
        func_name = function.get("name")
        if not func_name or not isinstance(func_name, str) or not func_name.strip():
            raise ValidationError(f"Tool '{name}': function.name must be a non-empty string", field="function.name")
        
        if func_name != name:
            logger.warning("Tool name mismatch: registry key='%s' vs schema function.name='%s'", name, func_name)

    def execute(self, name: str, arguments: dict[str, Any]) -> str:
        """Execute a tool by name with the given arguments."""
        if name not in self._tools:
            logger.error("Unknown tool: %s", name)
            return json.dumps({"error": f"Unknown tool: {name}"}, ensure_ascii=False)

        try:
            logger.info("Executing tool: %s with args: %s", name, arguments)
            result = self._tools[name](arguments)
            logger.debug("Tool %s returned: %s", name, result[:200] if isinstance(result, str) else str(result)[:200])
            return result
        except Exception as exc:
            logger.exception("Tool execution failed: %s", name)
            return json.dumps(
                {"error": f"Tool execution failed: {exc}"}, ensure_ascii=False
            )

    def get_schemas(self) -> list[dict[str, Any]]:
        """Get all registered tool schemas for OpenAI function calling."""
        schemas = list(self._schemas.values())
        # Validate all schemas before returning
        for schema in schemas:
            self._validate_schema_for_provider(schema)
        return schemas

    def _validate_schema_for_provider(self, schema: dict[str, Any]) -> None:
        """Validate schema structure for provider request."""
        if not isinstance(schema, dict):
            raise ValidationError(f"Invalid tool schema: not a dict", field="schema")
        
        if schema.get("type") != "function":
            raise ValidationError(f"Tool schema type must be 'function'", field="type")
        
        function = schema.get("function")
        if not isinstance(function, dict):
            raise ValidationError(f"Tool schema must have 'function' object", field="function")
        
        func_name = function.get("name")
        if not func_name or not isinstance(func_name, str) or not func_name.strip():
            raise ValidationError(f"Tool function.name must be a non-empty string", field="function.name")

    def get_schema(self, name: str) -> dict[str, Any] | None:
        """Get the schema for a specific tool."""
        return self._schemas.get(name)

    def has_tool(self, name: str) -> bool:
        """Check if a tool is registered."""
        return name in self._tools

    def list_tools(self) -> list[str]:
        """List all registered tool names."""
        return list(self._tools.keys())