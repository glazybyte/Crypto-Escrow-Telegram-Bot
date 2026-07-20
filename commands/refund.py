from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ParseMode
from telegram.ext import CallbackContext
from decimal import Decimal, ROUND_HALF_UP
from imports.utils import validate_text, is_number
from globalState import GlobalState;
async def execute(update: Update, context: CallbackContext, bot_state: GlobalState) -> None:
    if len(context.args) <= 0:
        await update.message.reply_text("Enter an amount\nEx: /refund <trade_id>")
        return
    trade_id = context.args[0]
    trade_details = bot_state.get_var(trade_id)
    if trade_details is False:
        return await update.message.reply_text("Trade not found")
    
    keyboard = [
        [InlineKeyboardButton("LTC", callback_data='option_3')],
        [InlineKeyboardButton("SOL (Solana)", callback_data='option_11')],
        [InlineKeyboardButton("USDT (Solana)", callback_data='option_12')],
        [InlineKeyboardButton("BNB (BSC Bep-20)", callback_data='option_13')],
        [InlineKeyboardButton("USDT (BSC Bep-20)", callback_data='option_14')],
        [InlineKeyboardButton("DOGE", callback_data='option_15')],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    if trade_details['status'] != 'open':
        return await update.message.reply_text("Trade has Status other than Open Do u wanna proceed", reply_markup=reply_markup)

description = "Calculate fee to be included in amount being sent"
aliases = ['/refund']
enabled = False
hidden = True
OperaterCommand = False
