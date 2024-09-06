from telegram import Update, ParseMode
from telegram.ext import CallbackContext
from datetime import datetime
from decimal import Decimal

from globalState import GlobalState
from imports.utils import *
def execute(update: Update, context: CallbackContext, bot_state: GlobalState) -> None:
    user_input = context.args[0]
    item_details = bot_state.get_item_details(user_input)
    print(item_details)
    if len(item_details) < 2 or not item_details or item_details['toggle'] == 'disabled' :
        update.message.reply_text("Invalid Item ID")
        return
    if item_details['seller'] != str(update.message.from_user.id):
        update.message.reply_text("Another delusion of yours to add stock to someone else's item.")
        return
    if item_details['type'] == 'manual':
        update.message.reply_text(
            text=f"This item's delivery mode is `manual`, so you can edit stock mnumber instead.\nEx: `/edit itemstock {user_input} 69`",
            parse_mode=ParseMode.MARKDOWN
        )
        return
    bot_state.set_waiting_for_input(update.message.from_user.id, user_input)
    update.message.reply_text(f'Alrighty Right! \nEnter product codes or keys to deliver after payment.\nEx:\nkey1\nkey2\nkey3\nkey4\n(this will add 4 keys in stock)')
    
def handle_input(update: Update, context: CallbackContext, bot_state: GlobalState) -> None:
    chat_id = str(update.message.from_user.id)
    user_input = update.message.text.strip()
    # Check if the bot is waiting for input from this user
    waiting_for = bot_state.get_waiting_for_input_context(chat_id)
    if not waiting_for:
        return
    if validate_text(input_text=user_input, extra=['\n']) != True:
        update.message.reply_text(validate_text(input_text=user_input))
        return
    bot_state.clear_waiting_for_input(chat_id)
    item_details = bot_state.get_item_details(waiting_for)
    if item_details['seller'] != str(update.message.from_user.id): # Condition doesn't make sense but here we go
        return 
    item_details['stockList'] = item_details['stockList']+[line.strip() for line in user_input.splitlines() if line.strip()]
    item_details['stock'] = len(item_details['stockList'])
    update.message.reply_text(
        text=f"Stock for item with id `{waiting_for}` updated!",
        parse_mode=ParseMode.MARKDOWN
    )


description = "Add stock to item for delivery"
aliases = ['/addstock', '/as']
enabled = False
hidden = True
OperaterCommand = False
