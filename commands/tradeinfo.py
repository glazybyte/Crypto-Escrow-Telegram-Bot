from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ParseMode
from telegram.ext import CallbackContext

from globalState import GlobalState
from imports.utils import escape_markdown_v2
from datetime import datetime
def execute(update: Update, context: CallbackContext,bot_state: GlobalState) -> None:
    if str(update.message.from_user.id) not in [bot_state.config['bot_owner']] + bot_state.config['bot_moderators']:
        return  # Not authorized
    if not context.args:
        update.message.reply_text("Please provide an trade ID.\n /ti <trade_id>")
        return
    selection = context.args[0]
    if selection.startswith("TRADE"):
        tradeDetails = bot_state.get_var(selection)
        if not tradeDetails:
            update.message.reply_text("Trade not found")
            return
        steps_done = [step for step in range(1, 11) if tradeDetails.get(f"step{step}") == "done"]
        total_steps = 10
        step_status = "ALL STEP CHECKS: DONE" if len(steps_done) == total_steps else f"{len(steps_done)}/{total_steps}"
        date_time = datetime.fromtimestamp(tradeDetails['timestamp'])  # Convert to UTC datetime
        formatted_date = date_time.strftime('%Y-%m-%d %H:%M:%S')
        trade_message = (
            f"*Trade Details(Escrow)*\n"
            f"━━━━⍟𝗘𝘀𝗰𝗿𝗼𝘄 𝗦𝗵𝗶𝗲𝗹𝗱⍟━━━━\n\n"
            f"*Timestamp:* {formatted_date}\n"
            f"*Buyer:* {tradeDetails['buyer_username']} (`{tradeDetails['buyer']}`)\n"
            f"*Seller:* {tradeDetails['seller_username']} (`{tradeDetails['seller']}`)\n"
        )
        if tradeDetails['sellerAddress'] != '':
                trade_message += f"*Seller Address:* `{tradeDetails['sellerAddress']}`\n\n"
        if tradeDetails['brokerTrade']:
            trade_message += f"*Broker:* {tradeDetails['broker_username']} (`{tradeDetails['broker']}`)\n"
            
            if tradeDetails['brokerAddress'] != '':
                trade_message += f"*Broker Address:* `{tradeDetails['brokerAddress']}`\n\n"

        trade_message += f"*Amount:* {tradeDetails['tradeAmount']} {tradeDetails['currency']}\n"
        if tradeDetails['fee']>0:
            trade_message += f"*Escrow Fee:* {tradeDetails['fee']} {tradeDetails['currency']} ({tradeDetails['fee_percentage']*100}%)\n"
        if tradeDetails['brokerTrade']:
            trade_message += f"*Broker Fee:* {tradeDetails['broker_fee']} {tradeDetails['currency']} ({tradeDetails['broker_fee_percentage']*100}%)\n"
        trade_message += (
            f"*Status:* {tradeDetails['status']}\n"
            f"*Steps:* {step_status}\n\n"
            f"━━━━⍟𝗘𝘀𝗰𝗿𝗼𝘄 𝗦𝗵𝗶𝗲𝗹𝗱⍟━━━━\n\n"
            f"*Agreement:*\n{tradeDetails['tradeDetails']}"
        )
        
        update.message.reply_text(trade_message, parse_mode=ParseMode.MARKDOWN)
    elif selection.startswith("TXID"):
        txDetails = bot_state.get_tx_var(selection)
        if not txDetails:
            update.message.reply_text("Item not found")
            return
        date_time = datetime.fromtimestamp(txDetails['timestamp'])  # Convert to UTC datetime
        formatted_date = date_time.strftime('%Y-%m-%d %H:%M:%S')
        item_message = (
            f"*Item Details*\n"
            f"━━━━⍟𝗘𝘀𝗰𝗿𝗼𝘄 𝗦𝗵𝗶𝗲𝗹𝗱⍟━━━━\n\n"
            f"*Timestamp:* {formatted_date}\n"
            f"*Buyer:* {txDetails['buyer_username']} (`{txDetails['buyer']}`)\n"
            f"*Item ID:* `{txDetails['item_id']}`\n"
            f"*Amount:* {txDetails['itemAmount']}\n"
            f"*Price:* `{txDetails['tradeAmount']}` *{txDetails['currency']}*\n"
            f"*Escrow Address:* `{txDetails['ourAddress']}`\n\n"
            f"*Status:* {txDetails['status']}\n"
            f"━━━━⍟𝗘𝘀𝗰𝗿𝗼𝘄 𝗦𝗵𝗶𝗲𝗹𝗱⍟━━━━\n"
        )
        
        update.message.reply_text(item_message, parse_mode=ParseMode.MARKDOWN)
    elif selection.startswith("ITEM"):
        itemDetails = bot_state.get_item_details(selection)
        if not itemDetails or len(itemDetails)<=2:
            update.message.reply_text("Item not found")
            return
        item_message = (
            f"*Item Details*\n"
            f"━━━━⍟𝗘𝘀𝗰𝗿𝗼𝘄 𝗦𝗵𝗶𝗲𝗹𝗱⍟━━━━\n\n"
            f"*Title:* {itemDetails['title']}\n"
            f"*Description:* {itemDetails['description']}\n"
            f"*Type:* {itemDetails['type']}\n"
            f"*Seller:* {itemDetails['seller']}\n"
            f"*Stock:* {itemDetails['stock']}\n"
            f"*Locked Stock:* {itemDetails['lockedStock']}\n"
            f"*Buyable Stock:* {itemDetails['stock']-itemDetails['lockedStock']}\n"
            f"*Price:* `{itemDetails['price']}` *{itemDetails['currency']}*\n"
            f"*Seller Address:* `{itemDetails['sellerAddress']}`\n\n"
            f"*Tags:* {itemDetails['tags']}\n"
            f"━━━━⍟𝗘𝘀𝗰𝗿𝗼𝘄 𝗦𝗵𝗶𝗲𝗹𝗱⍟━━━━\n"
        )
        
        update.message.reply_text(item_message, parse_mode=ParseMode.MARKDOWN)
description = "Display Information about a trade or transaction"
aliases = ['/tradeinfo', '/ti']
enabled = False
hidden = True
OperaterCommand = False
