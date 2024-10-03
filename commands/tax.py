from telegram import Update
from telegram.ext import CallbackContext
from decimal import Decimal, ROUND_HALF_UP
from imports.utils import validate_text, is_number
def execute(update: Update, context: CallbackContext, bot_state) -> None:
    fee_percentage = '2'

    fee_percentage_inverse = Decimal(1-Decimal(Decimal(fee_percentage)/100))
    if len(context.args) <= 0:
        update.message.reply_text("Enter an amount\nEx: /tax 10")
        return
    user_input = context.args[0]
    if validate_text(input_text=user_input) != True:
        update.message.reply_text(validate_text(input_text=user_input))
        return
    input_amount = is_number(user_input)
    if not input_amount:
        update.message.reply_text(
            # reply_to_message_id=update.message.message_id,
            text=f"Please input a valid Amount"
        )
    final_amount =  ((Decimal(input_amount)/fee_percentage_inverse).quantize(Decimal('0.001'), rounding=ROUND_HALF_UP))+Decimal('0.001')

    update.message.reply_text(f'Actual Amount: {input_amount}\nFinal amount to be paid `{final_amount}`\nFee Rate: {fee_percentage}%', parse_mode='Markdown')

description = "Calculate fee to be included in amount being sent"
aliases = ['/tax', '/nirmala', '/fee']
enabled = False
hidden = True
OperaterCommand = False
