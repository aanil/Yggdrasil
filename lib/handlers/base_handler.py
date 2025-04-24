import asyncio
from abc import ABC, abstractmethod
from typing import Any, Dict


class BaseHandler(ABC):
    """
    All handlers must implement:
      - __call__: for async dispatch (under the running event loop)
      - handle_async: the actual async work
      - run_now: a sync wrapper for one-off CLI use
    """

    @abstractmethod
    async def handle_task(self, payload: Dict[str, Any]) -> None:
        """
        Coroutine that does the real work.
        Subclasses implement this (e.g. resolving realm, running it).
        """
        ...

    @abstractmethod
    def __call__(self, payload: Dict[str, Any]) -> None:
        """
        Schedule handle_async under asyncio.create_task().
        """
        ...

    def run_now(self, payload: Dict[str, Any]) -> None:
        """
        Blocking, one-off entrypoint for CLI mode.
        Simply runs handle_async() to completion.
        """
        asyncio.run(self.handle_task(payload))
