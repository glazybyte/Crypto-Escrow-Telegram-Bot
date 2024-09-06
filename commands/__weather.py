import requests
from telegram import Update
from telegram.ext import CallbackContext

def execute(update: Update, context: CallbackContext, bot_state) -> None:
    #Yours is bad.. move on
    pass
    

description = "Get weather information"
aliases = ['/weather']
enabled = False
hidden = True
OperaterCommand = False
