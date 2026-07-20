import asyncio
from typing import Optional

_main_loop: Optional[asyncio.AbstractEventLoop] = None


def set_main_loop(loop: asyncio.AbstractEventLoop) -> None:
    global _main_loop
    _main_loop = loop


def call_bot(coro):
    if _main_loop is None:
        raise RuntimeError(
            "async_bridge.set_main_loop() was never called - "
            "cannot dispatch bot call from a background thread."
        )
    future = asyncio.run_coroutine_threadsafe(coro, _main_loop)
    return future.result()
