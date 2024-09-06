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
        load_dotenv()
        ##NOTE FOR MYSELF: we can add address checker to interval_handler_thread too, making just one thread which runs indefinitely

        bot_state = GlobalState(os.getenv('ENABLEDB'), os.getenv('HOST'), int(os.getenv('PORT')), os.getenv('USER'), os.getenv('PASSWORD'), os.getenv('DATABASE'))
        updater = Updater(os.getenv('BOT_TOKEN'), use_context=True)
        thread = threading.Thread(target=execute, args=(bot_state,updater.bot))
        thread.daemon = True
        thread.start()
        
        interval_handler_thread = threading.Thread(target=timer_handler_init, args=(bot_state,updater.bot))
        interval_handler_thread.daemon = True
        interval_handler_thread.start()
        
        #testing
        # import time
        # for i in range(20_000):
        #     bot_state.state['items'][f'{i}'] = {'title': 'Xjs', 'description': 'jfhsrkgjlhkhgisrrsfkjghwrgfieugfyiagfilyagfuyasglfiyadgvlfyuigdiyufvgayivf', 'type': 'automatic', 'seller': '6280011468', 'stock': 1, 'lockedStock': 0, 'stockList': ['ndcv'], 'toggle': 'enabled', 'price': '20', 'sellerAddress': '9o9cdHpRLBykY3kMUZbAjVXarZRoe2Bjwioc6aKVrakF', 'currency': 'USDT (Solana)', '__last_access': time.time()}
        # for i in range(10_000):
        #     bot_state.state['items'][f'{i+10_000}'] = {'title': 'Xjs', 'description': 'jfhsrkgjlhkhgisrrsfkjghwrgfieugfyiagfilyagfuyasglfiyadgvlfyuigdiyufvgayivf', 'type': 'automatic', 'seller': '6280011468', 'stock': 1, 'lockedStock': 0, 'stockList': ['ndcv'], 'toggle': 'enabled', 'price': '20', 'sellerAddress': '9o9cdHpRLBykY3kMUZbAjVXarZRoe2Bjwioc6aKVrakF', 'currency': 'USDT (Solana)', '__last_access': int(time.time())- (60*60)}
        # for i in range(10_000):
        #     bot_state.state['txs'][f'{i}'] = {"status":"close[payment_timeout]","currency":"USDT (Solana)","openUpto":1725453934,"itemAmount":1,"message_id":2859,"ourAddress":"3Au4HSJLwUkHjijcCQYoitNs2iQ6D3ZK4ksePyqcUY58","lastRefresh":1725453891,"tradeAmount":"20","buyer_username":"addylad6725","payment_timeout":"TI122518085819","seller_username":"addylad6725", '__last_access': time.time()}
        # for i in range(10_000):
        #     bot_state.state['txs'][f'{i+10_000}'] = {"status":"close[payment_timeout]","currency":"USDT (Solana)","openUpto":1725453934,"itemAmount":1,"message_id":2859,"ourAddress":"3Au4HSJLwUkHjijcCQYoitNs2iQ6D3ZK4ksePyqcUY58","lastRefresh":1725453891,"tradeAmount":"20","buyer_username":"addylad6725","payment_timeout":"TI122518085819","seller_username":"addylad6725", '__last_access': time.time()- (60*60)}
        # for i in range(30_000):
        #     bot_state.state['wallets'][f'{i}'] = {"tradeId": "TXID589455959703", "memonic": "sunny guide museum gentle oyster increase main chapter balance rapid meat typical", "secretKey": "da2631b1bef8a88cff0b43a6d30666471a6abb4e96f04f04d183a155067a904b", "publicKey": "2amQyqkkagxjnKbzHJW5QsdfzdfvVBaMoKakdU27Dv1w", "currency": "SOL", "tradeType": "buy", '__time_added': time.time()- (60*60)}
        # for i in range(10_000):
        #     bot_state.state['wallets'][f'{i+30_000}'] = {"tradeId": "TXID589455959703", "memonic": "sunny guide museum gentle oyster increase main chapter balance rapid meat typical", "secretKey": "da2631b1bef8a88cff0b43a6d30666471a6abb4e96f04f04d183a155067a904b", "publicKey": "2amQyqkkagxjnKbzHJW5QsdfzdfvVBaMoKakdU27Dv1w", "currency": "SOL", "tradeType": "buy", '__time_added': time.time()- (60*60)}
        # for i in range(10_000):
        #     bot_state.state['user_data'][f'{i}'] = {'title': 'Xjs', 'description': 'jfhsrkgjlhkhgisrrsfkjghwrgfieugfyiagfilyagfuyasglfiyadgvlfyuigdiyufvgayivf', 'type': 'automatic', 'seller': '6280011468', 'stock': 1, 'lockedStock': 0, 'stockList': ['ndcv'], 'toggle': 'enabled', 'price': '20', 'sellerAddress': '9o9cdHpRLBykY3kMUZbAjVXarZRoe2Bjwioc6aKVrakF', 'currency': 'USDT (Solana)', '__last_access': time.time()}
        # for i in range(10_000):
        #     bot_state.state['user_data'][f'{i+10_000}'] = {'title': 'Xjs', 'description': 'jfhsrkgjlhkhgisrrsfkjghwrgfieugfyiagfilyagfuyasglfiyadgvlfyuigdiyufvgayivf', 'type': 'automatic', 'seller': '6280011468', 'stock': 1, 'lockedStock': 0, 'stockList': ['ndcv'], 'toggle': 'enabled', 'price': '20', 'sellerAddress': '9o9cdHpRLBykY3kMUZbAjVXarZRoe2Bjwioc6aKVrakF', 'currency': 'USDT (Solana)', '__last_access': int(time.time())- (60*60)}
        # for i in range(10_000):
        #     bot_state.state['escrow'][f'{i}'] = {"seller": "628001d1468", "buyer": "1528591d668", "trade": "", "currency": "USDT (Solana)", "tradeAmount": "", "sellerAddress": "", "ourAddress": "", "internalId": "", "senderId": "6280011468", "sellerApprovalId": "", "buyerApprovalId": "", "step1": "done", "step2": "done", "step3": "done", "step4": "done", "step5": "", "step6": "", "step7": "", "step8": "", "step9": "", "step10": "", "sellerApproval": "", "buyerApproval": "", "status": "open", "tradeDetails": "Flcbw", '__last_access': time.time()}
        # for i in range(10_000):
        #     bot_state.state['escrow'][f'{i+10_000}'] = {"seller": "62800114d68", "buyer": "152859d1668", "trade": "", "currency": "USDT (Solana)", "tradeAmount": "", "sellerAddress": "", "ourAddress": "", "internalId": "", "senderId": "6280011468", "sellerApprovalId": "", "buyerApprovalId": "", "step1": "done", "step2": "done", "step3": "done", "step4": "done", "step5": "", "step6": "", "step7": "", "step8": "", "step9": "", "step10": "", "sellerApproval": "", "buyerApproval": "", "status": "open", "tradeDetails": "Flcbw", '__last_access': time.time()- (60*60)}
        
        # print('inserted')
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
        updater.idle()
    except Exception as e:
        error_message = f"An error occurred: {str(e)}\n"
        error_message += ''.join(traceback.format_exception(None, e, e.__traceback__))
        
        # Log the detailed error message
        log_message(error_message, "error_log", True)
        # Nah dont think its working

if __name__ == '__main__':
    asyncio.run(main())





#Very well aware of the three memory leaks but decided not to fix for now as very early in development stage
#1 The tradedetails
#2 Waiting for user to respond indefinitely
#3 The wallets are in storage even after use