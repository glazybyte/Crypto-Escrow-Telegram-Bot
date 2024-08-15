from telegram import Update
from telegram.ext import CallbackContext

def execute(update: Update, context: CallbackContext, bot_state) -> None:
    help_text = (
        "This bot acts as middle-man for your trade by holding the agreed amount in our wallet, upon succesful delivery & confirmation by buyer, bot will release funds automatically\n\nOfcourse in an event where buyer denies to release funds, we will check delivery and working proof by seller and release the payment manually \n\nCurrently accepted payments are LTC, USDT, SOL, DOGE.\nThere is NO escrow fee for LTC & SOL and merely 2 percent fee for USDT"
    )
    update.message.reply_text(help_text)

description = "Information about Bot"
aliases = ['/info']
enabled = False
hidden = True
OperaterCommand = False
