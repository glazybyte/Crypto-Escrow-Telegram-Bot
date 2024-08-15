from telegram import Update
from telegram.ext import CallbackContext

def execute(update: Update, context: CallbackContext, bot_state) -> None:
    tradeId = bot_state.getUserTrade(str(update.message.from_user.id))
    if(tradeId != ''):
        from commands.escrow import close_trade
        close_trade(bot_state, tradeId, "close[user_initiated]")
        update.message.reply_text(text=f"Aw well that's sad...\nHope to see you soon!!", reply_to_message_id=update.message.message_id)
    else:
        update.message.reply_text(text=f"You have no ongoing Escrow", reply_to_message_id=update.message.message_id)
description = "Cancels the current Escrow going on"
aliases = ['/cancel']
enabled = True
hidden = True
OperaterCommand = False
