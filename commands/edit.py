from telegram import Update
from telegram.ext import CallbackContext
from decimal import Decimal
import os

from globalState import GlobalState
from imports.utils import *

def execute(update: Update, context: CallbackContext, bot_state: GlobalState) -> None:
    if update.message.from_user.id != update.message.chat_id:
        update.message.reply_text(
            text=f"This command is only for private messages"
        )
        return
    if bot_state.isUserLocked(str(update.message.from_user.id)):
        update.message.reply_text(
            text=f"You are currently locked"
        )
        return
    user_input = update.message.text.strip().split(' ', 3)
    if user_input[1].startswith('shop'):
        user_input = update.message.text.strip().split(' ', 2)
        if len(user_input) < 2:
            update.message.reply_text(
                "Usage: /edit <field> <item_id> <new_value>\n"
                "Fields: shopname, shopdescription, itemprice, itemdescription, itemtype, itemstock"
            )
            return
        edit_shop(user_input, update, context, bot_state)
    elif len(user_input) < 3:
        update.message.reply_text(
            "Usage: /edit <field> <item_id> <new_value>\n"
            "Fields: shopname, shopdescription, itemprice, itemdescription, itemtype, itemstock, itemwallet"
        )
        return
    else:
        edit_shop_item(user_input, update, context, bot_state)

def edit_shop(user_input, update: Update, context: CallbackContext, bot_state: GlobalState):
    user_details = bot_state.getUser(str(update.message.from_user.id))
    if not user_details:
        update.message.reply_text("User doesn't Exist")
        return
    field = user_input[1]
    new_value = user_input[2].strip()
    if field == 'shopname':
        if len(new_value) < 2:
            update.message.reply_text("Shop name must be greater than 2 characters.")
            return
        elif len(new_value) > 10:
            update.message.reply_text("Shop name cannot be more than 10 characters")
            return
        user_details['shopName'] = new_value
        update.message.reply_text(f"Your shop name has been successfully updated to: {new_value}")
    elif field == 'shopdescription':
        if len(new_value) < 2:
            update.message.reply_text("Shop description must be greater than 2 characters.")
            return
        elif len(new_value) > 100:
            update.message.reply_text("Shop description cannot be more than 100 characters")
            return
        user_details['shopDesc'] = new_value
        update.message.reply_text(f"Your shop description has been successfully updated.")
    else:
        update.message.reply_text("Invalid field. You can edit: shopname, shopdescription.")
        return
    bot_state.setUser(str(update.message.from_user.id), user_details)

def edit_shop_item(user_input, update: Update, context: CallbackContext, bot_state: GlobalState):
    field, item_id, new_value = user_input[1], user_input[2], user_input[3]
    item_details = bot_state.get_item_details(item_id)
    if item_details['seller'] != str(update.message.from_user.id):
        update.message.reply_text("Another delusion of yours to edit someone else's item.")
        return
    if len(item_details) < 2 or not item_details:
        update.message.reply_text(f"Item with ID {item_id} does not exist.")
        return
    if field == 'itemprice':
        numb = is_number(new_value)
        if not numb:
            update.message.reply_text("Invalid input for price.")
            return
        if numb < 2:
            update.message.reply_text("Price must be atleast 2 USDT")
            return
        elif numb > 30 and str(update.message.from_user.id) != os.getenv('BOT_OPERATER'):
            update.message.reply_text("Item cannot have price above 30 USDT, contact @addylad6725 for such cases.")
            return
        item_details['price'] = new_value
    elif field == 'itemdescription':
        if len(new_value) < 2:
            update.message.reply_text("Description must be greater than 2 characters.")
            return
        elif len(new_value) > 100:
            update.message.reply_text("Item Description cannot be more than 100 characters")
            return
        item_details['description'] = new_value
    elif field == 'itemtype':
        if new_value not in ['manual', 'automatic']:
            update.message.reply_text("Invalid item type. It should be either 'manual' or 'automatic'.")
            return
        item_details['type'] = new_value
    elif field == 'itemstock':
        if item_details['type'] != 'manual':
            update.message.reply_text("Cannot edit stock for automatic type items.")
            return
        numb = is_number(new_value)
        if not numb:
            update.message.reply_text("Invalid input for stock number.")
            return
        elif numb > Decimal('100') and str(update.message.from_user.id) != os.getenv('BOT_OPERATER'):
            update.message.reply_text("Item cannot have stock above 100, contact @addylad6725 for such cases.")
            return
        item_details['stock'] = numb
    elif field == 'itemwallet':
        selection=''
        if item_details["currency"] == 'LTC':
            selection = 'LTC'
        if item_details["currency"] == 'SOL (Solana)' or item_details["currency"] == 'USDT (Solana)':
            selection = 'SOL'
        if item_details["currency"] == 'BNB (BSC Bep-20)' or item_details["currency"] == 'USDT (BSC Bep-20)':
            selection = 'BSC'
        if item_details["currency"] == 'DOGE':
            selection = 'DOGE'
        if not is_address_valid(user_input, selection):
            update.message.reply_text(f"That's a invalid ${item_details['currency']} address")
            return
        item_details['sellerAddress'] = new_value
    else:
        update.message.reply_text("Invalid field. You can edit: itemprice, itemdescription, itemtype, itemstock.")
        return
    bot_state.add_item(item_id, item_details)
    update.message.reply_text(f"Item {item_id} has been successfully updated!")

description = "Edit item details in your shop"
aliases = ['/edit']
enabled = False
hidden = True
OperaterCommand = False
