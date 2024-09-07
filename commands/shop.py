from telegram import Update, ParseMode, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import CallbackContext
import math

from globalState import GlobalState
def execute(update: Update, context: CallbackContext, bot_state: GlobalState) -> None:
    user_input = ''
    if len(context.args)>0:
        user_input = context.args[0]
    else:
        user_input = str(update.message.from_user.id)
    if not user_input:
        update.message.reply_text("Ussage: `/shop <userid>`", parse_mode=ParseMode.MARKDOWN, reply_to_message_id=update.message.message_id)
        return
    user = bot_state.getUser(user_input)
    shop_name, shop_desc = user['shopName'], user['shopDesc']
    if user['shopName'] == 'none':
        shop_name = f"@{context.bot.get_chat(user_input).username}'s Shop"
    if user['shopDesc'] == 'none':
        shop_desc = ''

    reply_markup = InlineKeyboardMarkup([
        [InlineKeyboardButton("Browse", callback_data='option_22_1')],
    ])
    
    message = update.message.reply_text(
        text= f"*{shop_name}*\n{shop_desc}",
        parse_mode=ParseMode.MARKDOWN,
        reply_to_message_id=update.message.message_id,
        reply_markup=reply_markup
    )
    bot_state.set_waiting_for_input(str(update.message.from_user.id), [message,{"shop_owner": user_input}], 'button')
    
def button(update: Update, context: CallbackContext, bot_state: GlobalState):
    query = update.callback_query
    #message_id = query.message.message_id
    button_context = bot_state.get_waiting_for_input_context(str(query.from_user.id))
    target_message_id = query.message.message_id
    target_chat_id = query.message.chat_id
    user = bot_state.getUser(button_context['shop_owner'])
    shop_name, shop_desc = user['shopName'], user['shopDesc']
    if user['shopName'] == 'none':
        shop_name = f"@{context.bot.get_chat(button_context['shop_owner']).username}'s Shop"
    if user['shopDesc'] == 'none':
        shop_desc = ''
    page_numb_to_show = int(query.data.replace('option_22_',''))
    page_next = 'option_22_'+ str(page_numb_to_show+1)
    page_prev = 'option_22_'+ str(page_numb_to_show-1)
    
    if page_numb_to_show == 0:
        context.bot.edit_message_text(
            text= "Shop browsing closed",
            chat_id = target_chat_id,
            message_id=target_message_id
        )
        bot_state.clear_waiting_for_input(str(query.from_user.id))
        return
    bot_state.set_waiting_for_input(str(query.from_user.id), [query.message, {'shop_owner': button_context['shop_owner']}], 'button')
    seller_items = bot_state.get_seller_items(button_context['shop_owner'])
    page_limit = 5 # per page showcasing 5 items
    page_start = (page_numb_to_show-1)*page_limit
    page_stop = page_limit*page_numb_to_show
    if page_stop> len(seller_items):
        page_stop = len(seller_items)
    total_pages = len(seller_items)/page_limit
    if len(seller_items) % page_limit != 0:
        total_pages = math.floor(total_pages)+1
    if total_pages == 0:
        query.message.reply_text("This shop have no items.", parse_mode=ParseMode.MARKDOWN, reply_to_message_id=query.message.message_id)
        return
    msg = f"*{shop_name}*\npage: {page_numb_to_show}/{total_pages}\n"
    
    for item in seller_items[page_start:page_stop]:
        stock = item['stock']
        if stock == 0:
           stock = "Out of Stock"
        msg = msg+f"{item['title']}\n{item['description']}\n*Stock:* {stock}\n*Delivery Type:* {item['type']}\n*Item ID:* `{item['item_id']}`\n\n"
    keyboard = []
    if(page_numb_to_show+1)<=total_pages:
        keyboard.append([InlineKeyboardButton("Next", callback_data=page_next)])
    if page_numb_to_show-1 == 0:
        keyboard.append([InlineKeyboardButton("Close", callback_data=page_prev)])
    else:
        keyboard.append([InlineKeyboardButton("Back", callback_data=page_prev)])
    reply_markup = InlineKeyboardMarkup(keyboard)
    context.bot.edit_message_text(
        parse_mode=ParseMode.MARKDOWN,
        text = msg,
        chat_id = target_chat_id,
        reply_markup = reply_markup,
        message_id=target_message_id,
    )

description = "Browse shop of a user"
aliases = ['/shop', '/myshop']
enabled = False
hidden = True
OperaterCommand = False
