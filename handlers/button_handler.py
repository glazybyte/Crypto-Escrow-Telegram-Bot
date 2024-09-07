from telegram import Update
from telegram.ext import CallbackContext
import importlib

from globalState import GlobalState
from imports.utils import *

def button_click(update: Update, context: CallbackContext, bot_state: GlobalState):
    user_id = str(update.callback_query.from_user.id)
    button_context = bot_state.get_waiting_for_input_context(user_id)
    if bot_state.get_waiting_for_input_type(user_id) != 'button' or update.callback_query.message.message_id != button_context['message_id'] or update.callback_query.message.chat_id != button_context['chat_id']:
        update.callback_query.answer()
 
        return
    cmd = bot_state.get_waiting_for_cmd(user_id)
    #bot_state.clear_waiting_for_input(user_id)
    if not cmd:
        return
    module = importlib.import_module(cmd)
    module.button(update, context, bot_state)