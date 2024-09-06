import requests, os
from solana.rpc.api import Client
from solders.transaction import Transaction, VersionedTransaction
from solders.keypair import Keypair
from solders.pubkey import Pubkey
from solders.hash import Hash
from solders.message import Message
from solders import message
from spl.token.instructions import transfer_checked, TransferCheckedParams
from solders.token.associated import get_associated_token_address
from spl.token.instructions import get_associated_token_address as sol_get_associated_token_address
from spl.token.instructions import create_associated_token_account
from solana.rpc.commitment import Processed, Finalized
from solana.rpc.types import TxOpts
import base58, json, traceback
from solathon import keypair as solkeypair

from decimal import Decimal

from globalState import GlobalState
from imports.utils import log_message


def get_latest_blockhash():
    url = "https://api.mainnet-beta.solana.com"
    headers = {
        "Content-Type": "application/json"
    }
    payload = {
        "id": 1,
        "jsonrpc": "2.0",
        "method": "getLatestBlockhash",
        
    }

    response = requests.post(url, headers=headers, data=json.dumps(payload))
    response_json = response.json()

    if 'result' in response_json:
        blockhash = response_json['result']['value']['blockhash']
        return blockhash
    else:
        print("Failed to fetch the latest blockhash")
        print(response_json)
    try:
        transaction_json = json.loads(transaction_json_str)
    except json.JSONDecodeError as e:
        print(f"Invalid JSON string: {e}")
        return {"error": f"Invalid JSON string: {e}"}

    # Convert the transaction to bytes and then encode it in base64
    transaction_bytes = json.dumps(transaction_json).encode('utf-8')
    transaction_base58 = base58.b58encode(transaction_bytes).decode('utf-8')

    # Create the payload for the RPC request
    payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "sendTransaction",
        "params": [transaction_base58]
    }

    # Send the transaction via a POST request
    headers = {"Content-Type": "application/json"}
    response = requests.post(rpc_url, headers=headers, json=payload)

    # Check for HTTP request errors
    try:
        response.raise_for_status()
    except requests.exceptions.HTTPError as err:
        print(f"HTTP error occurred: {err}")
        return {"error": str(err)}

    # Parse the response JSON
    result = response.json()

    return result

def send_transaction(sender_private_key, fee_payer_private_key, recipient_address, send_amount, log_file):
    try:
        # Connect to Solana client
        client = Client("https://api.mainnet-beta.solana.com")

        #Escrow Wallet
        
        temp_keypair = solkeypair.Keypair.from_private_key(base58.b58encode(bytes.fromhex(sender_private_key)).decode('utf-8'))
        public_key_bytes = bytes(temp_keypair.public_key)
        sender_private_key = bytes.fromhex(sender_private_key) + public_key_bytes
        sender_private_key = base58.b58encode(sender_private_key).decode('utf-8')

        #Fee Payer wallet
        

        temp_keypair = solkeypair.Keypair.from_private_key(base58.b58encode(bytes.fromhex(fee_payer_private_key)).decode('utf-8'))
        public_key_bytes = bytes(temp_keypair.public_key)
        fee_payer_private_key = bytes.fromhex(fee_payer_private_key) + public_key_bytes
        fee_payer_private_key = base58.b58encode(fee_payer_private_key).decode('utf-8')
        usdt_mint_address = "Es9vMFrzaCERmJfrF4H2FYD4KCoNkY11McCe8BenwNYB"
        sender = Keypair.from_base58_string(sender_private_key)
        fee_payer = Keypair.from_base58_string(fee_payer_private_key)
        usdt_mint_address_bytes = base58.b58decode(usdt_mint_address)
        recipient_address_bytes = base58.b58decode(recipient_address)

        sender_token_address = get_associated_token_address(sender.pubkey(), Pubkey(usdt_mint_address_bytes))
        fee_payer_token_address = get_associated_token_address(fee_payer.pubkey(), Pubkey(usdt_mint_address_bytes))
        recipient_token_address = get_associated_token_address(Pubkey(recipient_address_bytes), Pubkey(usdt_mint_address_bytes))
        amount = send_amount * Decimal(1_000_000)
        ourfee = Decimal(0.02) * amount
        finalamount = int(amount-ourfee)
        ourfee = int(ourfee)

        account_info = client.get_account_info(recipient_token_address)
        instruction =[]
        if account_info.value is None:
            log_message("Token account does not exist. Creating token account...", log_file)
            log_message("adding charges to out wallet", log_file)
            spl_creation_fee = int(Decimal(0.34) * Decimal(1_000_000))
            ourfee+=spl_creation_fee
            finalamount-=spl_creation_fee
            instruction.append(
                create_associated_token_account(
                    payer=fee_payer.pubkey(),
                    owner=Pubkey(recipient_address_bytes),
                    mint=Pubkey(usdt_mint_address_bytes)
                )
            )
        instruction.append(
            transfer_checked(
                TransferCheckedParams(
                    program_id=Pubkey(base58.b58decode("TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA")),
                    source=sender_token_address,
                    mint=Pubkey(usdt_mint_address_bytes),
                    dest=fee_payer_token_address,
                    owner=sender.pubkey(),
                    amount=ourfee,  # Specify the amount of tokens to transfer
                    decimals=6  # Number of decimal places for the token
                )
            )
        )

        instruction.append(
            transfer_checked(
                TransferCheckedParams(
                    program_id=Pubkey(base58.b58decode("TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA")),
                    source=sender_token_address,
                    mint=Pubkey(usdt_mint_address_bytes),
                    dest=recipient_token_address,
                    owner=sender.pubkey(),
                    amount=finalamount,  # Specify the amount of tokens to transfer
                    decimals=6  # Number of decimal places for the token
                )
            )
        )
        recent_hash= get_latest_blockhash()
        message1 = Message(
            instructions=instruction,
            payer=fee_payer.pubkey(),
        # recent_blockhash=Hash.from_string(get_latest_blockhash())
        )
        tempTrans = Transaction(from_keypairs=[fee_payer, sender], message=message1, recent_blockhash=Hash.from_string(recent_hash))
        tempTrans.sign([fee_payer,sender], recent_blockhash=Hash.from_string(recent_hash))
        transaction = VersionedTransaction.from_bytes(tempTrans.__bytes__())

        # EH well why make it more complex lol
        #signature = fee_payer.sign_message(message.to_bytes_versioned(transaction.message))
        #signature2 = sender.sign_message(message.to_bytes_versioned(transaction.message))
        #signed_txn = VersionedTransaction.populate(transaction.message, [signature, signature2])

        opts = TxOpts(skip_preflight=False, preflight_commitment=Finalized, max_retries=5)
        result = client.send_raw_transaction(txn=bytes(transaction), opts=opts)
        transaction_id = json.loads(result.to_json())['result']
        log_message(f"TX response: {result.to_json()}", log_file)
        log_message(f"Transaction sent: https://solscan.io/tx/{transaction_id}", log_file)
    except Exception as e:
        error_message = f"An error occurred: {str(e)}\n"
        error_message += ''.join(traceback.format_exception(None, e, e.__traceback__))

        log_message(error_message, log_file)

def send_usdt_sol_transaction(action_id, bot_state: GlobalState):
    tradeDetails = {}
    if action_id.startswith('TRADE'):
        tradeDetails = bot_state.get_var(action_id)
    elif action_id.startswith('TXID'):
        tradeDetails = bot_state.get_tx_var(action_id)
    walletDetails = bot_state.get_wallet_info(action_id)

    log_file = tradeDetails['ourAddress']
    sender_private_key = walletDetails['secretKey']
    recipient_address = tradeDetails['sellerAddress']
    send_amount = Decimal(tradeDetails["tradeAmount"])

    log_message(f"Initiating transaction for Trade ID: {action_id}", log_file)
    log_message(f"Sender: {walletDetails['publicKey']}, Recipient: {recipient_address}, Amount: {send_amount} USDT", log_file)


    send_transaction(sender_private_key, os.getenv('SOLANA_FEE_PAYER_SECRET'), recipient_address, send_amount, log_file)
    log_message(f"Transaction for Trade ID {action_id} completed", log_file)

#LOVE you Solana



#Issue1: After sending 2 taking a fee of 2% ie 0.04 but still leaves tiny amount of 0.000001 on escrow wallet (83hCEcaxPMSzaJAc2UAJ9tojeFLyweyeZvZwDs8JEdSv)
#reason: Not tried to figure yet