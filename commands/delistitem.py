from telegram import Update, ParseMode
from telegram.ext import CallbackContext
from datetime import datetime
from decimal import Decimal

from globalState import GlobalState
def execute(update: Update, context: CallbackContext, bot_state: GlobalState) -> None:
    user_input = context.args[0]
    item_details = bot_state.get_item_details(user_input)
    if not item_details or item_details['toggle'] == 'disabled':
        update.message.reply_text("Invalid Item ID")
        return
    if item_details['seller'] != str(update.message.from_user.id):
        update.message.reply_text("Another delusion of yours to remove someone else's item.")
        return
    if item_details['lockedStock']>0: # Meaning someone buying it
        item_details['toggle'] = "disabled"
        bot_state.add_item(user_input, item_details)
        bot_state.add_timeout(2*24*60*60, user_input) #straight forward tx will be under 10 minutes(automatic) to 1 day(manual), but lets take 1 day margin
    else:
        bot_state.remove_item(user_input)
    update.message.reply_text(f"Item with id `{user_input}` removed!", parse_mode=ParseMode.MARKDOWN)

def timeout_up(context, bot, bot_state: GlobalState):
    item_details = bot_state.get_item_details(context)
    if not item_details or item_details['toggle'] == 'disabled':
        return
    bot_state.remove_item(context)
    

description = "Check ping for bot"
aliases = ['/delistitem', 'di']
enabled = False
hidden = True
OperaterCommand = False
