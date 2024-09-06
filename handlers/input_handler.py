from telegram import Update
from telegram.ext import CallbackContext
import importlib

from globalState import GlobalState
from imports.utils import *

def user_input(update: Update, context: CallbackContext, bot_state: GlobalState):
    if bot_state.get_waiting_for_input_type(update.message.from_user.id) != 'text':
        return
    cmd = bot_state.get_waiting_for_cmd(update.message.from_user.id)
    if not cmd:
        return
    module = importlib.import_module(cmd)
    module.handle_input(update, context, bot_state)