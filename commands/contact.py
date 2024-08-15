from telegram import Update
from telegram.ext import CallbackContext

def execute(update: Update, context: CallbackContext, bot_state) -> None:
    help_text = (
        "Remember we will never ask you to pay more to release your crypto nor we will ask for your wallet keys \n\nException: In a case if your telegram account gets suspended/deleted and your payment is stuck with us, we will ask you to verify that the funds belong to you by asking to initiate a transaction (will never be more than $0.002) from the wallet used to pay our escrow wallet\n\n\nContact ID: @addylad6725"
    )
    update.message.reply_text(help_text)

description = "Contact to Support"
aliases = ['/contact', '/scam', '/support', '/daddy']
enabled = False
hidden = True
OperaterCommand = False
