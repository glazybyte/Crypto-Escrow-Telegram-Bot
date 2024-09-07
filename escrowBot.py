import os
import importlib
from functools import partial
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler, MessageHandler, Filters
import asyncio
import threading, traceback
from dotenv import load_dotenv, set_key

from transaction_checker_at_interval import execute
from globalState import GlobalState
from imports.utils import log_message, private_key_gen
from handlers.timer_handler import timer_handler_init
from handlers.button_handler import button_click
from handlers.input_handler import user_input



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
        print('trying to Start Bot...\n\n')
        load_dotenv()
        
        if os.getenv('PRIVATE_KEY') == 'not_set':
            print('Private Key not set. Generating one...')
            set_key('.env', 'PRIVATE_KEY', private_key_gen())
            load_dotenv(override=True)
            print(f"PRIVATE_KEY updated to: \n{os.getenv('PRIVATE_KEY')}\nSECURELY SAVE THIS SOMEWHERE ELSE\n\n")
        if os.getenv('SOLANA_FEE_PAYER_SECRET') == 'not_set':
            from imports.solwalletgen import generate_solana_wallet
            print('Solana Wallet not set. Generating one...')
            wallet = generate_solana_wallet()
            set_key('.env', 'SOLANA_FEE_PAYER_SECRET', wallet['private_key'])
            load_dotenv(override=True)
            print(f"SOLANA_FEE_PAYER_SECRET updated to: \n{os.getenv('SOLANA_FEE_PAYER_SECRET')}\n Menmonic: {wallet['mnemonic']}\n SecretKey: {wallet['private_key']}\n Public Key: {wallet['public_address']}\nSECURELY SAVE THIS SOMEWHERE ELSE")

        bot_state = GlobalState(os.getenv('ENABLEDB'), os.getenv('HOST'), int(os.getenv('PORT')), os.getenv('USER'), os.getenv('PASSWORD'), os.getenv('DATABASE'))
        updater = Updater(os.getenv('BOT_TOKEN'), use_context=True)
        thread = threading.Thread(target=execute, args=(bot_state,updater.bot))
        thread.daemon = True
        thread.start()

        ## NOTE_FOR_MYSELF: we can add address checker to interval_handler_thread too, making just one thread which runs indefinitely
        interval_handler_thread = threading.Thread(target=timer_handler_init, args=(bot_state,updater.bot))
        interval_handler_thread.daemon = True
        interval_handler_thread.start()
        
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

        button_click_handler = partial(button_click, bot_state=bot_state)
        dispatcher.add_handler(CallbackQueryHandler(button_click_handler, pattern='^option_.*'))
        user_input_handler = partial(user_input, bot_state=bot_state)
        dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, user_input_handler))
        updater.start_polling()
        print('Bot has been initialized successfully...')
        updater.idle()
        
    except Exception as e:
        error_message = f"An error occurred: {str(e)}\n"
        error_message += ''.join(traceback.format_exception(None, e, e.__traceback__))
        
        # Log the detailed error message
        log_message(error_message, "error_log", True)

if __name__ == '__main__':
    asyncio.run(main())





#Very well aware of the three memory leaks but decided not to fix for now as very early in development stage
#1 The tradedetails
#2 Waiting for user to respond indefinitely
#3 The wallets are in storage even after use