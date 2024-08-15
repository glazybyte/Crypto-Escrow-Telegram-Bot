import time
import requests, traceback
from concurrent.futures import ThreadPoolExecutor
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, CallbackContext, CallbackQueryHandler, MessageHandler, Filters
from imports.ltc_transaction_checker import ltcTransactionChecker
from imports.solwalletbalance import get_finalized_sol_balance, USDT_MINT_ADDRESS
from imports.doge_transaction_checker import dogeTransactionChecker
from decimal import Decimal

from imports.utils import log_message


def execute(bot_state, bot):
    log_file = 'Transaction_checker_at_Interval'
    while True:
        with ThreadPoolExecutor() as executor:
            futures = []
            try:
                for key, value in bot_state.get_all_queue_addresses().items():
                    if value['currency'] == "LTC":
                        print(f"[Wallet Checker]:: Initiating LTC wallet check for {key}")
                        future = executor.submit(ltcTransactionChecker, key)
                        futures.append(future)
                    elif value['currency'] == "DOGE":
                        print(f"[Wallet Checker]:: Initiating DOGE wallet check for {key}")
                        future = executor.submit(dogeTransactionChecker, key)
                        futures.append(future)
                    elif value['currency'] == "SOL (Solana)":
                        print(f"[Wallet Checker]:: Initiating SOL (Solana) wallet check for {key}")
                        future = executor.submit(get_finalized_sol_balance, key)
                        futures.append(future)
                    elif value['currency'] == "USDT (Solana)":
                        print(f"[Wallet Checker]:: Initiating USDT (Solana) wallet check for {key}")
                        future = executor.submit(get_finalized_sol_balance, key, USDT_MINT_ADDRESS)
                        futures.append(future)
                    elif value['currency'] == "BNB (BSC Bep-20)":
                        print(f"[Wallet Checker]:: Initiating BNB (BSC Bep-20) wallet check for {key}")
                        #future = executor.submit(get_finalized_sol_balance, key, USDT_MINT_ADDRESS)
                        #futures.append(future)
                    
                for future in futures:
                    response = future.result()
                    handleResponse(response, bot_state, bot)
            except Exception as e:
                error_message = f"An error occurred: {str(e)}\n"
                error_message += ''.join(traceback.format_exception(None, e, e.__traceback__))
                
                # Log the detailed error message
                log_message(error_message, log_file, True)

        time.sleep(100)

def handleResponse(response, bot_state, bot):
    wallet = bot_state.get_address_info(response['publicKey'])
    log_file = response['publicKey']
    tradeDetails = bot_state.get_var(wallet['tradeId'])
    if tradeDetails['currency'] == 'LTC':
        if isinstance(response, dict) and response.get("code") == "confirmed":
            bot_state.remove_address_from_queue(response['publicKey'])
            log_message(f"[LTC wallet Checker]:: {response['publicKey']} Transaction for {response['amount']} detected", log_file)
            
            if(float(response['amount'])>=float(tradeDetails["tradeAmount"])):
                proceed_transaction(bot_state, wallet['tradeId'], response, tradeDetails, bot)
            else:
                bot.send_message(chat_id=tradeDetails["buyer"], text="Your Transaction seems to have less than the quoted amount in trade, contact @addylad6725 for resolution")
                from commands.escrow import close_trade
                close_trade(bot_state=bot_state, tradeId=wallet['tradeId'], message="close[insuff_funds_receieved]")
                log_message(f"[LTC wallet Checker]:: {response['publicKey']} Insufficient Transaction for {response['amount']} detected, trade is closed", log_file)

        # print(f"Confirmed transaction: {response['amount']} LTC")
        elif isinstance(response, dict) and response.get("code") == "unconfirmed":
            log_message(f"[LTC wallet Checker]:: {response['publicKey']} Transaction is detected but unconfirmed", log_file)
        elif isinstance(response, dict) and response.get("code") == "undetected":
            print(f"[LTC wallet Checker]:: {response['publicKey']} no transactions")
        else:
            # Handle errors
            log_message(f"Error: {response}", log_file)
    if tradeDetails['currency'] == 'DOGE':
        if isinstance(response, dict) and response.get("code") == "confirmed":
            bot_state.remove_address_from_queue(response['publicKey'])
            log_message(f"[DOGE wallet Checker]:: {response['publicKey']} Transaction for {response['amount']} detected", log_file)
            
            if(float(response['amount'])>=float(tradeDetails["tradeAmount"])):
                proceed_transaction(bot_state, wallet['tradeId'], response, tradeDetails, bot)
            else:
                bot.send_message(chat_id=tradeDetails["buyer"], text="Your Transaction seems to have less than the quoted amount in trade, contact @addylad6725 for resolution")
                from commands.escrow import close_trade
                close_trade(bot_state=bot_state, tradeId=wallet['tradeId'], message="close[insuff_funds_receieved]")
                log_message(f"[DOGE wallet Checker]:: {response['publicKey']} Insufficient Transaction for {response['amount']} detected, trade is closed", log_file)

        # print(f"Confirmed transaction: {response['amount']} LTC")
        elif isinstance(response, dict) and response.get("code") == "unconfirmed":
            log_message(f"[DOGE wallet Checker]:: {response['publicKey']} Transaction is detected but unconfirmed", log_file)
        elif isinstance(response, dict) and response.get("code") == "undetected":
            print(f"[DOGE wallet Checker]:: {response['publicKey']} no transactions")
        else:
            # Handle errors
            log_message(f"Error: {response}", log_file)
    elif tradeDetails['currency'] == "SOL (Solana)" or tradeDetails['currency'] == "USDT (Solana)":
        if(response["amount"]>= Decimal(tradeDetails["tradeAmount"])):
            print(f"[SOL Wallet Checker]:: Transaction detected for wallet {tradeDetails['ourAddress']} of {response['amount']} {tradeDetails['currency']}")
            bot_state.remove_address_from_queue(response['publicKey'])
            proceed_transaction(bot_state, wallet['tradeId'], response["amount"], tradeDetails, bot)
        elif response["amount"] == 0:
            print(f"[SOL wallet Checker]:: {tradeDetails['ourAddress']} no transactions")
        else:
            bot_state.remove_address_from_queue(response['publicKey'])
            bot.send_message(chat_id=tradeDetails["buyer"], text="Your Transaction seems to have less than the quoted amount in trade, contact @addylad6725 for resolution")
            bot.send_message(chat_id=tradeDetails["seller"], text="The buyer has sent less than the agreed amount, so we have cancled the trade")
            from commands.escrow import close_trade
            close_trade(bot_state=bot_state, tradeId=wallet['tradeId'], message="close[insuff_funds_receieved]")
    elif tradeDetails['currency'] == "BNB (BSC Bep-20)" or tradeDetails['currency'] == "USDT (BSC Bep-20)":
        if(response["amount"]>= Decimal(tradeDetails["tradeAmount"])):
            print(f"[BSC Wallet Checker]:: Transaction detected for wallet {tradeDetails['ourAddress']} of {response['amount']} {tradeDetails['currency']}")
            bot_state.remove_address_from_queue(response['publicKey'])
            proceed_transaction(bot_state, wallet['tradeId'], response["amount"], tradeDetails, bot)
        elif response["amount"] == 0:
            print(f"[BSC wallet Checker]:: {tradeDetails['ourAddress']} no transactions")
        else:
            bot_state.remove_address_from_queue(response['publicKey'])
            bot.send_message(chat_id=tradeDetails["buyer"], text="Your Transaction seems to have less than the quoted amount in trade, contact @addylad6725 for resolution")
            bot.send_message(chat_id=tradeDetails["seller"], text="The buyer has sent less than the agreed amount, so we have cancled the trade")
            from commands.escrow import close_trade
            close_trade(bot_state=bot_state, tradeId=wallet['tradeId'], message="close[insuff_funds_receieved]")

def proceed_transaction(bot_state, tradeId, response, tradeDetails, bot):
    
    bot.send_message(chat_id=tradeDetails["buyer"], text="Your Transaction is now confirmed in Blockchain, seller is now notified to send your product")
    keyboard = [
        [InlineKeyboardButton("I have Sent", callback_data='option_9')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    bot.send_message(
        chat_id=tradeDetails["seller"], 
        text="Buyer has sent the payment to our escrow wallet, You can now safely deliever your product \n\n It's recomended that you keep delievery and working proof to yourself until you receive the payment. \n\n CLick button below after you have delivered it",
        reply_markup=reply_markup
        )
        