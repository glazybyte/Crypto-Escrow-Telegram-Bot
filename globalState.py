import json, inspect, time, random, copy, math, psutil, os
from concurrent.futures import ThreadPoolExecutor
from telegram import ParseMode
from telegram.error import TelegramError

from imports.utils import log_message
from databaseClass import MySQLDatabase
from commands.cancel import close_trade

class GlobalState:  
    
    def __init__(self, enabledb, host='', port=6969, user='', password='', database=''):
        self.state = {
            "lockmanager": {},
            "user_data": {},
            "escrow": {},
            "waiting_for_input": {},
            "wallet_checker_queue": {},
            "wallets": {},
            "items": {},
            "txs": {},
            "intervals_timeouts": {}
        }
        if (enabledb.lower() in ['true', 'yes', 'yeah', 'yup', 'certainly', 'sex']):
            self.enabledb = True
        else:
            self.enabledb = False
        
        if enabledb:
            self.database = MySQLDatabase(
                host= host,
                port= port,
                user= user,
                password= password,
                database= database
            )
        self.add_timeout(60*60, 'hourly_cleanup')
        self.add_timeout(25*60, 'deepclean')
    def set_var(self, var: str, new_value: dict):
        self.state['escrow'][var] = new_value
        self.state['escrow'][var]['__last_access'] = int(time.time())
        if self.enabledb:
            self.database.send_data_trade(var, new_value)

    def get_var(self, var: str):
        if self.enabledb:
            if var in self.state:
                print(f'cache call for {var}')
                return self.state['escrow'].get(var)
            else:
                self.state['escrow'][var] = self.database.retrieve_data_trade(var)
        self.state['escrow'][var]['__last_access'] = int(time.time())
        return self.state['escrow'].get(var)

    def lockUser(self, user: str):
        self.state["lockmanager"][user] = True
    
    def unlockUser(self, user: str):
        self.state["lockmanager"][user] = False
    
    def isUserLocked(self, user: str):
        return self.state["lockmanager"].get(user, False)

    def getUser(self, userid:str):
        template = {
            "currentTrade": "",
            "shopName": "none",
            "shopDesc": "none",
            "shopStatus": "enabled",
            "shopItems": [],
            "userStatus": "enabled"
        }
        if self.enabledb:
            if userid in self.state["user_data"]:
                print(f'cache call for {userid}')
                return self.state["user_data"].get(userid,template)
            else:
                rrun = self.database.retrieve_data_user_trade(userid)
                if("currentTrade" in rrun):
                    self.state["user_data"][userid] = rrun
                else:
                    self.state["user_data"][userid] = template
        user = self.state["user_data"].get(userid, template)
        self.state['user_data'][userid]['__last_access'] = int(time.time())
        if 'shopItems' not in user:
            user['shopItems'] = []
            user['shopName'] = user['shopDesc'] = 'none'
            user['shopStatus'] = 'enabled'
        return self.state["user_data"].get(userid, template)
    
    def setUser(self, userid: str, data):
        self.state["user_data"][userid] = data
        self.state['user_data'][userid]['__last_access'] = int(time.time())
        if self.enabledb:
            self.database.send_data_user_trade(userid, data)

    def setUserTrade(self, userid: str, id: str):
        user = self.getUser(userid)
        user['currentTrade'] = id
        self.setUser(userid, user)

    def getUserTrade(self, userid: str):
        user = self.getUser(userid)
        return user['currentTrade'];

    def set_waiting_for_input(self, chat_id: str, context, input_type = 'text', cmd='none'):
        caller_frame = inspect.stack()[1]
        chat_id = str(chat_id)
        if input_type == 'button':
            if len(context) == 1:
                context = {
                    'message_id': context[0].message_id,
                    'chat_id': context[0].chat_id,
                    'intended_user': chat_id
                }
            else:
                context = {
                'message_id': context[0].message_id,
                'chat_id': context[0].chat_id,
                'intended_user': chat_id
            } | context[1]
        if cmd == 'none':
            self.state["waiting_for_input"][chat_id] = {'context': context, 'input_type': input_type, 'cmd': inspect.getmodule(caller_frame[0]).__name__, 'user': chat_id}
        else:
            self.state["waiting_for_input"][chat_id] = {'context': context, 'input_type': input_type, 'cmd': cmd, 'user': chat_id}
        self.state['waiting_for_input'][chat_id]['__last_access'] = int(time.time())
            
    def get_waiting_for_input_context(self, chat_id: str):
        chat_id = str(chat_id)
        if chat_id in self.state["waiting_for_input"]:
            res = self.state["waiting_for_input"].get(chat_id, {})
            self.state['waiting_for_input'][chat_id]['__last_access'] = int(time.time())
            return res['context']
        else:
            return False
    def get_waiting_for_input_user(self, chat_id: str):
        chat_id = str(chat_id)
        if chat_id in self.state["waiting_for_input"]:
            res = self.state["waiting_for_input"].get(chat_id, {})
            self.state['waiting_for_input'][chat_id]['__last_access'] = int(time.time())
            return res['user']
        else:
            return False
    def get_waiting_for_input_type(self, chat_id: str):
        chat_id = str(chat_id)
        if chat_id in self.state["waiting_for_input"]:
            res = self.state["waiting_for_input"].get(chat_id, {})
            self.state['waiting_for_input'][chat_id]['__last_access'] = int(time.time())
            return res['input_type']
        else:
            return False
    def get_waiting_for_cmd(self, chat_id: str):
        chat_id = str(chat_id)
        if chat_id in self.state["waiting_for_input"]:
            res = self.state["waiting_for_input"].get(chat_id, {})
            self.state['waiting_for_input'][chat_id]['__last_access'] = int(time.time())
            return res['cmd']
        else:
            return False
    
    def clear_waiting_for_input(self, chat_id: str):
        self.state["waiting_for_input"].pop(chat_id, None)
    
    def save_wallet_info(self, tradeId: str, memonic: str, secretKey: str, publicKey: str, currency: str, tradeType='escrow'):
        self.state["wallets"][tradeId] = {
            "tradeId": tradeId,
            "memonic": memonic,
            "secretKey": secretKey,
            "publicKey": publicKey,
            "currency": currency,
            "tradeType": tradeType,
            "__time_added": int(time.time())
        }
        #self.state['wallets'][tradeId]['__last_access'] = int(time.time())
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
        #self.state['wallets'][tradeId]['__last_access'] = int(time.time())
        return self.state["wallets"][tradeId]

    
    def add_address_to_check_queue(self,publicKey: str, tradeId: str,  currency: str):
        self.state["wallet_checker_queue"][publicKey] = {
            "tradeId":tradeId,
            "currency": currency,
            "__time_added": int(time.time())
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

    def add_item(self,item_id: str, item_details: str):
        self.state["items"][item_id] = item_details
        self.state["items"][item_id]['__last_access'] = int(time.time())
        user = self.getUser(item_details['seller'])
        
        if item_id not in user["shopItems"]:
            user["shopItems"].append(item_id)
        self.setUser(item_details['seller'], user)
        if self.enabledb:
            self.database.send_data_items(item_id, copy.deepcopy(self.state["items"][item_id]))
        return
    
    def get_item_details(self, item_id: str):
        if self.enabledb:
            if item_id in self.state["items"]:
                print(f'cache call for Item ID {item_id}')
                return self.state["items"][item_id]
            else:

                self.state["items"][item_id] = self.database.retrieve_data_items(item_id)
        if item_id in self.state["items"]:
            self.state["items"][item_id]['__last_access'] = int(time.time())
            return self.state["items"][item_id]
        else:
            return False
        
    def remove_item(self, item_id):
        if self.enabledb:
            self.database.delete_item(item_id)
        item_details = self.get_item_details(item_id)
        user = self.getUser(item_details['seller'])
        if item_id in user["shopItems"]:
            user["shopItems"].pop(item_id, None)
        self.setUser(item_details['seller'], user)
        self.state["items"].pop(item_id, None)

    def set_tx_var(self, tx_id: str, new_value: dict):
        self.state['txs'][tx_id] = new_value
        self.state['txs'][tx_id]['__last_access'] = int(time.time())
        if self.enabledb:
            self.database.send_data_txns(tx_id, copy.deepcopy(new_value))

    def get_tx_var(self, tx_id: str):
        if self.enabledb:
            if tx_id in self.state['txs']:
                print(f'cache call for TXID {tx_id}')
                self.state['txs'][tx_id]['__last_access'] = int(time.time())
                return self.state['txs'].get(tx_id)
            else:
                self.state['txs'][tx_id] = self.database.retrieve_data_txns(tx_id)
        return self.state['txs'].get(tx_id)

    def add_interval(self, reoccur_after, context, cmd):
        id = "IN"+''.join([str(random.randint(0, 9)) for _ in range(12)])
        self.state['intervals_timeouts'][id] = {
            'type': 'interval',
            'interval': reoccur_after,
            'context': context,
            'cmd': cmd,
            'next_call_at': int(time.time()) + int(reoccur_after)
        }
        if self.enabledb:
            self.database.send_data_intervals_timeouts(id, self.state['intervals_timeouts'][id]['type'], self.state['intervals_timeouts'][id]['context'], self.state['intervals_timeouts'][id]['cmd'], self.state['intervals_timeouts'][id]['next_call_at'])
        return id
    
    def update_interval(self, id, data):
        self.state['intervals_timeouts'][id] = data
        if self.enabledb:
            self.database.send_data_intervals_timeouts(id, self.state['intervals_timeouts'][id]['type'], self.state['intervals_timeouts'][id]['context'], self.state['intervals_timeouts'][id]['cmd'], self.state['intervals_timeouts'][id]['next_call_at'])
    
    def remove_timer(self, interval_timeout_id):
        self.state["intervals_timeouts"].pop(interval_timeout_id, None)
        if self.enabledb:
            self.database.delete_interval_timeout(interval_timeout_id)

    def add_timeout(self, reoccur_after, context, cmd='none'):
        if cmd == 'none':
            caller_frame = inspect.stack()[1]
            cmd = inspect.getmodule(caller_frame[0]).__name__
        id = "TI"+''.join([str(random.randint(0, 9)) for _ in range(12)])
        self.state['intervals_timeouts'][id] = {
            'type': 'timeout',
            'context': context,
            'cmd': cmd,
            'next_call_at': int(time.time()) + int(reoccur_after)
        }
        if self.enabledb:
            self.database.send_data_intervals_timeouts(id, self.state['intervals_timeouts'][id]['type'], self.state['intervals_timeouts'][id]['context'], self.state['intervals_timeouts'][id]['cmd'], self.state['intervals_timeouts'][id]['next_call_at'])
        return id
    
    def get_all_timers(self, is_init=False):
        if self.enabledb and is_init:
            self.state['intervals_timeouts'] = self.database.fetch_all_data_intervals_timeouts()
        return self.state['intervals_timeouts']
    
    def get_seller_items(self, seller_id: str):
        seller_item_ids = copy.deepcopy(self.getUser(seller_id)['shopItems'])
        item_id_not_in_cache = []
        cached_items = []
        for i in range(len(seller_item_ids)):
            if seller_item_ids[i] in self.state['items']:
                self.state['items'][seller_item_ids[i]]['__last_access'] = int(time.time())
                item = self.state['items'][seller_item_ids[i]]
                item.pop('id', None)
                item['item_id'] = seller_item_ids[i]
                cached_items.append(item)
            else:
                item_id_not_in_cache.append(seller_item_ids[i])
        if self.enabledb:
            with ThreadPoolExecutor() as executor:
                futures = []
                for item_id in item_id_not_in_cache:
                    future = executor.submit(self.database.retrieve_data_items, item_id)
                    futures.append(future)
                for i in range(len(futures)):
                    item = futures[i].result()
                    item['__last_access'] = int(time.time())
                    item.pop('id', None)
                    item['item_id'] = item_id_not_in_cache[i]
                    self.state['items'][item_id_not_in_cache[i]] = item
                    cached_items.append(item)
        return cached_items
            
def timeout_up(context, bot, bot_state: GlobalState):
    print('Cleaner Initiating...')
    user_data_limit = 20_000
    tx_limit = 15_000
    escrow_limit = 15_000
    items_limit = 30_000
    #wallet_limit = tx_limit + escrow_limit
    #The total memory ussage should under 200 MB with these presets
    base = bot_state.state
    print('starting Ussage Checker...')
    time.sleep(1)
    print('-------------------------------------------------------------')
    print(f"escrow length: {len(base['escrow'])}, ussage: {(len(base['escrow'])/escrow_limit)*100}%")
    print(f"items length: {len(base['items'])}, ussage: {(len(base['items'])/items_limit)*100}%")
    print(f"txs length: {len(base['txs'])}, ussage: {(len(base['txs'])/tx_limit)*100}%")
    print(f"user_data length: {len(base['user_data'])}, ussage: {(len(base['user_data'])/user_data_limit)*100}%")
    
    process = psutil.Process(os.getpid())
    memory_usage_before = process.memory_info().rss / (1024 ** 2)  
    print(f"\nMemory Usage: {memory_usage_before:.2f} MB")
    print('-------------------------------------------------------------')
    
    if context == 'hourly_cleanup':

        keys_to_be_poped = []

        for tx_id, tx in base['txs'].items(): 
            if tx['status'].startswith('close') and tx['status'] != 'close[delivered]':
                keys_to_be_poped.append(tx_id)

        pop_list(keys_to_be_poped, base['txs'])
        keys_to_be_poped = []

        for item_id, item in base['items'].items():
            if (int(time.time())-item['__last_access']) >= 60*60:
                keys_to_be_poped.append(item_id)
        
        pop_list(keys_to_be_poped, base['items'])
        keys_to_be_poped = []

        for user_id, user in base['user_data'].items():
            if (int(time.time())-user['__last_access']) >= 60*60:
                keys_to_be_poped.append(user_id)
        
        pop_list(keys_to_be_poped, base['user_data'])
        keys_to_be_poped = []

        for publicKey, info in base['wallet_checker_queue'].items():
            if (int(time.time())-info['__time_added']) >= 2*60*60:
                keys_to_be_poped.append(publicKey)

        for key in keys_to_be_poped:
            bot_state.remove_address_from_queue(key)
        
        keys_to_be_poped = []
        escrow_to_be_closed = []

        for escrow_id, escrow in base['escrow'].items():
            if escrow['status'].startswith('close'):
                keys_to_be_poped.append(escrow_id)
            elif escrow['status'] == 'open' and (escrow['ourAddress'] not in base['wallet_checker_queue']) and (time.time()-escrow['__last_access']) > 60*60:
                escrow_to_be_closed.append(escrow_id)
        
        for escrow_id in escrow_to_be_closed:
            escrow = base['escrow'][escrow_id]
            keys_to_be_poped.append(escrow_id)
            close_trade(bot_state, escrow_id, 'close[inactivity]')
            try:
                # bot.send_message(
                #     chat_id=escrow["buyer"], 
                #     parse_mode=ParseMode.MARKDOWN,
                #     text=f"Escrow ID: `{escrow_id}`\nEscrow has been closed due to inactivity", 
                # )
                pass
            except TelegramError as e:
                pass
            try:
                # bot.send_message(
                #     chat_id=escrow["seller"], 
                #     parse_mode=ParseMode.MARKDOWN,
                #     text=f"Escrow ID: `{escrow_id}`\nEscrow has been closed due to inactivity", 
                # )
                pass
            except TelegramError as e:
                pass
        
        pop_list(keys_to_be_poped, base['escrow'])
        keys_to_be_poped = []

        for action_id, wallet in base['wallets'].items():
            if (int(time.time())-wallet['__time_added']) >= 20*60:
                keys_to_be_poped.append(action_id)
        
        pop_list(keys_to_be_poped, base['wallets'])

        print('Cleaner Finished')


    ussage_percentage = {
            'user_data_limit': len(base['user_data'])/user_data_limit,
            'tx_limit': len(base['txs'])/tx_limit,
            'escrow_limit': len(base['escrow'])/escrow_limit,
            'items_limit': len(base['items'])/items_limit
        }
    if ussage_percentage['user_data_limit'] <0.95 and ussage_percentage['tx_limit'] <0.95 and ussage_percentage['escrow_limit'] <0.95 and ussage_percentage['items_limit'] <0.95:
        print('Deep clean not needed')
        bot_state.add_timeout(60*60, 'hourly_cleanup')
        return
    context = 'deepclean'

    if context == 'deepclean':
        print('Starting Deep Clean...')
        
        for name, percent in ussage_percentage.items():
            selected_data = {}
            num_to_remove = 0
            total_removed = 0
            if percent < 0.95:
                continue
            print(f'Running Deep Clean for {name}')
            if name == 'user_data_limit':
                selected_data = copy.deepcopy(base['user_data'])
            if name == 'tx_limit':
                selected_data = copy.deepcopy(base['txs'])
            if name == 'escrow_limit':
                selected_data = copy.deepcopy(base['escrow'])
            if name == 'items_limit':
                selected_data = copy.deepcopy(base['items'])
            num_to_remove = (len(selected_data)/percent)-((len(selected_data)/percent)*0.65)
            
            if len(selected_data)-(len(selected_data)/percent) > 0:
                num_to_remove += len(selected_data)-(len(selected_data)/percent)

            num_to_remove = math.floor(num_to_remove)
            if(len(selected_data)> num_to_remove):
                num_to_remove += 1

            i = 1
            while total_removed < num_to_remove:
                for key, value in selected_data.items():
                    if total_removed >= num_to_remove:
                        break
                    time_diff = 0
                    if i == 1:
                        time_diff = 50*60
                    elif i == 2:
                        time_diff = 40*60
                    elif i == 3:
                        time_diff = 30*60
                    #time diff = 0 mean high load, so removing all until num_to_remove is satisfied

                    type_ = '__last_access'
                    if '__time_added' in value:
                        type_ = '__time_added'
                    if (time.time() - value[type_]) >= time_diff:
                        if name == 'user_data_limit':
                            base['user_data'].pop(key, None)
                        if name == 'tx_limit':
                            base['txs'].pop(key, None)
                        if name == 'escrow_limit':
                            base['escrow'].pop(key, None)
                        if name == 'items_limit':
                            base['items'].pop(key, None)
                        #selected_data.pop(key, None)
                        total_removed += 1

                i += 1
            selected_data = {}
        bot_state.add_timeout(25*60, 'deepclean')
    print('starting Ussage Checker...')
    time.sleep(1)
    print('-------------------------------------------------------------')
    print(f"escrow length: {len(base['escrow'])}, ussage: {(len(base['escrow'])/escrow_limit)*100}%")
    print(f"items length: {len(base['items'])}, ussage: {(len(base['items'])/items_limit)*100}%")
    print(f"txs length: {len(base['txs'])}, ussage: {(len(base['txs'])/tx_limit)*100}%")
    print(f"user_data length: {len(base['user_data'])}, ussage: {(len(base['user_data'])/user_data_limit)*100}%")
    
    process = psutil.Process(os.getpid())
    memory_usage = process.memory_info().rss / (1024 ** 2)
    print(f"\nMemory Usage: {memory_usage:.2f} MB")
    print(f"\nFreed Memory: {memory_usage_before-memory_usage:.2f} MB")
    print('-------------------------------------------------------------')


def pop_list(poplist, dict_data):
    for key in poplist:
        dict_data.pop(key)
        #clean base['user_data']
#lol after completing get_seller_items fxn to include item_id I realised it have item_id saved as id already, now not touching it tch tch

