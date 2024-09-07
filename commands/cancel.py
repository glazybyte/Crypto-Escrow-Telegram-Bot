from telegram import Update
from telegram.ext import CallbackContext
import concurrent.futures


def execute(update: Update, context: CallbackContext, bot_state) -> None:
    tradeId = bot_state.getUserTrade(str(update.message.from_user.id))
    print(tradeId)
    if(tradeId != ''):
        close_trade(bot_state, tradeId, "close[user_initiated]")
        update.message.reply_text(text=f"Aw well that's sad...\nHope to see you soon!!", reply_to_message_id=update.message.message_id)
    else:
        update.message.reply_text(text=f"You have no ongoing Escrow", reply_to_message_id=update.message.message_id)

def close_trade(bot_state, action_id: str, message: str):
    if action_id.startswith('TRADE'):
        tradeDetails = bot_state.get_var(action_id)
        tradeDetails["status"] = message
        with concurrent.futures.ThreadPoolExecutor() as executor:
            futures = [
                executor.submit(bot_state.set_var, action_id, tradeDetails), 
                executor.submit(bot_state.setUserTrade, tradeDetails["buyer"], ""), 
                executor.submit(bot_state.setUserTrade, tradeDetails["seller"], ""),
                executor.submit(bot_state.unlockUser, tradeDetails["buyer"]), 
                executor.submit(bot_state.unlockUser, tradeDetails["seller"]), 
                executor.submit(bot_state.unlockUser, tradeDetails["senderId"]),
                executor.submit(bot_state.setUserTrade, tradeDetails["senderId"], ""),
            ]
            concurrent.futures.wait(futures)
    elif action_id.startswith('TXID'):
        tx_details = bot_state.get_tx_var(action_id)
        tx_details["status"] = message
        item_details = bot_state.get_item_details(tx_details['item_id'])
        if message == 'close[delivered]' or message == 'close[success_after_intervention]':
            item_details['stock'] -= 1
            item_details['lockedStock'] -= 1
        elif message == 'close[success]':
            item_details['status'] = message
        else:
        #elif message in ['close[no_seller_response]', 'close[payment_timeout]', 'close[user_initiated]' , 'close[fail_after_intervention]']:
            item_details['lockedStock'] -= 1
        bot_state.remove_timer(tx_details['payment_timeout'])
        bot_state.add_item(tx_details['item_id'], item_details)
        bot_state.set_tx_var(action_id, tx_details)
    return True

description = "Cancels the current Trade going on"
aliases = ['/cancel']
enabled = True
hidden = True
OperaterCommand = False
