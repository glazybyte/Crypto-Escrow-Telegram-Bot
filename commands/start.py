from telegram import Update
from telegram.ext import CallbackContext

def execute(update: Update, context: CallbackContext, bot_state) -> None:
    update.message.reply_text("Welcome! Time for a escrow? \ntype /escrow for quick pompt for escrow \n/info to know about bot")

description = "Starts the bot"
aliases = ['/start']
enabled = True
hidden = True
OperaterCommand = False
