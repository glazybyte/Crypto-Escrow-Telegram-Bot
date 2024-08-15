import os
import importlib
from functools import partial
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler, MessageHandler, Filters
import asyncio
import threading, traceback
from dotenv import load_dotenv

from transaction_checker_at_interval import execute
from globalState import GlobalState
from imports.utils import log_message




def load_commands():
    command_files = os.listdir('commands')
    command_modules = []

    for file in command_files:
        if file.endswith('.py') and not file.startswith('__'):
            module_name = f"commands.{file[:-3]}"
            module = importlib.import_module(module_name)
            command_modules.append(module)

    return command_modules

async def main():
    try:
        load_dotenv()
        bot_state = GlobalState(False, os.getenv('HOST'), int(os.getenv('PORT')), os.getenv('USER'), os.getenv('PASSWORD'), os.getenv('DATABASE'))
        updater = Updater(os.getenv('BOT_TOKEN'), use_context=True)
        thread = threading.Thread(target=execute, args=(bot_state,updater.bot))
        thread.daemon = True
        thread.start()
        dispatcher = updater.dispatcher
        command_modules = load_commands()
        for module in command_modules:
            if hasattr(module, 'execute') and hasattr(module, 'aliases'):
                for alias in module.aliases:
                    handler = partial(module.execute, bot_state=bot_state)
                    dispatcher.add_handler(CommandHandler(alias.lstrip('/'), handler))
            elif hasattr(module, 'commands'):  
                for cmd in module.commands:
                    handler = partial(cmd['function'], bot_state=bot_state)
                    for alias in cmd['aliases']:
                        dispatcher.add_handler(CommandHandler(alias.lstrip('/'), handler))
            if hasattr(module, 'button'):
                handler = partial(module.button, bot_state=bot_state)
                dispatcher.add_handler(CallbackQueryHandler(handler, pattern='^option_.*'))

            if hasattr(module, 'handle_input'):
                handler = partial(module.handle_input, bot_state=bot_state)
                dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, handler))
        updater.start_polling()
        updater.idle()
    except Exception as e:
        error_message = f"An error occurred: {str(e)}\n"
        error_message += ''.join(traceback.format_exception(None, e, e.__traceback__))
        
        # Log the detailed error message
        log_message(error_message, "error_log", True)
        # Nah dont think its working

if __name__ == '__main__':
    asyncio.run(main())
