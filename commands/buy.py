import time
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ParseMode
from telegram.ext import CallbackContext
import random

from globalState import GlobalState
from imports.utils import *
from imports.wallet_utils import *
from commands.cancel import close_trade

def execute(update: Update, context: CallbackContext, bot_state: GlobalState) -> None:
    user_input = ''
    if len(context.args)>0:
        user_input = context.args[0]
    else:
        update.message.reply_text("Enter a item ID")
        return
    item_details = bot_state.get_item_details(user_input)
    if not item_details or len(item_details)<=2:
        update.message.reply_text("Invalid Item ID")
        return
    if item_details['toggle'] == 'disabled' or (item_details['stock']-item_details['lockedStock']) <=0:
        update.message.reply_text("Item is unavaliable for purchase at the moment")
        return
    item_details['lockedStock'] += 1
    tx_id = "TXID"+''.join([str(random.randint(0, 9)) for _ in range(12)])
    tx_details = {
        "buyer": str(update.message.from_user.id),
        "buyer_username": update.message.from_user.username if update.message.from_user.username else update.message.from_user.full_name,
        "seller_username": context.bot.get_chat(item_details['seller']).username if context.bot.get_chat(item_details['seller']).username else context.bot.get_chat(item_details['seller']).full_name,
        "item_id": context.args[0],
        "timestamp": int(time.time()),
        "currency": item_details['currency'], #In case i add a functionality for an item to change currency later
        "itemAmount": 1,
        "tradeAmount": item_details['price'],
        "fee": 0,
        "fee_percentage" : 0,
        "ourAddress": '',
        "openUpto": 0, #
        "status": "open",
        "lastRefresh": 0,
        "message_id": ''
    }
    result = multi_task(
        [
            [update.message.reply_text, "Generating an Invoice...", ParseMode.MARKDOWN],
            [bot_state.add_item, user_input, item_details],
            [bot_state.set_tx_var, tx_id, tx_details],
            [generateWallet, tx_id, bot_state]

        ]
    )
    message, wallet = result[0], result[3]
    if not wallet:
        pass #stop tx tch
    tx_details['ourAddress'] = wallet
    tx_details['openUpto'] = int(time.time())+(10*60)
    tx_details['lastRefresh'] = int(time.time())
    tx_details['message_id'] = message.message_id
    tx_details['payment_timeout'] = bot_state.add_timeout(10*60,tx_id, 'commands.buy')
    tx_details['fee_percentage'] = bot_state.config['usdt_fee_percentage']/100
    tx_details['fee'] = calc_fee(tx_details['tradeAmount'], tx_details['fee_percentage'], tx_details['currency'], True)
    tx_details['tradeAmount'] = Decimal(tx_details['tradeAmount'])
    tx_details['tradeAmount'] += tx_details['fee']
    tx_details['tradeAmount'] = str(tx_details['tradeAmount'])
    tx_details['fee'] = str(tx_details['fee'])
    tx_details['fee_percentage'] = str(tx_details['fee_percentage'])
    reply_markup = InlineKeyboardMarkup([
        [InlineKeyboardButton("Refresh Time", callback_data='option_16')],
        [InlineKeyboardButton("I have Sent", callback_data='option_17')],
    ])
    result = multi_task(
        [
            [bot_state.set_tx_var, tx_id, tx_details],
            [bot_state.set_waiting_for_input, str(update.message.from_user.id), [message, {'tx_id': tx_id}], 'button', 'commands.buy'],
            [
                context.bot.edit_message_text, 
                {
                    'text':f"━━━━⍟𝗘𝘀𝗰𝗿𝗼𝘄 𝗦𝗵𝗶𝗲𝗹𝗱⍟━━━━\n𝗧𝘅 𝗜𝗗: `{tx_id}`\n𝗜𝘁𝗲𝗺: {item_details['title']}\n𝗦𝗲𝗹𝗹𝗲𝗿: @{tx_details['seller_username']}\n𝗡𝗲𝘁 𝗖𝗵𝗮𝗿𝗴𝗲𝘀: `{tx_details['tradeAmount']}` *{tx_details['currency']}*\n𝗘𝘀𝗰𝗿𝗼𝘄 𝗙𝗲𝗲:{str(tx_details['fee'])} ({str(tx_details['fee_percentage']*100)}%)\n𝗗𝗲𝗹𝗶𝘃𝗲𝗿𝘆 𝗠𝗼𝗱𝗲: {item_details['type']}\n𝗧𝗶𝗺𝗲 𝗥𝗲𝗺𝗮𝗶𝗻𝗶𝗻𝗴: 10min\n𝗜𝗻𝘃𝗼𝗶𝗰𝗲 𝗦𝘁𝗮𝘁𝘂𝘀: Open\n\nSend only `{tx_details['tradeAmount']}` *{tx_details['currency']}* to address below\n`{tx_details['ourAddress']}` \n\n *NOTE:* If sending from an Exchange, be sure to withdraw this amount *plus Exchange's fee*",
                    'reply_markup':reply_markup,
                    'chat_id':message.chat_id,
                    'message_id':message.message_id,
                    'parse_mode':ParseMode.MARKDOWN
                }
            ]
        ]
    )
    
def button(update: Update, context: CallbackContext, bot_state: GlobalState) -> None:
    query = update.callback_query
    tx_id = bot_state.get_waiting_for_input_context(query.from_user.id)['tx_id']
    tx_details = bot_state.get_tx_var(tx_id)
    item_details = bot_state.get_item_details(tx_details['item_id'])
    if tx_details['status'] != 'open' and tx_details['status'] != 'open[awaiting_payment]':
        query.answer()
        return
    time_left = int(tx_details['openUpto']) - int(time.time())
    minutes, seconds = divmod(time_left, 60)
    time_text = 'tch'
    if seconds == 0:
        time_text = f"{minutes} min"
    elif minutes == 0:
        time_text = f"{seconds} sec"
    else:
        time_text = f"{minutes} min {seconds} sec"

    if query.data == 'option_16':
        slowmode = int(time.time()) - int(tx_details['lastRefresh'])
        if slowmode < 30:
            slowmode = 30-slowmode
            bot_state.set_waiting_for_input(str(query.from_user.id), [query.message, {'tx_id': tx_id}], 'button')
            query.answer(text=f"Try to refresh time after {slowmode}sec", show_alert=True)
            return
        if time_left <= 0:
            try: 
                query.edit_message_text(
                    parse_mode=ParseMode.MARKDOWN,
                    text=f"━━━━⍟𝗘𝘀𝗰𝗿𝗼𝘄 𝗦𝗵𝗶𝗲𝗹𝗱⍟━━━━\n𝗧𝘅 𝗜𝗗: `{tx_id}`\n𝗜𝘁𝗲𝗺: {item_details['title']}\n𝗦𝗲𝗹𝗹𝗲𝗿: @{tx_details['seller_username']}\n𝗡𝗲𝘁 𝗖𝗵𝗮𝗿𝗴𝗲𝘀: `{tx_details['tradeAmount']}` *{tx_details['currency']}*\n𝗗𝗲𝗹𝗶𝘃𝗲𝗿𝘆 𝗠𝗼𝗱𝗲: {item_details['type']}\n𝗧𝗶𝗺𝗲 𝗥𝗲𝗺𝗮𝗶𝗻𝗶𝗻𝗴: {time_text}\n𝗜𝗻𝘃𝗼𝗶𝗰𝗲 𝗦𝘁𝗮𝘁𝘂𝘀: Closed\n\nSend only {tx_details['currency']} to address below\n`{tx_details['ourAddress']}`\n\n *NOTE:* If sending from an Exchange, be sure to withdraw this amount *plus Exchange's fee*",
                )
            except:
                pass
            #close Transaction Function
            return
        else:
            tx_details['lastRefresh'] = int(time.time())
            bot_state.set_tx_var(tx_id, tx_details)
            bot_state.set_waiting_for_input(str(query.from_user.id), [query.message, {'tx_id': tx_id}], 'button')
            reply_markup='tch'
            msg_piece = 'tch'
            if tx_details['status'] == 'open':
                msg_piece = "Open"
                reply_markup = InlineKeyboardMarkup([
                    [InlineKeyboardButton("Refresh Time", callback_data='option_16')],
                    [InlineKeyboardButton("I have Sent", callback_data='option_17')],
                ])
            else:
                msg_piece = 'Awating for Txn in blockchain'
                reply_markup = InlineKeyboardMarkup([
                    [InlineKeyboardButton("Refresh Time", callback_data='option_16')]
                ])
            try:
                query.edit_message_text(
                    text=f"━━━━⍟𝗘𝘀𝗰𝗿𝗼𝘄 𝗦𝗵𝗶𝗲𝗹𝗱⍟━━━━\n𝗧𝘅 𝗜𝗗: `{tx_id}`\n𝗜𝘁𝗲𝗺: {item_details['title']}\n𝗦𝗲𝗹𝗹𝗲𝗿: @{tx_details['seller_username']}\n𝗡𝗲𝘁 𝗖𝗵𝗮𝗿𝗴𝗲𝘀: `{tx_details['tradeAmount']}` *{tx_details['currency']}*\n𝗗𝗲𝗹𝗶𝘃𝗲𝗿𝘆 𝗠𝗼𝗱𝗲: {item_details['type']}\n𝗧𝗶𝗺𝗲 𝗥𝗲𝗺𝗮𝗶𝗻𝗶𝗻𝗴: {time_text}\n𝗜𝗻𝘃𝗼𝗶𝗰𝗲 𝗦𝘁𝗮𝘁𝘂𝘀: {msg_piece}\n\nSend only {tx_details['tradeAmount']} {tx_details['currency']} to address below\n`{tx_details['ourAddress']}` \n\n *NOTE:* If sending from an Exchange, be sure to withdraw this amount *plus Exchange's fee*",
                    reply_markup=reply_markup,
                    parse_mode=ParseMode.MARKDOWN
                )
            except:
                pass
    
    elif query.data == 'option_17':
        bot_state.set_waiting_for_input(str(query.from_user.id), [query.message, {'tx_id': tx_id}], 'button')
        context.bot.send_message(chat_id=tx_details['buyer'], text="━━━━⍟𝗘𝘀𝗰𝗿𝗼𝘄 𝗦𝗵𝗶𝗲𝗹𝗱⍟━━━━\nAlrighty Right! We will check your payment status every minute now until we receive it, once confirmed in Blockchain, we will proceed.")
        bot_state.add_address_to_check_queue(tx_details["ourAddress"], tx_id,  tx_details["currency"])
        reply_markup = InlineKeyboardMarkup([
            [InlineKeyboardButton("Refresh Time", callback_data='option_16')],
        ])
        tx_details['status'] = 'open[awaiting_payment]'
        bot_state.set_tx_var(tx_id, tx_details)
        try:
            query.edit_message_text(
                parse_mode=ParseMode.MARKDOWN,
                text=f"━━━━⍟𝗘𝘀𝗰𝗿𝗼𝘄 𝗦𝗵𝗶𝗲𝗹𝗱⍟━━━━\n𝗧𝘅 𝗜𝗗: `{tx_id}`\n𝗜𝘁𝗲𝗺: {item_details['title']}\n𝗦𝗲𝗹𝗹𝗲𝗿: @{tx_details['seller_username']}\n𝗡𝗲𝘁 𝗖𝗵𝗮𝗿𝗴𝗲𝘀: `{tx_details['tradeAmount']}` *{tx_details['currency']}*\n𝗗𝗲𝗹𝗶𝘃𝗲𝗿𝘆 𝗠𝗼𝗱𝗲: {item_details['type']}\n𝗧𝗶𝗺𝗲 𝗥𝗲𝗺𝗮𝗶𝗻𝗶𝗻𝗴: {time_text}\n𝗜𝗻𝘃𝗼𝗶𝗰𝗲 𝗦𝘁𝗮𝘁𝘂𝘀: Awaiting Blockchain Confirmation\n\nSend only {tx_details['tradeAmount']} {tx_details['currency']} to address below\n`{tx_details['ourAddress']}` \n\n *NOTE:* If sending from an Exchange, be sure to withdraw this amount *plus Exchange's fee*",
                reply_markup=reply_markup
            )
        except:
            pass
    query.answer()
def timeout_up(context, bot, bot_state: GlobalState):
    tx_details = bot_state.get_tx_var(context)
    item_details = bot_state.get_item_details(tx_details['item_id'])
    if tx_details['status'] in ["open", "open[awaiting_payment]"]:
        close_trade(bot_state, context, 'close[payment_timeout]')
        bot.edit_message_text(
            text=f"━━━━⍟𝗘𝘀𝗰𝗿𝗼𝘄 𝗦𝗵𝗶𝗲𝗹𝗱⍟━━━━\n𝗧𝘅 𝗜𝗗: `{context}`\n𝗜𝘁𝗲𝗺: {item_details['title']}\n𝗦𝗲𝗹𝗹𝗲𝗿: @{tx_details['seller_username']}\n𝗡𝗲𝘁 𝗖𝗵𝗮𝗿𝗴𝗲𝘀: `{tx_details['tradeAmount']}` *{tx_details['currency']}*\n𝗗𝗲𝗹𝗶𝘃𝗲𝗿𝘆 𝗠𝗼𝗱𝗲: {item_details['type']}\n𝗧𝗶𝗺𝗲 𝗥𝗲𝗺𝗮𝗶𝗻𝗶𝗻𝗴: Time Out!\n𝗜𝗻𝘃𝗼𝗶𝗰𝗲 𝗦𝘁𝗮𝘁𝘂𝘀: Invoice Expired",
            chat_id=tx_details['buyer'],
            message_id=tx_details['message_id'],
            parse_mode=ParseMode.MARKDOWN,
        )
description = "Buy an item from Shop"
aliases = ['/buy']
enabled = False
hidden = True
OperaterCommand = False
