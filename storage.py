from __future__ import annotations

import asyncio
import copy
import json
from pathlib import Path
from typing import Any, Callable, TypeVar

T = TypeVar("T")


class JsonStore:
    def __init__(self, path: Path) -> None:
        self.path = path
        self._lock = asyncio.Lock()
        self._loaded = False
        self._data: dict[str, Any] = {"guilds": {}}

    async def load(self) -> None:
        async with self._lock:
            await self._load_locked()

    async def read(self) -> dict[str, Any]:
        async with self._lock:
            await self._load_locked()
            return copy.deepcopy(self._data)

    async def mutate(self, callback: Callable[[dict[str, Any]], T]) -> T:
        async with self._lock:
            await self._load_locked()
            result = callback(self._data)
            self._save_locked()
            return result

    async def _load_locked(self) -> None:
        if self._loaded:
            return

        if self.path.is_file():
            try:
                raw_data = json.loads(self.path.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                raw_data = {"guilds": {}}
        else:
            raw_data = {"guilds": {}}

        if not isinstance(raw_data, dict):
            raw_data = {"guilds": {}}

        raw_data.setdefault("guilds", {})
        self._data = raw_data
        self._loaded = True

    def _save_locked(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(
            json.dumps(self._data, indent=2, sort_keys=True),
            encoding="utf-8",
        )
