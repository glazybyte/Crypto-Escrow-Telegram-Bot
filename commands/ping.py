from telegram import Update
from telegram.ext import CallbackContext
from datetime import datetime
from decimal import Decimal
def execute(update: Update, context: CallbackContext, bot_state) -> None:
    start_time = datetime.now()
    update.message.reply_text('Pong!')
    end_time = datetime.now()
    latency = (end_time - start_time).total_seconds()*1000
    update.message.reply_text(f'Ping: {latency:.0f} ms')

description = "Check ping for bot"
aliases = ['/ping']
enabled = False
hidden = True
OperaterCommand = False
