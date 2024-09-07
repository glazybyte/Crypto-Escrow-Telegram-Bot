from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ParseMode
from telegram.ext import CallbackContext

from globalState import GlobalState

def execute(update: Update, context: CallbackContext, bot_state: GlobalState) -> None:
    """Handler for the /help command."""
    keyboard = [
        [InlineKeyboardButton("Shop Commands", callback_data='option_24_1')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    help_text = (
        "━━━━⍟𝗘𝘀𝗰𝗿𝗼𝘄 𝗦𝗵𝗶𝗲𝗹𝗱⍟━━━━\n"
        "Here are some basic Commands:\n\n"
        "*/escrow* - Start a new escrow interaction\n\n"
        "*/cancel* - Cancel the current escrow session \n\n"
        "*/contact* - Contact Support\n\n"
        "*/shop* - Browse a user's Shop\n\n"
        "*/buy* - Buy an Item from a Shop\n\n"
        "*/id* - get your own ID or Shop ID\n\n"
        "*/fee* - Calculate amount to send after inclusion of fee\n\n"
        "*/info* - Know more about bot\n\n"
        "*/donate* - Feeling generous today?\n\n"
    )
    message = update.message.reply_text(help_text, parse_mode=ParseMode.MARKDOWN, reply_markup=reply_markup, reply_to_message_id=update.message.message_id)
    bot_state.set_waiting_for_input(update.message.from_user.id, [message], 'button')

def button(update: Update, context: CallbackContext, bot_state: GlobalState) -> None:
    query = update.callback_query
    bot_state.clear_waiting_for_input(str(query.from_user.id))
    if query.data == 'option_24_1':
        help_text = (
        "━━━━⍟𝗘𝘀𝗰𝗿𝗼𝘄 𝗦𝗵𝗶𝗲𝗹𝗱⍟━━━━\n"
        "Here are Commands to manage your shop:\n"
        "*/listitem* - Add a item to your shop\n"
        "Aliases: `/li` \n\n"
        "*/delistitem* - Remove item from shop\n"
        "Aliases: `/dl` \n\n"
        "*/edit* - Edit shop or Item\n"
        "Ussage: /edit <field> <item-id> <new-value>\n"
        "Fields: itemprice, itemdescription, itemtype, itemstock\nor\n"
        "Ussage: /edit <field> <new-value>\n"
        "Fields: shopname, shopdescription\n\n"
        "*/addstock* - Add stock for automatic delivery type item\n"
        "Aliases: `/as`\n\n"
    )
    query.message.edit_text(
        text=help_text,
        parse_mode=ParseMode.MARKDOWN
    )
    bot_state.clear_waiting_for_input(str(query.from_user.id))
description = "Display help to mere humans"
aliases = ['/help']
enabled = False
hidden = True
OperaterCommand = False
