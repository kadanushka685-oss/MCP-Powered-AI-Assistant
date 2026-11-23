"""A tiny tool registry: one place that knows every tool.

Each tool is a normal Python function decorated with ``@registry.tool(...)``.
The registry stores its name, description, JSON input schema and search
keywords. Two things then use the same registry:

1. the MCP server (``server.py``) registers every tool with FastMCP, and
2. the assistant can run the tools directly ("direct mode") without
   starting a separate process.

This is what makes dynamic tool discovery possible: the assistant never
has a hard-coded list of tools, it asks the registry (or the MCP server).
"""
import inspect
import typing
from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Optional

from utils.validators import ToolError

_TYPE_NAMES = {str: "string", int: "integer", float: "number", bool: "boolean"}


@dataclass
class ToolSpec:
    name: str
    description: str
    func: Callable
    category: str
    keywords: List[str]
    input_schema: dict


def _json_type(annotation) -> str:
    if typing.get_origin(annotation) is typing.Union:
        inner = [a for a in typing.get_args(annotation) if a is not type(None)]
        return _json_type(inner[0]) if inner else "string"
    return _TYPE_NAMES.get(annotation, "string")


def _build_schema(func: Callable, param_docs: Dict[str, str]) -> dict:
    hints = typing.get_type_hints(func)
    properties, required = {}, []
    for name, param in inspect.signature(func).parameters.items():
        prop = {"type": _json_type(hints.get(name, str))}
        if name in param_docs:
            prop["description"] = param_docs[name]
        if param.default is inspect.Parameter.empty:
            required.append(name)
        elif param.default is not None:
            prop["default"] = param.default
        properties[name] = prop
    schema = {"type": "object", "properties": properties}
    if required:
        schema["required"] = required
    return schema


def _coerce(name: str, value: Any, json_type: str) -> Any:
    if json_type == "integer":
        if isinstance(value, bool):
            raise ToolError(f"'{name}' must be a whole number.")
        try:
            return int(value)
        except (TypeError, ValueError):
            raise ToolError(f"'{name}' must be a whole number, got {value!r}.")
    if json_type == "number":
        if isinstance(value, bool):
            raise ToolError(f"'{name}' must be a number.")
        try:
            return float(value)
        except (TypeError, ValueError):
            raise ToolError(f"'{name}' must be a number, got {value!r}.")
    if json_type == "boolean":
        if isinstance(value, bool):
            return value
        if str(value).lower() in ("true", "1", "yes"):
            return True
        if str(value).lower() in ("false", "0", "no"):
            return False
        raise ToolError(f"'{name}' must be true or false.")
    if isinstance(value, (dict, list)):
        raise ToolError(f"'{name}' must be a text value.")
    return str(value)


class ToolRegistry:
    def __init__(self) -> None:
        self._tools: Dict[str, ToolSpec] = {}

    def tool(self, category: str = "general", keywords: Optional[List[str]] = None,
             params: Optional[Dict[str, str]] = None):
        """Decorator that registers a function as a tool."""
        def decorator(func: Callable) -> Callable:
            doc = inspect.cleandoc(func.__doc__ or "").split("\n\n")[0].replace("\n", " ")
            if func.__name__ in self._tools:
                raise ValueError(f"Duplicate tool name: {func.__name__}")
            self._tools[func.__name__] = ToolSpec(
                name=func.__name__,
                description=doc,
                func=func,
                category=category,
                keywords=[k.lower() for k in (keywords or [])],
                input_schema=_build_schema(func, params or {}),
            )
            return func
        return decorator

    def list_specs(self) -> List[ToolSpec]:
        return list(self._tools.values())

    def get(self, name: str) -> ToolSpec:
        if name not in self._tools:
            raise ToolError(f"Unknown tool: {name!r}. It is not in the approved tool list.")
        return self._tools[name]

    def describe(self) -> List[dict]:
        """Machine-readable list of tools (this is what 'discovery' returns)."""
        return [
            {"name": s.name, "description": s.description, "category": s.category,
             "keywords": s.keywords, "input_schema": s.input_schema}
            for s in self._tools.values()
        ]

    def clean_arguments(self, spec: ToolSpec, arguments: Optional[dict]) -> dict:
        """Check argument names/types against the schema (safe tool execution)."""
        if arguments is None:
            arguments = {}
        if not isinstance(arguments, dict):
            raise ToolError("Tool arguments must be an object (key/value pairs).")
        props = spec.input_schema["properties"]
        unknown = sorted(set(arguments) - set(props))
        if unknown:
            raise ToolError(f"Unknown argument(s) for {spec.name}: {', '.join(unknown)}.")
        missing = [r for r in spec.input_schema.get("required", []) if arguments.get(r) in (None, "")]
        if missing:
            raise ToolError(f"Missing required argument(s) for {spec.name}: {', '.join(missing)}.")
        return {k: _coerce(k, v, props[k]["type"]) for k, v in arguments.items() if v is not None}

    def call(self, name: str, arguments: Optional[dict] = None) -> dict:
        spec = self.get(name)
        return spec.func(**self.clean_arguments(spec, arguments))


registry = ToolRegistry()
