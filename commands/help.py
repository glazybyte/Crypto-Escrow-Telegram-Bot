from telegram import Update
from telegram.ext import CallbackContext

def execute(update: Update, context: CallbackContext, bot_state) -> None:
    """Handler for the /help command."""
    help_text = (
        "Here are the available commands:\n\n"
        "/escrow - Starts a new escrow interaction\n\n"
        "/cancel - cancel the current escrow session \n\n"
        "/contact - Contact Support\n\n"
        "/info - know more about bot\n\n"
        "/donate - Feeling generous today?\n\n"
    )
    update.message.reply_text(help_text)

description = "Display help to mere humans"
aliases = ['/help']
enabled = False
hidden = True
OperaterCommand = False
