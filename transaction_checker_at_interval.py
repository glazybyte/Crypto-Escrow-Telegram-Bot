import time, traceback
from concurrent.futures import ThreadPoolExecutor
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ParseMode
from telegram.ext import Updater, CommandHandler, CallbackContext, CallbackQueryHandler, MessageHandler, Filters
from telegram.error import TelegramError
from imports.ltc_transaction_checker import ltcTransactionChecker
from imports.solwalletbalance import get_finalized_sol_balance, USDT_MINT_ADDRESS
from imports.doge_transaction_checker import dogeTransactionChecker
from decimal import Decimal

from imports.utils import log_message
from commands.escrow import close_trade
from globalState import GlobalState
from imports.wallet_utils import sendtrans

def execute(bot_state: GlobalState, bot):
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

        time.sleep(20)

def handleResponse(response, bot_state: GlobalState, bot):
    wallet = bot_state.get_address_info(response['publicKey'])
    log_file = response['publicKey']
    tradeDetails = {}
    type = "TRADE"
    if wallet['tradeId'].startswith('TRADE'):
        tradeDetails = bot_state.get_var(wallet['tradeId'])
    elif wallet['tradeId'].startswith('TXID'):
        type = "TX"
        tradeDetails = bot_state.get_tx_var(wallet['tradeId'])
    else:
        print(f"Invalid action id supplied: {wallet['tradeId']}") #error itself doesnt make any sense but here we go
        return False
    if tradeDetails['currency'] == 'LTC':
        if isinstance(response, dict) and response.get("code") == "confirmed":
            bot_state.remove_address_from_queue(response['publicKey'])
            log_message(f"[LTC wallet Checker]:: {response['publicKey']} Transaction for {response['amount']} detected", log_file)
            if(float(response['amount'])>=float(tradeDetails["tradeAmount"])):
                proceed_transaction(bot_state, wallet['tradeId'], wallet, tradeDetails, bot)
            else:
                if type == "TRADE":
                    handle_escrow_insuff(response, bot, tradeDetails, bot_state)
                elif type == "TX":
                    handle_buy_item_insuff(response, bot, tradeDetails, bot_state, wallet)
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
                proceed_transaction(bot_state, wallet['tradeId'], wallet, tradeDetails, bot)
            else:
                if type == "TRADE":
                    handle_escrow_insuff(response, bot, tradeDetails, bot_state)
                elif type == "TX":
                    handle_buy_item_insuff(response, bot, tradeDetails, bot_state, wallet)
        elif isinstance(response, dict) and response.get("code") == "unconfirmed":
            log_message(f"[DOGE wallet Checker]:: {response['publicKey']} Transaction is detected but unconfirmed", log_file)
        elif isinstance(response, dict) and response.get("code") == "undetected":
            print(f"[DOGE wallet Checker]:: {response['publicKey']} no transactions")
        else:
            # Handle errors
            log_message(f"Error: {response}", log_file)
    elif tradeDetails['currency'] == "SOL (Solana)" or tradeDetails['currency'] == "USDT (Solana)":
        #testing
        # proceed_transaction(bot_state, wallet['tradeId'], response, tradeDetails, bot)
        # bot_state.remove_address_from_queue(response['publicKey'])
        # return
        if(response["amount"]>= Decimal(tradeDetails["tradeAmount"])):
            print(f"[SOL Wallet Checker]:: Transaction detected for wallet {tradeDetails['ourAddress']} of {response['amount']} {tradeDetails['currency']}")
            bot_state.remove_address_from_queue(response['publicKey'])
            proceed_transaction(bot_state, wallet['tradeId'], wallet, tradeDetails, bot)
        elif response["amount"] == 0:
            print(f"[SOL wallet Checker]:: {tradeDetails['ourAddress']} no transactions")
        else:
            if type == "TRADE":
                handle_escrow_insuff(response, bot, tradeDetails, bot_state)
            elif type == "TX":
                handle_buy_item_insuff(response, bot, tradeDetails, bot_state, wallet)
    # elif tradeDetails['currency'] == "BNB (BSC Bep-20)" or tradeDetails['currency'] == "USDT (BSC Bep-20)":
    #     if(response["amount"]>= Decimal(tradeDetails["tradeAmount"])):
    #         print(f"[BSC Wallet Checker]:: Transaction detected for wallet {tradeDetails['ourAddress']} of {response['amount']} {tradeDetails['currency']}")
    #         bot_state.remove_address_from_queue(response['publicKey'])
    #         proceed_transaction(bot_state, wallet['tradeId'], wallet, tradeDetails, bot)
    #     elif response["amount"] == 0:
    #         print(f"[BSC wallet Checker]:: {tradeDetails['ourAddress']} no transactions")
    #     else:
    #         if type == "TRADE":
    #             handle_escrow_insuff(response, bot, tradeDetails, bot_state)
    #         elif type == "TX":
    #             handle_buy_item_insuff(response, bot, tradeDetails, bot_state, wallet)

def handle_escrow_insuff(response, bot, tradeDetails, bot_state, wallet):
    bot_state.remove_address_from_queue(response['publicKey'])
    bot.send_message(chat_id=tradeDetails["buyer"], text="Your Transaction seems to have less than the quoted amount in trade, contact @addylad6725 for resolution")
    bot.send_message(chat_id=tradeDetails["seller"], text="The buyer has sent less than the agreed amount, so we have cancled the trade")
    close_trade(bot_state=bot_state, action_id=wallet['tradeId'], message="close[insuff_funds_receieved]")

def handle_buy_item_insuff(response, bot, tx_details, bot_state, wallet):
    bot_state.remove_address_from_queue(response['publicKey'])
    bot.send_message(chat_id=tx_details["buyer"], text="Your Transaction seems to have less than the quoted amount in trade, contact @addylad6725 for resolution")
    close_trade(bot_state=bot_state, action_id=wallet['tradeId'], message="close[insuff_funds_receieved]")

def proceed_transaction(bot_state: GlobalState, tradeId, wallet, tradeDetails, bot):
    #wallet = bot_state.get_address_info(response['publicKey'])
    if wallet['tradeId'].startswith('TRADE'):
        tradeDetails['status'] = 'open[paid]'
        bot_state.set_var(tradeId, tradeDetails)
        bot.send_message(chat_id=tradeDetails["buyer"], text="Your Transaction is now confirmed in Blockchain, seller is now notified to send your product")
        keyboard = [
            [InlineKeyboardButton("I have Sent", callback_data='option_9')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        message = bot.send_message(
            chat_id=tradeDetails["seller"], 
            text="Buyer has sent the payment to our escrow wallet, You can now safely deliever your product \n\n It's recomended that you keep delievery and working proof to yourself until you receive the payment. \n\n CLick button below after you have delivered it",
            reply_markup=reply_markup
        )
        bot_state.set_waiting_for_input(tradeDetails["seller"], [message], 'button', 'commands.escrow')
    elif wallet['tradeId'].startswith('TXID'):
        item_details = bot_state.get_item_details(tradeDetails["item_id"])
        tradeDetails['status'] = 'open[paid]'
        bot_state.remove_timer(tradeDetails['payment_timeout'])
        try:
            message = bot.edit_message_text(
                parse_mode=ParseMode.MARKDOWN,
                text=f"━━━━⍟𝗘𝘀𝗰𝗿𝗼𝘄 𝗦𝗵𝗶𝗲𝗹𝗱⍟━━━━\n𝗧𝘅 𝗜𝗗: `{tradeId}`\n𝗜𝘁𝗲𝗺: {item_details['title']}\n𝗦𝗲𝗹𝗹𝗲𝗿: @{tradeDetails['seller_username']}\n𝗡𝗲𝘁 𝗖𝗵𝗮𝗿𝗴𝗲𝘀: {tradeDetails['tradeAmount']}\n𝗗𝗲𝗹𝗶𝘃𝗲𝗿𝘆 𝗠𝗼𝗱𝗲: {item_details['type']}\n𝗜𝗻𝘃𝗼𝗶𝗰𝗲 𝗦𝘁𝗮𝘁𝘂𝘀: Paid\n",
                chat_id=tradeDetails["buyer"],
                message_id=tradeDetails["message_id"]
            )
        except TelegramError as e:
            error_message = f"An error occurred: {str(e)}\n"
            error_message += ''.join(traceback.format_exception(None, e, e.__traceback__))
            log_message(error_message, wallet['publicKey'])
            bot.send_message(
                parse_mode=ParseMode.MARKDOWN,
                chat_id=tradeDetails["buyer"], 
                text=f"━━━━⍟𝗘𝘀𝗰𝗿𝗼𝘄 𝗦𝗵𝗶𝗲𝗹𝗱⍟━━━━\n𝗧𝘅 𝗜𝗗: `{tradeId}`\n𝗜𝘁𝗲𝗺: {item_details['title']}\n𝗦𝗲𝗹𝗹𝗲𝗿: @{tradeDetails['seller_username']}\n𝗡𝗲𝘁 𝗖𝗵𝗮𝗿𝗴𝗲𝘀: {tradeDetails['tradeAmount']}\n𝗗𝗲𝗹𝗶𝘃𝗲𝗿𝘆 𝗠𝗼𝗱𝗲: {item_details['type']}\n𝗜𝗻𝘃𝗼𝗶𝗰𝗲 𝗦𝘁𝗮𝘁𝘂𝘀: Paid\n", 
            )
        if item_details['type'] == 'automatic':
            if item_details['stock'] > 0:
                delivery = item_details['stockList'].pop()
                bot_state.add_item(tradeDetails["item_id"], item_details)
                tradeDetails['delivery'] = delivery
                keyboard = [
                    [InlineKeyboardButton("Take Delivery", callback_data='option_23')],
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                message = bot.send_message(
                    parse_mode=ParseMode.MARKDOWN,
                    chat_id=tradeDetails["buyer"],
                    text=f"━━━━⍟𝗘𝘀𝗰𝗿𝗼𝘄 𝗦𝗵𝗶𝗲𝗹𝗱⍟━━━━\n*Item Delivery*\n𝗧𝘅 𝗜𝗗: `{tradeId}`\n𝗜𝘁𝗲𝗺: {item_details['title']}\n𝗡𝗲𝘁 𝗖𝗵𝗮𝗿𝗴𝗲𝘀: {tradeDetails['tradeAmount']} *{tradeDetails['currency']}*\nWe recommend to start recording a video while clicking 'Take Delivery' and verifying your keys for proof", 
                    reply_markup=reply_markup
                )
                bot_state.set_waiting_for_input(tradeDetails["buyer"], [message, {'tx_id': tradeId, 'context': 'deliveryClaim'}], 'button')
                
                bot_state.set_tx_var(tradeId, tradeDetails)
                close_trade(bot_state, tradeId, 'close[delivered]')
        elif item_details['type'] == 'manual':
            bot.send_message(
                chat_id=tradeDetails["buyer"],
                parse_mode=ParseMode.MARKDOWN,
                text=f"━━━━⍟𝗘𝘀𝗰𝗿𝗼𝘄 𝗦𝗵𝗶𝗲𝗹𝗱⍟━━━━\n𝗧𝘅 𝗜𝗗: `{tradeId}`\n𝗜𝘁𝗲𝗺: {item_details['title']}\n𝗡𝗲𝘁 𝗖𝗵𝗮𝗿𝗴𝗲𝘀: {tradeDetails['tradeAmount']} *{tradeDetails['currency']}*\nSeller is notified to Deliver your Product.\n(if seller fails to deliver within 1 day or you have issues contact us)", 
            )
            keyboard = [
                [InlineKeyboardButton("I have Sent", callback_data='option_20')],
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            message = bot.send_message(
                chat_id=item_details["seller"],
                parse_mode=ParseMode.MARKDOWN,
                text=f"━━━━⍟𝗘𝘀𝗰𝗿𝗼𝘄 𝗦𝗵𝗶𝗲𝗹𝗱⍟━━━━\n𝗧𝘅 𝗜𝗗: `{tradeId}`\n𝗜𝘁𝗲𝗺: {item_details['title']}\n𝗡𝗲𝘁 𝗖𝗵𝗮𝗿𝗴𝗲𝘀: {tradeDetails['tradeAmount']} *{tradeDetails['currency']}*\n𝗕𝘂𝘆𝗲𝗿: {tradeDetails['buyer']}\n\nThe Buyer has paid the amount, do the delivery!", 
                reply_markup=reply_markup
            )
            bot_state.set_waiting_for_input(tradeDetails["seller"], [message, {'tx_id': tradeId, 'context': 'product_verification'}], 'button')
        
            t = bot_state.add_timeout(24*60*60, tradeId)
            tradeDetails['manual_timeout'] = t
            bot_state.set_tx_var(tradeId, tradeDetails)
    else:
        print(f"Invalid action id supplied: {wallet['tradeId']}") #error itself doesnt make any sense but here we go
        return False
    
    
def timeout_up(context, bot, bot_state: GlobalState):
    if context.startswith('TXID'):
        tx_details = bot_state.get_tx_var(context)
        item_details = bot_state.get_item_details(tx_details['item_id'])
        if item_details['type'] == 'automatic':
            bot.send_message(
                chat_id=tx_details["buyer"], 
                parse_mode=ParseMode.MARKDOWN,
                text=f"━━━━⍟𝗘𝘀𝗰𝗿𝗼𝘄 𝗦𝗵𝗶𝗲𝗹𝗱⍟━━━━\n𝗧𝘅 𝗜𝗗: `{context}`\n𝗜𝘁𝗲𝗺: {item_details['title']}\n𝗡𝗲𝘁 𝗖𝗵𝗮𝗿𝗴𝗲𝘀: {tx_details['tradeAmount']} *{tx_details['currency']}*\n\n You Failed to provide a response, releasing payment to Seller",   
            )
            sendtrans(bot_state, context)
            bot.send_message(
                chat_id=item_details["seller"], 
                parse_mode=ParseMode.MARKDOWN,
                text=f"━━━━⍟𝗘𝘀𝗰𝗿𝗼𝘄 𝗦𝗵𝗶𝗲𝗹𝗱⍟━━━━\n𝗧𝘅 𝗜𝗗: `{context}`\n𝗜𝘁𝗲𝗺: {item_details['title']}\n𝗡𝗲𝘁 𝗖𝗵𝗮𝗿𝗴𝗲𝘀: {tx_details['tradeAmount']} *{tx_details['currency']}*\n\n Your Payment has been released",   
            )
            close_trade(bot_state, context, 'close[success]')
        elif item_details['type'] == 'manual' and tx_details['sellerStatus'] != 'delivered': #manual type
            bot.send_message(
                chat_id=item_details["seller"], 
                parse_mode=ParseMode.MARKDOWN,
                text=f"━━━━⍟𝗘𝘀𝗰𝗿𝗼𝘄 𝗦𝗵𝗶𝗲𝗹𝗱⍟━━━━\n𝗧𝘅 𝗜𝗗: `{context}`\n𝗜𝘁𝗲𝗺: {item_details['title']}\n𝗡𝗲𝘁 𝗖𝗵𝗮𝗿𝗴𝗲𝘀: {tx_details['tradeAmount']} *{tx_details['currency']}*\n\n You Failed to deliver goods within 1 day, transaction has been marked Canceled!",   
            )
            bot.send_message(
                chat_id=tx_details["buyer"],
                parse_mode=ParseMode.MARKDOWN,
                text=f"━━━━⍟𝗘𝘀𝗰𝗿𝗼𝘄 𝗦𝗵𝗶𝗲𝗹𝗱⍟━━━━\n𝗧𝘅 𝗜𝗗: `{context}`\n𝗜𝘁𝗲𝗺: {item_details['title']}\n𝗡𝗲𝘁 𝗖𝗵𝗮𝗿𝗴𝗲𝘀: {tx_details['tradeAmount']} *{tx_details['currency']}*\n\n Seller failed to provide you a solution it seems, you can collect your funds by contacting us.",   
            )
            close_trade(bot_state, context, 'close[manual_delivery_timeout]')
        elif item_details['type'] == 'manual' and tx_details['sellerStatus'] == 'delivered':
            bot.send_message(
                chat_id=tx_details["buyer"],
                parse_mode=ParseMode.MARKDOWN,
                text=f"━━━━⍟𝗘𝘀𝗰𝗿𝗼𝘄 𝗦𝗵𝗶𝗲𝗹𝗱⍟━━━━\n𝗧𝘅 𝗜𝗗: `{context}`\n𝗜𝘁𝗲𝗺: {item_details['title']}\n𝗡𝗲𝘁 𝗖𝗵𝗮𝗿𝗴𝗲𝘀: {tx_details['tradeAmount']} *{tx_details['currency']}*\n\n You Failed to provide a response, releasing payment to Seller",   
            )
            sendtrans(bot_state, context)
            close_trade(bot_state, context, 'close[success]')

def button(update: Update, context: CallbackContext, bot_state: GlobalState):
    query = update.callback_query
    #message_id = query.message.message_id
    button_context = bot_state.get_waiting_for_input_context(str(query.from_user.id))
    tx_id = button_context['tx_id']
    tx_details = bot_state.get_tx_var(tx_id)
    item_details = bot_state.get_item_details(tx_details['item_id'])
    
    if tx_details['status'] not in ['open[paid]', 'close[delivered]']:
        return
    if button_context['context'] == 'deliveryClaim':
        keyboard = [
            [InlineKeyboardButton("Confirm Working", callback_data='option_18')],
            [InlineKeyboardButton("I am Having Issues", callback_data='option_19')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        message = context.bot.edit_message_text(
            message_id=button_context["message_id"],
            parse_mode=ParseMode.MARKDOWN,
            chat_id=tx_details["buyer"],
            text=f"━━━━⍟𝗘𝘀𝗰𝗿𝗼𝘄 𝗦𝗵𝗶𝗲𝗹𝗱⍟━━━━\n𝗧𝘅 𝗜𝗗: `{tx_id}`\n𝗜𝘁𝗲𝗺: {item_details['title']}\n𝗡𝗲𝘁 𝗖𝗵𝗮𝗿𝗴𝗲𝘀: {tx_details['tradeAmount']} *{tx_details['currency']}*\nDelivery Key(s):\n {tx_details['delivery']}\n(you have 10 minutes to confirm if working or not)", 
            reply_markup=reply_markup
        )
        bot_state.set_waiting_for_input(tx_details["buyer"], [message, {'tx_id': tx_id, 'context': 'product_verification'}], 'button')
        t = bot_state.add_timeout(10*60, tx_id)
        tx_details['product_confirmation_timeout'] = t
        bot_state.set_tx_var(tx_id, tx_details)

    elif query.data == 'option_18' and str(query.from_user.id) == tx_details['buyer']:
        bot_state.remove_timer(tx_details['product_confirmation_timeout'])
        context.bot.send_message(
            chat_id=tx_details["buyer"], 
            parse_mode=ParseMode.MARKDOWN,
            text=f"━━━━⍟𝗘𝘀𝗰𝗿𝗼𝘄 𝗦𝗵𝗶𝗲𝗹𝗱⍟━━━━\n𝗧𝘅 𝗜𝗗: `{tx_id}`\n𝗜𝘁𝗲𝗺: {item_details['title']}\n𝗡𝗲𝘁 𝗖𝗵𝗮𝗿𝗴𝗲𝘀: {tx_details['tradeAmount']} *{tx_details['currency']}*\nAlrighty Right! Releasing payment to Seller, don't forget to share about our services.", 
        )
        sendtrans(bot_state, tx_id)
        context.bot.send_message(
            chat_id=item_details["seller"],
            parse_mode=ParseMode.MARKDOWN,
            text=f"━━━━⍟𝗘𝘀𝗰𝗿𝗼𝘄 𝗦𝗵𝗶𝗲𝗹𝗱⍟━━━━\n𝗧𝘅 𝗜𝗗: `{tx_id}`\n𝗜𝘁𝗲𝗺: {item_details['title']}\n𝗡𝗲𝘁 𝗖𝗵𝗮𝗿𝗴𝗲𝘀: {tx_details['tradeAmount']} *{tx_details['currency']}*\n\n𝗕𝘂𝘆𝗲𝗿: @{tx_details['buyer_username']}\n\n Your Payment has been released",   
        )
        close_trade(bot_state, tx_id, 'close[success]')
        
    elif query.data == 'option_19'and str(query.from_user.id) == tx_details['buyer']:
        bot_state.remove_timer(tx_details['product_confirmation_timeout'])
        context.bot.send_message(
            chat_id=item_details["seller"], 
            parse_mode=ParseMode.MARKDOWN,
            text=f"━━━━⍟𝗘𝘀𝗰𝗿𝗼𝘄 𝗦𝗵𝗶𝗲𝗹𝗱⍟━━━━\n𝗧𝘅 𝗜𝗗: `{tx_id}`\n𝗜𝘁𝗲𝗺: {item_details['title']}\n𝗡𝗲𝘁 𝗖𝗵𝗮𝗿𝗴𝗲𝘀: {tx_details['tradeAmount']} *{tx_details['currency']}*\n\n𝗕𝘂𝘆𝗲𝗿: @{tx_details['buyer_username']}\n Buyer seems to be having Issues with the order, fix that by contacting them within 24 hours",   
        )
        keyboard = [
            [InlineKeyboardButton("Resolved", callback_data='option_21')],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        message = context.bot.send_message(
            chat_id=tx_details["buyer"],
            parse_mode=ParseMode.MARKDOWN,
            text=f"━━━━⍟𝗘𝘀𝗰𝗿𝗼𝘄 𝗦𝗵𝗶𝗲𝗹𝗱⍟━━━━\n𝗧𝘅 𝗜𝗗: `{tx_id}`\n𝗜𝘁𝗲𝗺: {item_details['title']}\n𝗡𝗲𝘁 𝗖𝗵𝗮𝗿𝗴𝗲𝘀: {tx_details['tradeAmount']} *{tx_details['currency']}*\n\n𝗦𝗲𝗹𝗹𝗲𝗿: @{tx_details['seller_username']}\n\n Seller is notified to assist you, they have 1 day to resolve\nClick button below if issue is resolved", 
            reply_markup=reply_markup
        )
        bot_state.set_waiting_for_input(tx_details["buyer"], [message, {'tx_id': tx_id, 'context': 'issue_resolved'}], 'button')
        
    elif query.data == 'option_21'and str(query.from_user.id) == tx_details['buyer']:
        context.bot.send_message(
            chat_id=tx_details["buyer"], 
            parse_mode=ParseMode.MARKDOWN,
            text=f"━━━━⍟𝗘𝘀𝗰𝗿𝗼𝘄 𝗦𝗵𝗶𝗲𝗹𝗱⍟━━━━\n𝗧𝘅 𝗜𝗗: `{tx_id}`\n𝗜𝘁𝗲𝗺: {item_details['title']}\n𝗡𝗲𝘁 𝗖𝗵𝗮𝗿𝗴𝗲𝘀: {tx_details['tradeAmount']} *{tx_details['currency']}*\n Alrighty Right! Releasing payment to Seller, Dont forgot to share about our services.", 
        )
        sendtrans(bot_state, tx_id)
        context.bot.send_message(
            chat_id=item_details["seller"],
            parse_mode=ParseMode.MARKDOWN,
            text=f"━━━━⍟𝗘𝘀𝗰𝗿𝗼𝘄 𝗦𝗵𝗶𝗲𝗹𝗱⍟━━━━\n𝗧𝘅 𝗜𝗗: `{tx_id}`\n𝗜𝘁𝗲𝗺: {item_details['title']}\n𝗡𝗲𝘁 𝗖𝗵𝗮𝗿𝗴𝗲𝘀: {tx_details['tradeAmount']} *{tx_details['currency']}*\n\n𝗕𝘂𝘆𝗲𝗿: {tx_details['buyer_username']}\n\n Your Payment has been released",   
        )
        close_trade(bot_state, tx_id, 'close[success]')
    elif query.data == 'option_20'and str(query.from_user.id) == item_details['seller']:
        bot_state.remove_timer(tx_details['manual_timeout'])
        tx_details['sellerStatus'] = 'delivered'
        context.bot.send_message(
            chat_id=item_details["seller"],
            parse_mode=ParseMode.MARKDOWN,
            text=f"━━━━⍟𝗘𝘀𝗰𝗿𝗼𝘄 𝗦𝗵𝗶𝗲𝗹𝗱⍟━━━━\n𝗧𝘅 𝗜𝗗: `{tx_id}`\n𝗜𝘁𝗲𝗺: {item_details['title']}\n𝗡𝗲𝘁 𝗖𝗵𝗮𝗿𝗴𝗲𝘀: {tx_details['tradeAmount']} *{tx_details['currency']}*\n\n𝗕𝘂𝘆𝗲𝗿: {tx_details['buyer_username']}\n\n Asking Buyer for Confirmation",   
        )
        keyboard = [
            [InlineKeyboardButton("Confirm Working", callback_data='option_18')],
            [InlineKeyboardButton("I am Having Issues", callback_data='option_19')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        message = context.bot.send_message(
            chat_id=tx_details["buyer"], 
            parse_mode=ParseMode.MARKDOWN,
            text=f"━━━━⍟𝗘𝘀𝗰𝗿𝗼𝘄 𝗦𝗵𝗶𝗲𝗹𝗱⍟━━━━\n𝗧𝘅 𝗜𝗗: `{tx_id}`\n𝗜𝘁𝗲𝗺: {item_details['title']}\n𝗡𝗲𝘁 𝗖𝗵𝗮𝗿𝗴𝗲𝘀: {tx_details['tradeAmount']} *{tx_details['currency']}*\n Seller says to have delivered the product(s), click the button below to confirm (you have 10 minutes to confirm if working or not)", 
            reply_markup=reply_markup
        )
        bot_state.set_waiting_for_input(tx_details["buyer"], [message, {'tx_id': tx_id, 'context': 'product_verification'}], 'button')
        t = bot_state.add_timeout(10*60, tx_id)
        tx_details['product_confirmation_timeout'] = t
        bot_state.set_tx_var(tx_id, tx_details)
        close_trade(bot_state, tx_id, 'close[delivered]')
        
    query.answer()
