"""Shared MCP wrapper for AMap tools via HelloAgents MCPTool."""

from __future__ import annotations

import json
import logging
import sys
import threading
from typing import Any, Dict, List, Optional

from app.config import get_settings

logger = logging.getLogger(__name__)

try:
    from hello_agents.tools.builtin.protocol_tools import MCPTool
except Exception:  # pragma: no cover - optional dependency at runtime
    MCPTool = None  # type: ignore[assignment]


class MCPToolService:
    """Singleton-style access to a shared HelloAgents MCPTool instance."""

    _tool: Optional[Any] = None
    _tool_lock = threading.Lock()
    _tool_failed = False
    _known_tools: Optional[set[str]] = None

    def __init__(self) -> None:
        settings = get_settings()
        self.api_key = (settings.amap_api_key or "").strip()
        self.enabled = bool(settings.use_amap_mcp and self.api_key and MCPTool)

    def search_poi(self, keywords: str, city: str) -> List[Dict[str, Any]]:
        payload = {"keywords": keywords, "city": city}
        result = self.call_tool(["maps_text_search"], payload)
        return self._parse_poi_result(result)

    def get_weather(self, city: str) -> Optional[Dict[str, Any]]:
        result = self.call_tool(["maps_weather"], {"city": city})
        return self._parse_weather_result(result)

    def call_tool(self, tool_names: List[str], arguments: Dict[str, Any]) -> Any:
        tool = self._ensure_tool()
        if not tool:
            return None

        if MCPToolService._known_tools is None:
            MCPToolService._known_tools = self._list_tools(tool)

        available = MCPToolService._known_tools or set()
        for tool_name in tool_names:
            if available and tool_name not in available:
                continue
            try:
                raw = tool.run(
                    {
                        "action": "call_tool",
                        "tool_name": tool_name,
                        "arguments": arguments,
                    }
                )
                result = self._unwrap_result(raw)
                if result not in (None, "", [], {}):
                    return result
            except Exception as exc:
                logger.info("AMap MCP tool call failed for %s: %s", tool_name, exc)
        return None

    def _ensure_tool(self) -> Optional[Any]:
        if not self.enabled or MCPToolService._tool_failed:
            return None
        if MCPToolService._tool is not None:
            return MCPToolService._tool

        with MCPToolService._tool_lock:
            if MCPToolService._tool is not None:
                return MCPToolService._tool
            if MCPToolService._tool_failed:
                return None

            try:
                for stream_name in ("stdout", "stderr"):
                    stream = getattr(sys, stream_name, None)
                    if stream and hasattr(stream, "reconfigure"):
                        try:
                            stream.reconfigure(encoding="utf-8")
                        except Exception:
                            pass
                MCPToolService._tool = MCPTool(
                    name="amap",
                    description="AMap MCP service",
                    server_command=["uvx", "amap-mcp-server"],
                    env={
                        "AMAP_MAPS_API_KEY": self.api_key,
                        "PYTHONIOENCODING": "utf-8",
                        "PYTHONUTF8": "1",
                        "UV_NO_PROGRESS": "1",
                    },
                    auto_expand=True,
                )
                return MCPToolService._tool
            except Exception as exc:
                MCPToolService._tool_failed = True
                logger.warning("Failed to initialize HelloAgents MCPTool, fallback to REST: %s", exc)
                return None

    def _list_tools(self, tool: Any) -> set[str]:
        try:
            output = tool.run({"action": "list_tools"})
            names: set[str] = set()
            for line in str(output).splitlines():
                line = line.strip()
                if line.startswith("- "):
                    name = line[2:].split(":", 1)[0].strip()
                    if name:
                        names.add(name)
            return names
        except Exception as exc:
            logger.info("AMap MCP list_tools failed: %s", exc)
            return set()

    def _unwrap_result(self, result: Any) -> Any:
        text = str(result or "").strip()
        if not text:
            return None

        for marker in ("执行结果:", "鎵ц缁撴灉:"):
            if marker in text:
                text = text.split(marker, 1)[1].strip()
                break

        return self._try_json(text)

    @staticmethod
    def _try_json(text: str) -> Any:
        text = (text or "").strip()
        if not text:
            return None
        try:
            return json.loads(text)
        except Exception:
            pass

        for start_char, end_char in (("{", "}"), ("[", "]")):
            start = text.find(start_char)
            end = text.rfind(end_char)
            if start != -1 and end != -1 and end > start:
                snippet = text[start : end + 1]
                try:
                    return json.loads(snippet)
                except Exception:
                    continue
        return text

    def _parse_poi_result(self, result: Any) -> List[Dict[str, Any]]:
        if result is None:
            return []
        if isinstance(result, dict):
            for key in ("pois", "data", "result", "items"):
                value = result.get(key)
                if isinstance(value, list):
                    return [item for item in value if isinstance(item, dict)]
            return [result]
        if isinstance(result, list):
            return [item for item in result if isinstance(item, dict)]
        return []

    def _parse_weather_result(self, result: Any) -> Optional[Dict[str, Any]]:
        if result is None:
            return None
        if isinstance(result, dict):
            if "forecasts" in result:
                forecasts = result.get("forecasts") or []
                if forecasts:
                    first = forecasts[0]
                    return {
                        "city": first.get("city") or result.get("city"),
                        "province": first.get("province") or result.get("province"),
                        "casts": first.get("casts") or result.get("casts") or [],
                    }
            if "casts" in result:
                return {
                    "city": result.get("city"),
                    "province": result.get("province"),
                    "casts": result.get("casts") or [],
                }
        return None
