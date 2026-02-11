from __future__ import annotations

from collections.abc import Callable
from typing import Any


class AgentDispatcherError(ValueError):
    pass


class AgentDispatcher:
    def __init__(self) -> None:
        self._handlers: dict[str, Callable[[dict[str, Any]], dict[str, Any]]] = {}

    def register(self, agent_id: str, handler: Callable[[dict[str, Any]], dict[str, Any]]) -> None:
        if agent_id in self._handlers:
            raise AgentDispatcherError(f"agent already registered: {agent_id}")
        self._handlers[agent_id] = handler

    def dispatch(self, agent_ids: list[str], context: dict[str, Any]) -> list[dict[str, Any]]:
        results: list[dict[str, Any]] = []
        for agent_id in agent_ids:
            handler = self._handlers.get(agent_id)
            if handler is None:
                raise AgentDispatcherError(f"agent not registered: {agent_id}")
            result = handler(context)
            normalized = dict(result)
            normalized["agent_id"] = agent_id
            results.append(normalized)
        return results
