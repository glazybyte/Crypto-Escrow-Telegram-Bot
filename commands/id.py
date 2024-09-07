from telegram import Update, ParseMode
from telegram.ext import CallbackContext
from datetime import datetime
def execute(update: Update, context: CallbackContext, bot_state) -> None:
    if update.message.reply_to_message:
        quoted_message = update.message.reply_to_message
        update.message.reply_text(f'Quoted message sender\'s ID and shop ID: `{quoted_message.from_user.id}`', parse_mode=ParseMode.MARKDOWN)
    else:
        update.message.reply_text(f'Your userId and shop ID: `{update.message.from_user.id}`', parse_mode=ParseMode.MARKDOWN)

description = "Get User id of yourself or a message sender"
aliases = ['/id']
enabled = False
hidden = True
OperaterCommand = False
