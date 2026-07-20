import asyncio
import inspect
from functools import wraps
from typing import Callable, Any

# Re-export common telegram classes for convenient imports
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ParseMode
from telegram.error import TelegramError
from telegram.ext import ContextTypes

__all__ = [
    'sync_handler_wrapper',
    'Update',
    'ParseMode',
    'InlineKeyboardButton',
    'InlineKeyboardMarkup',
    'TelegramError',
    'ContextTypes',
]


def sync_handler_wrapper(func: Callable) -> Callable:
    
    # Check if function is already async
    if inspect.iscoroutinefunction(func):
        return func  # Already async, return as-is
    
    @wraps(func)
    async def async_wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE) -> Any:
        loop = asyncio.get_event_loop()
        
        # Run the sync function in a thread pool executor to prevent blocking
        return await loop.run_in_executor(None, func, update, context)
    
    return async_wrapper
