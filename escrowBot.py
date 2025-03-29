import os, time, threading, traceback, importlib, asyncio
from functools import partial
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler, MessageHandler, Filters
from dotenv import load_dotenv, set_key
from transaction_checker_at_interval import execute
from globalState import GlobalState
from imports.utils import log_message, private_key_gen
from handlers.timer_handler import timer_handler_init
from handlers.button_handler import button_click
from handlers.input_handler import user_input

from decimal import Decimal

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
        if os.getenv('BSC_FEE_PAYER_SECRET') == 'not_set':
            from imports.bscwalletgen import generate_bsc_wallet
            print('Solana Wallet not set. Generating one...')
            wallet = generate_bsc_wallet()
            set_key('.env', 'BSC_FEE_PAYER_SECRET', wallet['private_key'])
            load_dotenv(override=True)
            print(f"BSC_FEE_PAYER_SECRET updated to: \n{os.getenv('BSC_FEE_PAYER_SECRET')}\n Menmonic: {wallet['mnemonic']}\n SecretKey: {wallet['private_key']}\n Public Key: {wallet['address']}\nSECURELY SAVE THIS SOMEWHERE ELSE")

        bot_state = GlobalState(os.getenv('ENABLEDB'), os.getenv('HOST'), int(os.getenv('PORT')), os.getenv('USER'), os.getenv('PASSWORD'), os.getenv('DATABASE'))
        updater = Updater(os.getenv('BOT_TOKEN'), use_context=True)
        thread = threading.Thread(target=execute, args=(bot_state,updater.bot))
        thread.daemon = True
        thread.start()

        ## NOTE_FOR_MYSELF: we can add address checker to interval_handler_thread too, making just one thread which runs indefinitely
        interval_handler_thread = threading.Thread(target=timer_handler_init, args=(bot_state,updater.bot))
        interval_handler_thread.daemon = True
        interval_handler_thread.start()
        bot_state.load_config("admin.config")
        # bot_state.set_var('TRADE095341922081', {'seller': '7206602140', 'buyer': '1528591668', 'broker': '6280011468', 'brokerTrade': True, 'seller_username': 'addylad6969', 'buyer_username': 'Noone1116', 'broker_username': 'addylad6725', "timestamp": 1740502165, 'tradeDetails': 'vsvs', 'currency': 'SOL (Solana)', 'tradeAmount': Decimal('103'), 'sellerAddress': 'CQ1GcrLym5NWySFjnTP8s28c8aJS7q1nHSmc1VXHA5ho', 'brokerAddress': 'HJFFFcrLym5NWySFjnTP8s28c8aJS7q1nHSmc1VXHA5yt', 'ourAddress': '', 'internalId': '', 'senderId': '6280011468', 'fee': Decimal('1'), 'fee_percentage': 0.01, 'broker_fee': Decimal('2'), 'broker_fee_percentage': Decimal('0.02'), 'step1': 'done', 'step2': 'done', 'step3': 'done', 'step4': 'done', 'step5': 'done', 'step6': '', 'step7': '', 'step8': '', 'step9': '', 'step10': '', 'sellerApproval': '', 'sellerApprovalId': '', 'buyerApproval': '', 'buyerApprovalId': '', 'status': 'open', '__last_access': 1740388893})
        # bot_state.add_item('ITEM501702843172', {'title': 'Tryhackme 2x 1month vouchers', 'description': 'Vouchers for tryhackme.com with a bumper discount of 78percent', 'type': 'automatic', 'seller': '6280011468', 'stock': 1, 'lockedStock': 0, 'stockList': ['jyfyju'], 'toggle': 'enabled', 'price': '100', 'sellerAddress': 'CQ1GcrLym5NWySFjnTP8s28c8aJS7q1nHSmc1VXHA5ho', 'currency': 'USDT (BSC Bep-20)', 'tags': 'none', 'item_id': 'ITEM501702843172', '__last_access': 1740409011})   
        
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