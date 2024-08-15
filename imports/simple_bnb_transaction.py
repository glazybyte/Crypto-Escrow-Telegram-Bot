from web3 import Web3
from web3.middleware import geth_poa_middleware
from decimal import Decimal
from globalState import GlobalState
def send_bsc_with_fee_deduction(secret_key, recipient_address, amount):
    w3 = Web3(Web3.HTTPProvider('https://bsc-dataseed.binance.org/'))
    w3.middleware_onion.inject(geth_poa_middleware, layer=0)
    try:
        w3.eth.get_block('latest')
    except:
        raise ConnectionError("Failed to connect to Binance Smart Chain network.")
    total_amount_in_wei = w3.to_wei(Decimal(amount), 'ether')
    account = w3.eth.account.from_key(secret_key)
    gas_price = w3.eth.gas_price
    gas_limit = 21000 
    tx_fee_in_wei = gas_price * gas_limit
    amount_to_send_in_wei = total_amount_in_wei - tx_fee_in_wei
    if amount_to_send_in_wei <= 0:
        raise ValueError("The input amount is too low to cover the transaction fee.")
    transaction = {
        'to': recipient_address,
        'value': amount_to_send_in_wei,
        'gas': gas_limit,
        'gasPrice': gas_price,
        'nonce': w3.eth.get_transaction_count(account.address),
        'chainId': 56  # BSC Mainnet chain ID
        # Use 97 for BSC Testnet
    }
    signed_txn = w3.eth.account.sign_transaction(transaction, private_key=secret_key)
    tx_hash = w3.eth.send_raw_transaction(signed_txn.rawTransaction)
    return w3.to_hex(tx_hash)


def send_bnb_transaction(tradeId: str, bot_state: GlobalState):
    tradeDetails = bot_state.get_var(tradeId)
    walletDetails = bot_state.get_wallet_info(tradeId=tradeId)

    log_file = tradeDetails['ourAddress']
    
    secret_key = walletDetails['secretKey']
    recipient_address = tradeDetails['sellerAddress']
    amount = tradeDetails["tradeAmount"] # Total amount in BNB, including the transaction fee

    tx_hash = send_bsc_with_fee_deduction(secret_key, recipient_address, amount)
    print(f"Transaction hash: {tx_hash}")


#Fuck you bsc (respectfully)
