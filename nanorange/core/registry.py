"""
Tool Registry - Central registration and discovery of tools.

The registry maintains a catalog of all available tools with their schemas,
enabling the orchestrator agent to discover and use them dynamically.
"""

import importlib
import pkgutil
from pathlib import Path
from typing import Callable, Dict, List, Optional, Type
from nanorange.core.schemas import ToolSchema, ToolType


class ToolRegistry:
    """
    Central registry for all available tools.
    
    Tools can be registered manually or discovered automatically
    from the tools package.
    """
    
    _instance: Optional["ToolRegistry"] = None
    
    def __new__(cls) -> "ToolRegistry":
        """Singleton pattern to ensure one global registry."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        self._tools: Dict[str, ToolSchema] = {}
        self._implementations: Dict[str, Callable] = {}
        self._tool_classes: Dict[str, Type] = {}
        self._initialized = True
    
    def register(
        self,
        schema: ToolSchema,
        implementation: Optional[Callable] = None,
        tool_class: Optional[Type] = None,
        replace: bool = False
    ) -> None:
        """
        Register a tool with its schema and implementation.
        
        Args:
            schema: The tool schema defining inputs/outputs
            implementation: Callable that executes the tool (for function tools)
            tool_class: Class that implements the tool (for class-based tools)
            replace: If True, replace existing tool; if False, skip if exists
        """
        if schema.tool_id in self._tools:
            if not replace:
                # Already registered, skip silently
                return
        
        self._tools[schema.tool_id] = schema
        
        if implementation is not None:
            self._implementations[schema.tool_id] = implementation
        
        if tool_class is not None:
            self._tool_classes[schema.tool_id] = tool_class
    
    def unregister(self, tool_id: str) -> bool:
        """Remove a tool from the registry."""
        if tool_id not in self._tools:
            return False
        
        del self._tools[tool_id]
        self._implementations.pop(tool_id, None)
        self._tool_classes.pop(tool_id, None)
        return True
    
    def get_schema(self, tool_id: str) -> Optional[ToolSchema]:
        """Get the schema for a registered tool."""
        return self._tools.get(tool_id)
    
    def get_implementation(self, tool_id: str) -> Optional[Callable]:
        """Get the implementation callable for a tool."""
        return self._implementations.get(tool_id)
    
    def get_tool_class(self, tool_id: str) -> Optional[Type]:
        """Get the tool class for a class-based tool."""
        return self._tool_classes.get(tool_id)
    
    def list_tools(self, category: Optional[str] = None) -> List[ToolSchema]:
        """
        List all registered tools, optionally filtered by category.
        
        Args:
            category: Filter by this category (None for all)
            
        Returns:
            List of tool schemas
        """
        tools = list(self._tools.values())
        if category:
            tools = [t for t in tools if t.category == category]
        return sorted(tools, key=lambda t: t.tool_id)
    
    def list_categories(self) -> List[str]:
        """Get all unique categories."""
        categories = set(t.category for t in self._tools.values())
        return sorted(categories)
    
    def search_tools(
        self,
        query: str,
        category: Optional[str] = None
    ) -> List[ToolSchema]:
        """
        Search tools by name, description, or tags.
        
        Args:
            query: Search query (case-insensitive)
            category: Optional category filter
            
        Returns:
            Matching tool schemas
        """
        query_lower = query.lower()
        results = []
        
        for tool in self._tools.values():
            if category and tool.category != category:
                continue
            
            # Search in name, description, and tags
            if (query_lower in tool.name.lower() or
                query_lower in tool.description.lower() or
                any(query_lower in tag.lower() for tag in tool.tags)):
                results.append(tool)
        
        return sorted(results, key=lambda t: t.tool_id)
    
    def get_tools_by_type(self, tool_type: ToolType) -> List[ToolSchema]:
        """Get all tools of a specific type."""
        return [t for t in self._tools.values() if t.type == tool_type]
    
    def has_tool(self, tool_id: str) -> bool:
        """Check if a tool is registered."""
        return tool_id in self._tools
    
    def clear(self) -> None:
        """Clear all registered tools (useful for testing)."""
        self._tools.clear()
        self._implementations.clear()
        self._tool_classes.clear()
    
    def discover_tools(self, package_name: str = "nanorange.tools.builtin") -> int:
        """
        Auto-discover and register tools from a package.
        
        Tools are discovered by looking for modules with a `register_tools`
        function or classes that inherit from ToolBase.
        
        Args:
            package_name: Package to scan for tools
            
        Returns:
            Number of tools discovered
        """
        count_before = len(self._tools)
        
        try:
            package = importlib.import_module(package_name)
        except ImportError:
            return 0
        
        package_path = Path(package.__file__).parent
        
        for _, module_name, _ in pkgutil.iter_modules([str(package_path)]):
            full_module_name = f"{package_name}.{module_name}"
            try:
                module = importlib.import_module(full_module_name)
                
                # Look for register_tools function
                if hasattr(module, "register_tools"):
                    module.register_tools(self)
                
            except ImportError as e:
                print(f"Warning: Could not import {full_module_name}: {e}")
        
        return len(self._tools) - count_before
    
    def to_description(self) -> str:
        """Generate a full description of all tools for the LLM."""
        lines = ["# Available Tools\n"]
        
        for category in self.list_categories():
            lines.append(f"\n## {category.title()}\n")
            for tool in self.list_tools(category=category):
                lines.append(tool.to_description())
                lines.append("")
        
        return "\n".join(lines)
    
    def to_summary(self) -> str:
        """Generate a brief summary of tools."""
        lines = ["Available tools:"]
        for tool in self.list_tools():
            lines.append(f"  - {tool.tool_id}: {tool.description[:60]}...")
        return "\n".join(lines)


# Global registry instance
_global_registry: Optional[ToolRegistry] = None


def get_registry() -> ToolRegistry:
    """Get the global tool registry instance."""
    global _global_registry
    if _global_registry is None:
        _global_registry = ToolRegistry()
    return _global_registry
