from telegram import Update
from telegram.ext import CallbackContext
import concurrent.futures


def execute(update: Update, context: CallbackContext, bot_state) -> None:
    tradeId = bot_state.getUserTrade(str(update.message.from_user.id))
    
    if(tradeId != ''):
        print(f'Canceling Escrow: {tradeId}')
        close_trade(bot_state, tradeId, "close[user_initiated]")
        update.message.reply_text(text=f"Aw well that's sad...\nHope to see you soon!!", reply_to_message_id=update.message.message_id)
    else:
        update.message.reply_text(text=f"You have no ongoing Escrow", reply_to_message_id=update.message.message_id)

def close_trade(bot_state, action_id: str, message: str, lockBypass=False):
    if action_id.startswith('TRADE'):
        tradeDetails = bot_state.get_var(action_id, lockBypass)
        tradeDetails["status"] = message
        with concurrent.futures.ThreadPoolExecutor() as executor:
            futures = [
                executor.submit(bot_state.set_var, action_id, tradeDetails, lockBypass),
                executor.submit(bot_state.setUserTrade, tradeDetails["buyer"], "", lockBypass),
                executor.submit(bot_state.setUserTrade, tradeDetails["seller"], "", lockBypass),
                executor.submit(bot_state.unlockUser, tradeDetails["buyer"], lockBypass),
                executor.submit(bot_state.unlockUser, tradeDetails["seller"], lockBypass),
                executor.submit(bot_state.unlockUser, tradeDetails["senderId"], lockBypass),
                executor.submit(bot_state.setUserTrade, tradeDetails["senderId"], "", lockBypass),
            ]
            concurrent.futures.wait(futures)
    elif action_id.startswith('TXID'):
        tx_details = bot_state.get_tx_var(action_id, lockBypass)
        tx_details["status"] = message
        item_details = bot_state.get_item_details(tx_details['item_id'], lockBypass)
        if message == 'close[delivered]' or message == 'close[success_after_intervention]':
            item_details['stock'] -= 1
            item_details['lockedStock'] -= 1
        elif message == 'close[success]':
            item_details['status'] = message
        else:
        #elif message in ['close[no_seller_response]', 'close[payment_timeout]', 'close[user_initiated]' , 'close[fail_after_intervention]']:
            item_details['lockedStock'] -= 1
        bot_state.remove_timer(tx_details['payment_timeout'], lockBypass)
        bot_state.add_item(tx_details['item_id'], item_details, lockBypass)
        bot_state.set_tx_var(action_id, tx_details, lockBypass)
    return True

description = "Cancels the current Trade going on"
aliases = ['/cancel']
enabled = True
hidden = True
OperaterCommand = False
