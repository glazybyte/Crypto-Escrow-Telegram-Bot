import os
from telegram import Update
from telegram.ext import CallbackContext
from datetime import datetime
from decimal import Decimal
import random

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
   
   item_details = {
       "title": "none",
       "description": "none",
       "type": "automatic",
       "seller": str(update.message.from_user.id),
       "stock": 0,
       "lockedStock": 0,
       "stockList": [], # at the of delivery it will be good to set up a lockStock Mechanism(before getting the data from databse, lock that item id first)
       "toggle": "disabled",
       "price": "0",
       "sellerAddress": "",
       "currency": "USDT (Solana)",
       "tags": 'none' # no use right now, for future if I add browse by category
   }
   itemId = "ITEM"+''.join([str(random.randint(0, 9)) for _ in range(12)])
   bot_state.add_item(itemId, item_details)
   update.message.reply_text("Enter Title, Description, Price(in USDT), Type('manual' or 'automatic' for delivery type) seperated by comma\nEx: My Item, this is description, 10, automatic")
   
   bot_state.set_waiting_for_input(update.message.from_user.id, itemId)

def handle_input(update: Update, context: CallbackContext, bot_state: GlobalState) -> None:
    """Handler to process user inputs"""
    chat_id = str(update.message.from_user.id)
    user_input = update.message.text
    # Check if the bot is waiting for input from this user
    waiting_for = bot_state.get_waiting_for_input_context(chat_id)
    if not waiting_for:
        return
    is_input_valid = validate_text(input_text=user_input, extra=['\n'])
    if is_input_valid != True:
        update.message.reply_text(is_input_valid)
        return
    # Retrieve Item details for the current chat
    item_details = bot_state.get_item_details(waiting_for)

    if(item_details['title'] == 'none'):
        user_input = user_input.split(',')
        if len(user_input) < 4 or len(user_input) > 4:
            update.message.reply_text("Enter Sufficient data\nEx: My Item, this is description, 10, automatic")
            return
        title, des, price, type = [x.strip() for x in user_input]
        numb = is_number(price)
        if not numb:
            update.message.reply_text("Invalid Input for Price")
            return
        elif numb > 30 and str(update.message.from_user.id) != os.getenv('BOT_OPERATER'):
            update.message.reply_text("Item cannot have limit above 30 USDT, contact @addylad6725 for such cases")
            return
        
        if title == 'none':
            update.message.reply_text("Title cannot be 'none'")
            return
        if type != 'automatic' and type != 'manual':
            update.message.reply_text("Invalid Type, this can either be 'manual' or 'automatic'")
            return
        item_details['title'], item_details['description'], item_details['price'], item_details['type'] = title, des, price, type
        bot_state.add_item(waiting_for, item_details)
        update.message.reply_text(f'Alrighty Right! Noted\nEnter your USDT(Solana) address to receive payment on')
        
    elif item_details['sellerAddress'] == '':
        if is_address_valid(user_input, 'SOL'):
            item_details['sellerAddress'] = user_input
            bot_state.add_item(waiting_for, item_details)
            msg = ''
            if item_details['type'] == 'automatic':
                msg = "You selected 'automatic' for delivery type, enter product codes or keys to deliver after payment.\nEx:\nkey1\nkey2\nkey3\nkey4\n (this will add 4 keys in stock)"
            if item_details['type'] == 'manual':
                msg = "You selected 'manual' for delivery type, enter amount of stock to list"
            update.message.reply_text(f'Alrighty Right! Noted\n{msg}')
        else:
            update.message.reply_text("Invalid USDT (Solana) Address")
            return
    elif(item_details['type'] == 'automatic'):
        bot_state.clear_waiting_for_input(chat_id)
        item_details['stockList'] = [line.strip() for line in user_input.splitlines() if line.strip()]
        item_details['stock'] = len(item_details['stockList'])
        item_details['toggle'] = 'enabled'
        bot_state.add_item(waiting_for, item_details)
        update.message.reply_text(f'Alrighty! your item has been added to your shop\nItem ID: {waiting_for}')
        return
    elif(item_details['type'] == 'manual'):
        bot_state.clear_waiting_for_input(chat_id)
        numb = is_number(user_input)
        if not numb:
            update.message.reply_text("Invalid Input for stock number")
            return
        elif numb > Decimal('100') and str(update.message.from_user.id) != os.getenv('BOT_OPERATER'):
            update.message.reply_text("Item cannot have stock above 100, contact @addylad6725 for such cases")
            return
        item_details['stock'] = numb
        item_details['toggle'] = 'enabled'
        bot_state.add_item(waiting_for, item_details)
        update.message.reply_text(f'Alrighty! your item has been added to your shop\nItem ID: {waiting_for}')
        return
        
        
        

    






description = "Add item to your Shop"
aliases = ['/listitem', '/li']
enabled = False
hidden = True
OperaterCommand = False


#dataBase Mind Plan
#Shop table which will have user and their shop information
#Item Table which will be serilized with id and info like item name, price in usdt, StockAmount, StockList, Type(automatic or manual by seller)
#ShopTransaction Table, Serilized by ID, ItemID, SpecificItem, SoldTO, SoldBy, Type(Manual or automatic, at the time of purchase)

#The amount will be released to 

#The problem is how to confirm if product was working right before Delivery
#sol1: Can display a warning that if the item is found to be a item which can be expired soon on such instance buyer will have upper hand
#Sol2: Add a feature for buyer side that first the item will be delivered to Bot Operator/Moderators for Inspection, and then he will
#   give the item to Buyer and release Payment to Seller


#Problem2 what if buyer Account gets deleted after Sending amount