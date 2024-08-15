from databaseClass import MySQLDatabase
from imports.utils import log_message
import json
class GlobalState:  
    
    def __init__(self, enabledb, host='', port=6969, user='', password='', database=''):
        self.state = {
            "lockmanager": {},
            "trade": {},
            "waiting_for_input": {},
            "wallet_checker_queue": {},
            "wallets": {}
        }
        self.enabledb = enabledb
        if enabledb:
            self.database = MySQLDatabase(
                host= host,
                port= port,
                user= user,
                password= user,
                database= database
            )
        
    def set_var(self, var: str, new_value: dict):
        self.state[var] = new_value
        if self.enabledb:
            self.database.send_data_trade(var, new_value)

    
    def get_var(self, var: str):
        if self.enabledb:
            if var in self.state:
                print(f'cache call for {var}')
                return self.state.get(var)
            else:
                self.state[var] = self.database.retrieve_data_trade(var)
        return self.state.get(var)

    
    def lockUser(self, user: str):
        self.state["lockmanager"][user] = True

    
    def unlockUser(self, user: str):
        self.state["lockmanager"][user] = False

    
    def isUserLocked(self, user: str):
        return self.state["lockmanager"].get(user, False)

    
    def setUserTrade(self, user: str, id: str):
        user = str(user)
        self.state["trade"][user] = id
        if self.enabledb:
            rrun = self.database.retrieve_data_user_trade(user)
            rrun["currentTrade"] = id
            self.database.send_data_user_trade(user, rrun)

    
    def getUserTrade(self, user: str):
        user = str(user)
        if self.enabledb:
            if user in self.state["trade"]:
                print(f'cache call for {user}')
                return self.state["trade"].get(str(user),"")
            else:
                rrun = self.database.retrieve_data_user_trade(user)
                if("currentTrade" in rrun):
                    self.state["trade"][user] = rrun["currentTrade"]
                else:
                    self.state["trade"][user] = ""
        return self.state["trade"].get(str(user),"")

    
    def set_waiting_for_input(self, chat_id: str, input_type: str):
        chat_id = str(chat_id)
        """Set the type of input the bot is waiting for from a user."""
        self.state["waiting_for_input"][chat_id] = input_type

    
    def get_waiting_for_input(self, chat_id: str):
        chat_id = str(chat_id)
        """Get the type of input the bot is waiting for from a user."""
        return self.state["waiting_for_input"].get(chat_id)

    
    def clear_waiting_for_input(self, chat_id: str):
        """Clear the input waiting state for a user."""
        self.state["waiting_for_input"].pop(chat_id, None)
    
    
    def save_wallet_info(self, tradeId: str, memonic: str, secretKey: str, publicKey: str, currency: str):
        self.state["wallets"][tradeId] = {
            "tradeId": tradeId,
            "memonic": memonic,
            "secretKey": secretKey,
            "publicKey": publicKey,
            "currency": currency
        }
        if self.enabledb:
            self.database.send_data_wallets(tradeId, self.state["wallets"][tradeId])
        log_message("Wallet generation Successful!\n"+json.dumps(self.state["wallets"][tradeId]), publicKey)
    
    def get_wallet_info(self, tradeId: str):
        if self.enabledb:
            if tradeId in self.state["wallets"]:
                print(f'cache call for {tradeId}')
                return self.state["wallets"][tradeId] 
            else:
                self.state["wallets"][tradeId] = self.database.retrieve_data_wallets(tradeId)
        return self.state["wallets"][tradeId]

    
    def add_address_to_check_queue(self,publicKey: str, tradeId: str,  currency: str):
        self.state["wallet_checker_queue"][publicKey] = {
            "tradeId":tradeId,
            "currency": currency
        }
        if self.enabledb:
            self.database.send_data_wallet_checker_queue(publicKey, self.state["wallet_checker_queue"][publicKey])
        return
    
    def get_address_info(self,publicKey: str):
        if self.enabledb:
            if publicKey in self.state["wallet_checker_queue"]:
                print(f'cache call for {publicKey}')
                return self.state["wallet_checker_queue"][publicKey]
            else:
                self.state["wallet_checker_queue"][publicKey] = self.database.retrieve_data_wallet_checker_queue(publicKey)
        return self.state["wallet_checker_queue"][publicKey]
        
    
    def get_all_queue_addresses(self):
        if self.enabledb:
            self.state["wallet_checker_queue"] = self.database.fetch_all_wallet_checker_queue()
        return self.state["wallet_checker_queue"]
    
    
    def remove_address_from_queue(self, publicKey: str):
        if self.enabledb:
            self.database.delete_wallet_checker_queue(publicKey)
        self.state["wallet_checker_queue"].pop(publicKey, None)
  