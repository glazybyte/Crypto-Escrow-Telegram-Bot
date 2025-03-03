from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ParseMode
from telegram.ext import CallbackContext
import time
import random

from globalState import GlobalState
from imports.utils import *
from imports.wallet_utils import *
from commands.cancel import close_trade
from decimal import Decimal, ROUND_HALF_UP

def execute(update: Update, context: CallbackContext, bot_state: GlobalState) -> None:
    if update.message.from_user.id != update.message.chat_id:
        update.message.reply_text(
            text=f"This command is only for private messages"
        )
        return
    if bot_state.isUserLocked(str(update.message.from_user.id)):
        update.message.reply_text(
            text=f"You are currently locked due to your ongoing trade"
        )
        return
    elif bot_state.getUserTrade(str(update.message.from_user.id)) != '':
        bot_state.lockUser(str(update.message.from_user.id))
        update.message.reply_text(
            text=f"You are currently locked due to your ongoing trade"
        )
        return
    else:
        bot_state.lockUser(str(update.message.from_user.id))
    
    tradeDetails = {
        "seller" : '',
        "buyer" : '',
        "broker" : '',
        "brokerTrade": False,
        "seller_username" : '',
        "buyer_username" : '',
        "broker_username" : '',
        "timestamp": int(time.time()),
        "tradeDetails" : '',
        "currency" : '',
        "tradeAmount" : '',
        "sellerAddress": "",
        "brokerAddress": "",
        "ourAddress": "",
        "internalId" : '',
        "senderId": str(update.message.from_user.id),
        "fee": 0,
        "fee_percentage": 0,
        "broker_fee": 0,
        "broker_fee_percentage": 0,
        "step1": "",
        "step2": "",
        "step3": "",
        "step4": "",
        "step5": "",
        "step6": "",
        "step7": "",
        "step8": "",
        "step9": "",
        "step10": "",
        "sellerApproval": "",
        "sellerApprovalId": "",
        "buyerApproval": "",
        "buyerApprovalId": "",
        "status": "open" #close[completed], close[input_error], close[user_cancel], close[unsent_message]
    }

    message_id = update.message.message_id
    keyboard = [
        [InlineKeyboardButton("Seller", callback_data='option_1')],
        [InlineKeyboardButton("Buyer", callback_data='option_2')],
        [InlineKeyboardButton("Broker", callback_data='option_25')],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    tradeId = "TRADE"+''.join([str(random.randint(0, 9)) for _ in range(12)])
    multi_task(
        [
            [bot_state.set_var, tradeId, tradeDetails],
            [bot_state.setUserTrade, str(update.message.from_user.id), tradeId],
        ]
    )
    
    message = update.message.reply_text(
        text=f"━━━━⍟𝗘𝘀𝗰𝗿𝗼𝘄 𝗦𝗵𝗶𝗲𝗹𝗱⍟━━━━\nAlrighty Right! Its time for a trade \n\n Your role??", 
        reply_to_message_id=message_id,
        reply_markup=reply_markup
    )
    bot_state.set_waiting_for_input(str(update.message.from_user.id), [message, {"step": "rolecollect"}], 'button')

def button(update: Update, context: CallbackContext, bot_state: GlobalState) -> None:
    """Callback for handling button clicks."""
    query = update.callback_query

    tradeId = bot_state.getUserTrade(str(query.from_user.id))
    tradeDetails = bot_state.get_var(tradeId)
    
    if tradeDetails['status'] not in ['open', 'open[paid]']:
        return
    #global_dict[query.message.message_id] = 
    if(tradeDetails["step1"] != "done"):        
        tradeDetails["step1"] = "done"
        selected = ""
        if query.data == 'option_1':
            tradeDetails["seller"] = tradeDetails["senderId"]
            tradeDetails['seller_username'] = context.bot.get_chat(tradeDetails["senderId"]).username if context.bot.get_chat(tradeDetails["senderId"]).username else context.bot.get_chat(tradeDetails["senderId"]).full_name
            selected = "seller"
        elif query.data == 'option_2':
            tradeDetails["buyer"] = tradeDetails["senderId"]
            tradeDetails['buyer_username'] = context.bot.get_chat(tradeDetails["senderId"]).username if context.bot.get_chat(tradeDetails["senderId"]).username else context.bot.get_chat(tradeDetails["senderId"]).full_name
            selected = "buyer"
        elif query.data == 'option_25':
            tradeDetails["broker"] = tradeDetails["senderId"]
            tradeDetails['broker_username'] = context.bot.get_chat(tradeDetails["senderId"]).username if context.bot.get_chat(tradeDetails["senderId"]).username else context.bot.get_chat(tradeDetails["senderId"]).full_name
            tradeDetails["brokerTrade"] = True
            bot_state.set_var(tradeId, tradeDetails)
            try:
                query.edit_message_text(text="━━━━⍟𝗘𝘀𝗰𝗿𝗼𝘄 𝗦𝗵𝗶𝗲𝗹𝗱⍟━━━━\nAlright, you're the Broker.\n\nSend the ID of the Seller:")
            except:
                pass
            bot_state.set_waiting_for_input(str(query.from_user.id), "seller_id")
            return
        else:
            return
        
        if selected == "seller":
            bot_state.set_var(tradeId, tradeDetails)
            try:
                query.edit_message_text(text="━━━━⍟𝗘𝘀𝗰𝗿𝗼𝘄 𝗦𝗵𝗶𝗲𝗹𝗱⍟━━━━\nAlright, you're the Seller.\n\nSend the ID of the Buyer:")
            except:
                pass
            bot_state.set_waiting_for_input(str(query.from_user.id), "buyer_id")
        elif selected == "buyer":
            bot_state.set_var(tradeId, tradeDetails)
            try:
                query.edit_message_text(text="━━━━⍟𝗘𝘀𝗰𝗿𝗼𝘄 𝗦𝗵𝗶𝗲𝗹𝗱⍟━━━━\nAlright, you're the Buyer.\n\nSend the ID of the Seller:")
            except:
                pass
            bot_state.set_waiting_for_input(str(query.from_user.id), "seller_id")
        return
    elif tradeDetails["step4"] != "done":
        selected = ""
        if query.data == 'option_3':
            tradeDetails["currency"] = 'LTC'
            selected = "LTC"
        elif query.data == 'option_11':
            tradeDetails["currency"] = 'SOL (Solana)'
            selected = "SOL (Solana)"
        elif query.data == 'option_12':
            tradeDetails["currency"] = 'USDT (Solana)'
            selected = "USDT (Solana)"
        elif query.data == 'option_13':
            tradeDetails["currency"] = 'BNB (BSC Bep-20)'
            selected = "BNB (BSC Bep-20)"
        elif query.data == 'option_14':
            tradeDetails["currency"] = 'USDT (BSC Bep-20)'
            selected = "USDT (BSC Bep-20)"
        elif query.data == 'option_15':
            tradeDetails["currency"] = 'DOGE'
            selected = "DOGE"
        else:
            return
        tradeDetails["step4"] = "done"
        if tradeDetails['currency'] in ['USDT (Solana)', 'USDT (BSC Bep-20)']:
            tradeDetails['fee_percentage'] = Decimal(bot_state.config['usdt_fee_percentage'])/100
        else:
            tradeDetails['fee_percentage'] = Decimal(bot_state.config['fee_percentage'])/100
        tradeDetails['fee_percentage'] = str(tradeDetails['fee_percentage'])
        multi_task(
            [
                [bot_state.set_var, tradeId, tradeDetails],
                [bot_state.set_waiting_for_input, str(query.from_user.id), "tradeAmount", 'text', 'commands.escrow'],
            ]
        )
        try:
            query.edit_message_text(text=f"━━━━⍟𝗘𝘀𝗰𝗿𝗼𝘄 𝗦𝗵𝗶𝗲𝗹𝗱⍟━━━━\nAlrighty Right, Selected Crypto is {tradeDetails['currency']}.\nFee: *{str(Decimal(tradeDetails['fee_percentage'])*100)}%* \n\nEnter the amount of {tradeDetails['currency']} for trade:", parse_mode=ParseMode.MARKDOWN)
        except:
            pass
        return
    elif(tradeDetails["step6"] != "done"):
        if(tradeDetails["seller"] == str(query.from_user.id)):
            if(tradeDetails["sellerApproval"] != True):
                if query.data == 'option_4':
                    tradeDetails["sellerApproval"] = True
                    bot_state.set_var(tradeId, tradeDetails)
                    context.bot.send_message(chat_id=tradeDetails["seller"], text=f"Alrighty Right! You have accepted the Trade, we are now waiting for other party's approval")
                    if tradeDetails['brokerTrade']:
                        context.bot.send_message(chat_id=tradeDetails["broker"], text=f"Seller has accepted the trade")
    
                elif query.data == 'option_5':
                    tradeDetails["sellerApproval"] = False
                    tradeDetails["buyerApproval"] = False
                    bot_state.set_var(tradeId, tradeDetails)
                    close_trade(bot_state, tradeId, "close[user_declined]")
                    context.bot.send_message(chat_id=tradeDetails["seller"], text=f"Oh that's a bummer...\n Hope to see you again soon!")
                    context.bot.send_message(chat_id=tradeDetails["buyer"], text=f"Other Party Declined the trade, Trade has been canceled")
                    if tradeDetails['brokerTrade']:
                        context.bot.send_message(chat_id=tradeDetails["broker"], text=f"Seller has denied the trade")
                    query.answer()
                    return
                else:
                    return
        elif(tradeDetails["buyer"] == str(query.from_user.id)):
            
            if(tradeDetails["buyerApproval"] != True):
                if query.data == 'option_6':
                    tradeDetails["buyerApproval"] = True
                    bot_state.set_var(tradeId, tradeDetails)
                    context.bot.send_message(chat_id=tradeDetails["buyer"], text=f"━━━━⍟𝗘𝘀𝗰𝗿𝗼𝘄 𝗦𝗵𝗶𝗲𝗹𝗱⍟━━━━\nAlrighty Right! You have accepted the Trade, we are now waiting for other party's approval")
                    if tradeDetails['brokerTrade']:
                        context.bot.send_message(chat_id=tradeDetails["broker"], text=f"Buyer has accepted the trade")
                    query.answer()
                elif query.data == 'option_7':
                    tradeDetails["buyerApproval"] = False
                    multi_task(
                        [
                            [bot_state.set_var, tradeId, tradeDetails],
                            [close_trade, bot_state, tradeId, "close[user_declined]"],
                            [context.bot.send_message, {
                                'chat_id':tradeDetails["buyer"],
                                'text':f"Oh that's a bummer...\n Hope to see you again soon!"
                            }],
                            [context.bot.send_message, {
                                'chat_id':tradeDetails["seller"],
                                'text':f"Other Party Declined the trade, Trade has been canceled"
                            }]
                        ]
                    )
                    if tradeDetails['brokerTrade']:
                        context.bot.send_message(chat_id=tradeDetails["broker"], text=f"buyer has denied the trade")
                    query.answer()
                    return
        if(tradeDetails["buyerApproval"] == True and tradeDetails["sellerApproval"] == True):
            #Notify both of them
            tradeDetails["step6"] = "done"
            part = ''
            if tradeDetails['brokerTrade']:
                part = " & broker"
            [message1, message2, temp, temp1] = multi_task(
                [
                    [context.bot.send_message, {
                        'chat_id':tradeDetails["buyer"],
                        'text':f"━━━━⍟𝗘𝘀𝗰𝗿𝗼𝘄 𝗦𝗵𝗶𝗲𝗹𝗱⍟━━━━\nAlrighty Right! Both parties have accepted the trade \nWaiting for seller{part} to enter their {tradeDetails['currency']} wallet address"
                    }],
                    [context.bot.send_message, {
                        'chat_id':tradeDetails["seller"],
                        'text':f"━━━━⍟𝗘𝘀𝗰𝗿𝗼𝘄 𝗦𝗵𝗶𝗲𝗹𝗱⍟━━━━\nAlrighty Right! Both parties have accepted the trade\nSince you're the seller enter your {tradeDetails['currency']} address to receive the funds on after trade"
                    }],
                    [bot_state.set_waiting_for_input, tradeDetails["seller"], "seller_address", 'text', 'commands.escrow'],
                    [bot_state.set_var, tradeId, tradeDetails]
                ]
            )
            if tradeDetails['brokerTrade']:
                bot_state.set_waiting_for_input(tradeDetails["broker"], "broker_address", 'text', 'commands.escrow')
                context.bot.send_message(chat_id= tradeDetails["broker"],text= f"━━━━⍟𝗘𝘀𝗰𝗿𝗼𝘄 𝗦𝗵𝗶𝗲𝗹𝗱⍟━━━━\nAlrighty Right! Both parties have accepted the trade\nSince you're the broker enter your {tradeDetails['currency']} address to receive the funds on after trade")
            if message1 and message2 :
                """All Good no function needed here"""
            else:
                context.bot.send_message(chat_id=tradeDetails["seller"], text=f"Couldnt message the other person, make sure they have ran /start atleast once")
                context.bot.send_message(chat_id=tradeDetails["buyer"], text=f"Couldnt message the other person, make sure they have ran /start atleast once")
                if tradeDetails['brokerTrade']:
                    context.bot.send_message(chat_id=tradeDetails["broker"], text=f"Couldnt message the other person, make sure they have ran /start atleast once")
                bot_state.set_var(tradeId, tradeDetails)
                close_trade(bot_state, tradeId, "close[couldnt_message]")
                query.answer()
                return
        query.answer()
    elif(tradeDetails["step8"] != "done"):
        if(str(query.from_user.id) == tradeDetails["buyer"] and query.data == 'option_8'):
            tradeDetails["step8"] = "done"
            
            multi_task(
                [
                    [context.bot.send_message, {
                        'chat_id':tradeDetails["buyer"],
                        'text':f"━━━━⍟𝗘𝘀𝗰𝗿𝗼𝘄 𝗦𝗵𝗶𝗲𝗹𝗱⍟━━━━\nAlrighty Right! We will check your payment status every minute now until we receive it, once confirmed in Blockchain, we will notify you and seller"
                    }],
                    [context.bot.send_message, {
                        'chat_id':tradeDetails["seller"],
                        'text':f"━━━━⍟𝗘𝘀𝗰𝗿𝗼𝘄 𝗦𝗵𝗶𝗲𝗹𝗱⍟━━━━\nBuyer says to have sent the payment, we are yet to confirm it in blockchain, we will notify when we confirm in blockchain \n\n NOTE: *DO NOT* send the item/product YET"
                    }],
                    [bot_state.add_address_to_check_queue, tradeDetails["ourAddress"], tradeId,  tradeDetails["currency"]],
                    [bot_state.set_var, tradeId, tradeDetails]
                ]
            )
            if tradeDetails['brokerTrade']:
                context.bot.send_message(chat_id=tradeDetails["broker"], text=f"━━━━⍟𝗘𝘀𝗰𝗿𝗼𝘄 𝗦𝗵𝗶𝗲𝗹𝗱⍟━━━━\nBuyer says to have sent the payment, we are yet to confirm it in blockchain, we will notify when we confirm in blockchain")
            query.answer()      
    elif(tradeDetails["step9"] != "done"):
        if(str(query.from_user.id) == tradeDetails["seller"] and query.data == 'option_9'):
            tradeDetails["step9"] = "done"
            context.bot.send_message(chat_id=tradeDetails["seller"], text="━━━━⍟𝗘𝘀𝗰𝗿𝗼𝘄 𝗦𝗵𝗶𝗲𝗹𝗱⍟━━━━\nAlrighty right! Asking buyer for confirmation")
            if tradeDetails['brokerTrade']:
                context.bot.send_message(chat_id=tradeDetails["broker"], text="━━━━⍟𝗘𝘀𝗰𝗿𝗼𝘄 𝗦𝗵𝗶𝗲𝗹𝗱⍟━━━━\nSeller says to have sent the product, we are waiting for buyer to confirm it")
            keyboard = [
                [InlineKeyboardButton("I Confirm", callback_data='option_10')]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            message = context.bot.send_message(chat_id=tradeDetails["buyer"], 
                text="━━━━⍟𝗘𝘀𝗰𝗿𝗼𝘄 𝗦𝗵𝗶𝗲𝗹𝗱⍟━━━━\nThe Seller says to have sent you the product. \n\n Click the button below to confirm the product is working. \n\n When you click this button we will release the payment to the seller",
                reply_markup=reply_markup
            )
            bot_state.set_waiting_for_input(tradeDetails["buyer"], [message], 'button')
            bot_state.set_var(tradeId, tradeDetails)
            return
    elif(tradeDetails["step10"] != "done"):
        if(str(query.from_user.id) == tradeDetails["buyer"] and query.data == 'option_10'):
            tradeDetails["step10"] = "done"
            context.bot.send_message(chat_id=tradeDetails["buyer"], text="Alrighty Right! Releasing Payment to seller \n\nDont forget to recommend our services to your friends!!")
            tradeDetails["status"] = "close[completed]"
            context.bot.send_message(
                chat_id=tradeDetails["seller"], 
                text="━━━━⍟𝗘𝘀𝗰𝗿𝗼𝘄 𝗦𝗵𝗶𝗲𝗹𝗱⍟━━━━\nBuyer has confirmed the product, we have now released your payment as per the trade contract, time taken is decided by crypto network. \n\nLiked our services? consider donating a portion to help us keep running this!"
            )
            if tradeDetails['brokerTrade']:
                context.bot.send_message(
                    chat_id=tradeDetails["broker"], 
                    text="━━━━⍟𝗘𝘀𝗰𝗿𝗼𝘄 𝗦𝗵𝗶𝗲𝗹𝗱⍟━━━━\nBuyer has confirmed the product, we have now released your payment as per the trade contract, time taken is decided by crypto network. \n\nLiked our services? consider donating a portion to help us keep running this!"
                )
            bot_state.set_var(tradeId, tradeDetails)
            close_trade(bot_state, tradeId, "close[completed]")
            sendtrans(bot_state, tradeId)
  
def handle_input(update: Update, context: CallbackContext, bot_state: GlobalState) -> None:
    """Handler to process user inputs"""
    chat_id = str(update.message.from_user.id)
    user_input = update.message.text
    # Check if the bot is waiting for input from this user
    waiting_for = bot_state.get_waiting_for_input_context(chat_id)
    if not waiting_for:
        return
    if validate_text(input_text=user_input) != True:
        update.message.reply_text(validate_text(input_text=user_input))
        return
    # Retrieve trade details for the current chat
    tradeId = bot_state.getUserTrade(str(update.message.from_user.id))
    tradeDetails = bot_state.get_var(tradeId)
    if tradeDetails['status'] != 'open':
        return
    if tradeDetails["step2"] != "done":
        
        message = ""
        user_id = is_valid_user(user_input, context=context)
        if not user_id:
            message = update.message.reply_text(f"Not a valid user tch. Make sure they have ran /start atleast once on the bot.")
            return
        else:
            user_input = str(user_id)
        if user_input == tradeDetails['senderId']:
            update.message.reply_text(f"Ah! Another delusion of yours to have trade with yourself... tch")
            return
       
        if waiting_for == "buyer_id":
            if user_input == tradeDetails['seller']:
                update.message.reply_text(f"Ah! Another delusion of yours to have trade with 2 \"same\" people... tch")
                return
            # Store the buyer ID
            tradeDetails["buyer"] = user_input
            tradeDetails['buyer_username'] = context.bot.get_chat(user_input).username if context.bot.get_chat(user_input).username else context.bot.get_chat(user_input).full_name
            message= update.message.reply_text(f"Buyer ID '{user_input}' received. Proceeding with the trade...")
            bot_state.clear_waiting_for_input(chat_id)
            tradeDetails["step2"] = "done"
            bot_state.set_var(tradeId, tradeDetails)
        elif waiting_for == "seller_id":
            # Store the seller ID
            tradeDetails["seller"] = user_input
            tradeDetails['seller_username'] = context.bot.get_chat(user_input).username if context.bot.get_chat(user_input).username else context.bot.get_chat(user_input).full_name
            message = update.message.reply_text(f"Seller ID '{user_input}' received. Proceeding with the trade...")
            if not tradeDetails["brokerTrade"]:
                tradeDetails["step2"] = "done"
                bot_state.set_var(tradeId, tradeDetails)
            else:
                bot_state.set_waiting_for_input(str(update.message.from_user.id), "buyer_id")
                bot_state.set_var(tradeId, tradeDetails)
                try:
                    context.bot.edit_message_text(
                        chat_id=message.chat_id,
                        message_id=message.message_id,
                        #reply_to_message_id=update.message.message_id,
                        text="━━━━⍟𝗘𝘀𝗰𝗿𝗼𝘄 𝗦𝗵𝗶𝗲𝗹𝗱⍟━━━━\nAlright. Send the ID of the Buyer:"
                    )
                except:
                    pass
                return
            bot_state.clear_waiting_for_input(chat_id)
        time.sleep(2)
        try:
            context.bot.edit_message_text(
                chat_id=message.chat_id,
                message_id=message.message_id,
                #reply_to_message_id=update.message.message_id,
                text="━━━━⍟𝗘𝘀𝗰𝗿𝗼𝘄 𝗦𝗵𝗶𝗲𝗹𝗱⍟━━━━\nExplain the trade in detail.\n(This is crucial if something goes wrong and manual intervention is needed.)"
            )
        except:
            pass
        bot_state.set_waiting_for_input(str(update.message.from_user.id), "tradeDetails")
        # Update trade details
        
        return
    if tradeDetails["step3"] != "done":
        if len(user_input)>400:
            update.message.reply_text(
                #reply_to_message_id=update.message.message_id,
                text=f"Only 400 Characters allowed")
            return
        tradeDetails["step3"] = "done"
        if waiting_for == "tradeDetails":
            tradeDetails["tradeDetails"] = user_input
            message = update.message.reply_text(
                reply_to_message_id=update.message.message_id,
                text=f"Alrighty right noted. Proceeding with the trade...")
            bot_state.clear_waiting_for_input(chat_id)
            time.sleep(0.5)

            keyboard = [
                [InlineKeyboardButton("LTC", callback_data='option_3')],
                [InlineKeyboardButton("SOL (Solana)", callback_data='option_11')],
                [InlineKeyboardButton("USDT (Solana)", callback_data='option_12')],
                [InlineKeyboardButton("BNB (BSC Bep-20)", callback_data='option_13')],
                [InlineKeyboardButton("USDT (BSC Bep-20)", callback_data='option_14')],
                # [InlineKeyboardButton("DOGE", callback_data='option_15')],
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            try:
                context.bot.edit_message_text(
                chat_id=message.chat_id,
                message_id=message.message_id,
                #reply_to_message_id=update.message.message_id,
                text="━━━━⍟𝗘𝘀𝗰𝗿𝗼𝘄 𝗦𝗵𝗶𝗲𝗹𝗱⍟━━━━\nSelect the Crypto for trade to be made on",
                reply_markup=reply_markup
                )
            except:
                pass
            bot_state.set_waiting_for_input(str(update.message.from_user.id), [message], 'button')
            bot_state.set_var(tradeId, tradeDetails)
            return
    if tradeDetails["step5"] != "done":
        if waiting_for == "tradeAmount":
            text = is_number(user_input.replace(",", ""))
            if not text:
                update.message.reply_text(
                    # reply_to_message_id=update.message.message_id,
                    text=f"Please input a valid amount"
                )
                return
            if tradeDetails["currency"] == "USDT (Solana)" or tradeDetails["currency"] == "USDT (BSC Bep-20)":
                if text<Decimal('2'):
                    update.message.reply_text(
                    #reply_to_message_id=update.message.message_id,
                        text=f"minimum amount for {tradeDetails['currency']} is $2"
                    )
                    return
            elif tradeDetails["currency"] == "SOL (Solana)" and text<Decimal('0.02'):  # Change to only higher of this, never lower
                update.message.reply_text(
                    #reply_to_message_id=update.message.message_id,
                    text=f"minimum amount for {tradeDetails['currency']} is 0.02"
                )
                return
            elif tradeDetails["currency"] == "BNB (BSC Bep-20)" and text<Decimal('0.005'):  # Change to only higher of this, never lower
                update.message.reply_text(
                    #reply_to_message_id=update.message.message_id,
                    text=f"minimum amount for {tradeDetails['currency']} is 0.005"
                )
                return
            elif tradeDetails["currency"] == "LTC" and text<Decimal('0.025'):
                update.message.reply_text(
                    #reply_to_message_id=update.message.message_id,
                    text=f"minimum amount for {tradeDetails['currency']} is 0.025"
                )
                return
            elif tradeDetails["currency"] == "DOGE" and text<1:
                update.message.reply_text(
                    #reply_to_message_id=update.message.message_id,
                    text=f"minimum amount for {tradeDetails['currency']} is 1"
                )
                return
            
            
            tradeDetails["tradeAmount"] = user_input.replace(",", "")
            tradeDetails['fee'] = calc_fee(tradeDetails['tradeAmount'], tradeDetails['fee_percentage'], tradeDetails['currency'], True)
            tradeDetails['fee'] = str(tradeDetails['fee'])
            
            message = update.message.reply_text(
                #reply_to_message_id=update.message.message_id,
                text=f"Alrighty right noted. Proceeding with the trade...")
            bot_state.clear_waiting_for_input(chat_id)
            bot_state.set_var(tradeId, tradeDetails)
            time.sleep(2)
            if tradeDetails['brokerTrade']:
                bot_state.set_waiting_for_input(tradeDetails['broker'], "brokerfee", 'text', 'commands.escrow')
                message.edit_text(text=f"━━━━⍟𝗘𝘀𝗰𝗿𝗼𝘄 𝗦𝗵𝗶𝗲𝗹𝗱⍟━━━━\nAlrighty Right. Enter your fee in Percentage (0-40) of total amount")
                return
            else:
                tradeDetails["step5"] = "done"
        elif waiting_for == "brokerfee":
            
            text = is_number(user_input)
            if not text:
                update.message.reply_text(
                    # reply_to_message_id=update.message.message_id,
                    text=f"Please input a valid number"
                )
                return
            
            if text<0 or text>40:
                update.message.reply_text(
                    #reply_to_message_id=update.message.message_id,
                    text=f"Please input a number between 0 and 100"
                )
                return
            bot_state.clear_waiting_for_input(tradeDetails['broker'])
            tradeDetails['broker_fee_percentage'] = Decimal(user_input)/(100)
            tradeDetails['broker_fee'] = calc_fee(tradeDetails['tradeAmount'], tradeDetails['broker_fee_percentage'], tradeDetails['currency'])
            tradeDetails["step5"] = "done"
            tradeDetails['broker_fee_percentage'] = str(tradeDetails['broker_fee_percentage'])
            tradeDetails["tradeAmount"] = Decimal(tradeDetails["tradeAmount"])
            tradeDetails["tradeAmount"] += tradeDetails['broker_fee']
            tradeDetails["tradeAmount"] = str(tradeDetails["tradeAmount"])
            tradeDetails['broker_fee'] = str(tradeDetails['broker_fee'])
            bot_state.set_var(tradeId, tradeDetails)
            
        #Send message to SELLER asking for trade Approval
        if bot_state.getUserTrade(tradeDetails["seller"]) != tradeId and bot_state.getUserTrade(tradeDetails["seller"]) != "":
            bot_state.set_var(tradeId, tradeDetails)
            close_trade(bot_state, tradeId, "close[user_already_on_trade]")
            text = "The seller is already on a trade, ask them to finish/cancel that one first"
            context.bot.send_message(chat_id=tradeDetails["buyer"], text=text)
            if tradeDetails["brokerTrade"]:
                context.bot.send_message(chat_id=tradeDetails["broker"], text=text)
            return
        else:
            bot_state.setUserTrade(tradeDetails["seller"], tradeId)
        keyboard = [
        [InlineKeyboardButton("Approve", callback_data='option_4')],
        [InlineKeyboardButton("Decline", callback_data='option_5')],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        part1 =''
        part2 = ''
        if not tradeDetails["brokerTrade"]:
            part1 = f"𝗕𝘂𝘆𝗲𝗿: @{tradeDetails['buyer_username']}"
        else:
            part1 = f"𝗕𝗿𝗼𝗸𝗲𝗿: @{tradeDetails['broker_username']}"
            part2 = f"\n𝗕𝗿𝗼𝗸𝗲𝗿 𝗙𝗲𝗲:{str(tradeDetails['broker_fee'])} ({str(Decimal(tradeDetails['broker_fee_percentage'])*100)}%)"
            
        message = context.bot.send_message(
            chat_id=tradeDetails["seller"], 
            text=f"━━━━⍟𝗘𝘀𝗰𝗿𝗼𝘄 𝗦𝗵𝗶𝗲𝗹𝗱⍟━━━━\nAlrighty Right! It's time for a trade \n𝗧𝗿𝗮𝗱𝗲𝗜𝗗: `{tradeId}` \n\n𝗬𝗼𝘂𝗿 𝗥𝗼𝗹𝗲: Seller \n{part1}\n\n𝐓𝐫𝐚𝐝𝐞 𝐀𝐦𝐨𝐮𝐧𝐭: `{str(Decimal(tradeDetails['tradeAmount'])+Decimal(tradeDetails['fee']))}` *{tradeDetails['currency']}*\n𝐓𝐫𝐚𝐝𝐞 𝐂𝐨𝐧𝐭𝐫𝐚𝐜𝐭: {tradeDetails['tradeDetails']}\n𝗘𝘀𝗰𝗿𝗼𝘄 𝗙𝗲𝗲:{str(tradeDetails['fee'])} ({str(Decimal(tradeDetails['fee_percentage'])*100)}%){part2} \n\nOnce both parties have approved the trade we will proceed", 
            reply_markup=reply_markup, 
            parse_mode=ParseMode.MARKDOWN
        )
        bot_state.set_waiting_for_input(tradeDetails["seller"], [message], 'button')
        if message:
            tradeDetails['sellerApprovalId'] = message.message_id
        else:
            #message = context.bot.send_message(chat_id=str(str(update.message.from_user.id)), text=f"Couldnt message the other person, make sure they have ran /start atleast once", )
            bot_state.set_var(tradeId, tradeDetails)
            close_trade(bot_state, tradeId, "close[couldnt_message]")
            context.bot.send_message(chat_id=tradeDetails["buyer"], text=f"Couldn't message the other party. Make sure they have atleast ran /start first")
            if tradeDetails["brokerTrade"]:
                context.bot.send_message(chat_id=tradeDetails["broker"], text=f"Couldn't message the buyer. Make sure they have atleast ran /start first")
            return
        
        #Send message to BUYER asking for trade Approval
        if (bot_state.getUserTrade(tradeDetails["buyer"]) != tradeId and bot_state.getUserTrade(tradeDetails["buyer"]) != ""):
            print("Ah Sh-1")
            bot_state.set_var(tradeId, tradeDetails)
            close_trade(bot_state, tradeId, "close[user_already_on_trade]")
            text = "The Buyer is already on a trade, ask them to finish/cancel that one first"
            context.bot.send_message(chat_id=tradeDetails["seller"], text=text)
            if tradeDetails["brokerTrade"]:
                context.bot.send_message(chat_id=tradeDetails["broker"], text=text)
            return
        else:
            bot_state.setUserTrade(tradeDetails["buyer"], tradeId)
        #bot_state.setUserTrade(str(update.message.from_user.id), sent_message.message_id)
        keyboard = [
        [InlineKeyboardButton("Approve", callback_data='option_6')],
        [InlineKeyboardButton("Decline", callback_data='option_7')],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        part1 =''
        part2 = ''
        if not tradeDetails["brokerTrade"]:
            part1 = f"𝗦𝗲𝗹𝗹𝗲𝗿: @{tradeDetails['seller_username']}"
        else:
            part1 = f"𝗕𝗿𝗼𝗸𝗲𝗿: @{tradeDetails['broker_username']}"
            part2 = f"\n𝗕𝗿𝗼𝗸𝗲𝗿 𝗙𝗲𝗲:{str(tradeDetails['broker_fee'])} ({str(Decimal(tradeDetails['broker_fee_percentage'])*100)}%)"
            
        message = context.bot.send_message(
            chat_id=tradeDetails["buyer"], 
            text=f"━━━━⍟𝗘𝘀𝗰𝗿𝗼𝘄 𝗦𝗵𝗶𝗲𝗹𝗱⍟━━━━\nAlrighty Right! It's time for a trade \n𝗧𝗿𝗮𝗱𝗲𝗜𝗗: `{tradeId}` \n\n𝗬𝗼𝘂𝗿 𝗥𝗼𝗹𝗲: Buyer \n{part1}\n\n𝐓𝐫𝐚𝐝𝐞 𝐀𝐦𝐨𝐮𝐧𝐭: `{str(Decimal(tradeDetails['tradeAmount'])+Decimal(tradeDetails['fee']))}` *{tradeDetails['currency']}*\n𝐓𝐫𝐚𝐝𝐞 𝐂𝐨𝐧𝐭𝐫𝐚𝐜𝐭: {tradeDetails['tradeDetails']}\n𝗘𝘀𝗰𝗿𝗼𝘄 𝗙𝗲𝗲:{str(tradeDetails['fee'])} ({str(Decimal(tradeDetails['fee_percentage'])*100)}%){part2} \n\nOnce both parties have approved the trade we will proceed", 
            reply_markup=reply_markup, 
            parse_mode=ParseMode.MARKDOWN
        )
        bot_state.set_waiting_for_input(tradeDetails["buyer"], [message], 'button')
        if message:
            tradeDetails['buyerApprovalId'] = message.message_id
        else:
            #message = context.bot.send_message(chat_id=str(update.message.from_user.id), text=f"Couldnt message the other person, make sure they have ran /start atleast once", )
            bot_state.set_var(tradeId, tradeDetails)
            close_trade(bot_state, tradeId, "close[couldnt_message]")
            context.bot.send_message(chat_id=tradeDetails["seller"], text=f"Couldn't message the other party. Make sure they have atleast ran /start first")
            if tradeDetails["brokerTrade"]:
                context.bot.send_message(chat_id=tradeDetails["broker"], text=f"Couldn't message the buyer. Make sure they have atleast ran /start first")
            return
        if tradeDetails["brokerTrade"]:
            context.bot.send_message(chat_id=tradeDetails["broker"], text=f"Asking for seller's and buyer's approval")

        bot_state.set_var(tradeId, tradeDetails)
        return
    if tradeDetails["step7"] != "done":
        
        selection=''
        if tradeDetails["currency"] == 'LTC':
            selection = 'LTC'
        if tradeDetails["currency"] == 'SOL (Solana)' or tradeDetails["currency"] == 'USDT (Solana)':
            selection = 'SOL'
        if tradeDetails["currency"] == 'BNB (BSC Bep-20)' or tradeDetails["currency"] == 'USDT (BSC Bep-20)':
            selection = 'BSC'
        if tradeDetails["currency"] == 'DOGE':
            selection = 'DOGE'
        if not is_address_valid(user_input, selection):
            context.bot.send_message(chat_id=update.message.from_user.id, 
                text=f"That's a invalid ${tradeDetails['currency']} address"
            )
            return
        bot_state.clear_waiting_for_input(update.message.from_user.id)
        if str(update.message.from_user.id) == tradeDetails['seller']:
            tradeDetails["sellerAddress"] = user_input
            bot_state.clear_waiting_for_input(update.message.from_user.id)
            if tradeDetails["brokerTrade"]:
                context.bot.send_message(chat_id=tradeDetails["seller"], text="Noted!")
                context.bot.send_message(chat_id=tradeDetails["broker"], text="Received Seller's address, Enter yours!")
                part = ''
                if tradeDetails['brokerAddress']== '':
                    part  = ", waiting for broker's address"
                context.bot.send_message(chat_id=tradeDetails["buyer"], text=f"Received Seller's address{part}")
        elif str(update.message.from_user.id) == tradeDetails['broker']:
            tradeDetails["brokerAddress"] = user_input
            bot_state.clear_waiting_for_input(chat_id)
            context.bot.send_message(chat_id=tradeDetails["broker"], text="Noted!")
            context.bot.send_message(chat_id=tradeDetails["seller"], text="Received Broker's address, Enter yours!")
            part = ''
            if tradeDetails['sellerAddress']== '':
                part  = ", waiting for seller's address"
            context.bot.send_message(chat_id=tradeDetails["buyer"], text=f"Received Broker's address{part}")

        if tradeDetails["brokerTrade"]:
            if tradeDetails["sellerAddress"] == '' or tradeDetails["brokerAddress"] == '':
                bot_state.set_var(tradeId, tradeDetails)
                return
        
        tradeDetails["step7"] = "done"
        text = f"━━━━⍟𝗘𝘀𝗰𝗿𝗼𝘄 𝗦𝗵𝗶𝗲𝗹𝗱⍟━━━━\nAlrighty right! Now *Buyer* is notified to send `{str(Decimal(tradeDetails['tradeAmount'])+Decimal(tradeDetails['fee']))}` {tradeDetails['currency']} to our wallet address"
        message = context.bot.send_message(chat_id=tradeDetails["seller"], text=text, parse_mode=ParseMode.MARKDOWN)
        if tradeDetails["brokerTrade"]:
            context.bot.send_message(chat_id=tradeDetails["broker"], text=text, parse_mode=ParseMode.MARKDOWN)
        wallet = generateWallet(tradeId, bot_state)
        tradeDetails["ourAddress"] = wallet
        keyboard = [
            [InlineKeyboardButton("I have Sent", callback_data='option_8')]
        ]
        
            
        tradeDetails['tradeAmount']= Decimal(tradeDetails["tradeAmount"]) + Decimal(tradeDetails['fee'])
        tradeDetails['tradeAmount'] = str(tradeDetails['tradeAmount'])
        bot_state.set_var(tradeId, tradeDetails)
        reply_markup = InlineKeyboardMarkup(keyboard)
        if(wallet):
            
            print(tradeDetails)
            message = context.bot.send_message(chat_id=tradeDetails["buyer"], text=f"━━━━⍟𝗘𝘀𝗰𝗿𝗼𝘄 𝗦𝗵𝗶𝗲𝗹𝗱⍟━━━━\nAlrighty right! Now send exactly `{tradeDetails['tradeAmount']}` *{tradeDetails['currency']}* to the wallet below.\n\nOnce you have sent to our wallet, click the button below, the trade will proceed after we have received the funds \n\n`{wallet}`\n\n*NOTE:* If sending from an Exchange, be sure to withdraw this amount *plus Exchange's fee*",
            reply_markup=reply_markup,
            parse_mode=ParseMode.MARKDOWN
            )
            bot_state.set_waiting_for_input(tradeDetails["buyer"], [message], 'button')
        else:
            close_trade(bot_state, tradeId, "close[wallet_creation_failed]")
            context.bot.send_message(chat_id=tradeDetails["buyer"], text=f"An error has occurred, please try again later")
            context.bot.send_message(chat_id=tradeDetails["seller"], text=f"An error has occurred, please try again later")
            if tradeDetails["brokerTrade"]:
                context.bot.send_message(chat_id=tradeDetails["broker"], text=f"An error has occurred, please try again later")
            return
        return


description = "Starts the Escrow process"
aliases = ['/escrow']
enabled = True
hidden = True
OperaterCommand = False

#507 Lines of Trauma