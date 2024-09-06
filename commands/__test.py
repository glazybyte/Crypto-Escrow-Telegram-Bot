from telegram import Update
from telegram.ext import CallbackContext
from datetime import datetime
from decimal import Decimal
from globalState import GlobalState, interval_up
def execute(update: Update, context: CallbackContext, bot_state:GlobalState) -> None:
    interval_up('hourly_cleanup', context.bot, bot_state)
    #timeout_up(context, 'bot', bot_state)

# def timeout_up(context, bot, bot_state):
#     import psutil, os
#     # Get system memory info
#     memory_info = psutil.virtual_memory()
#     total_memory = memory_info.total / (1024 ** 2)  # Convert to MB
#     available_memory = memory_info.available / (1024 ** 2)  # Convert to MB
#     used_memory = memory_info.used / (1024 ** 2)  # Convert to MB

#     print(f"Total Memory: {total_memory:.2f} MB")
#     print(f"Available Memory: {available_memory:.2f} MB")
#     print(f"Used Memory: {used_memory:.2f} MB")




#     # Get current process memory usage
#     process = psutil.Process(os.getpid())
#     memory_usage = process.memory_info().rss / (1024 ** 2)  # Convert to MB

#     print(f"Current Program Memory Usage: {memory_usage:.2f} MB")
description = "Check ping for bot"
aliases = ['/t']
enabled = False
hidden = True
OperaterCommand = False
