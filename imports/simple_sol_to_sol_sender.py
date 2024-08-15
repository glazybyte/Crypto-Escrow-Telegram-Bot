import base58, traceback
from solathon.core.instructions import transfer
from solathon import Client, Transaction, PublicKey, Keypair
from decimal import Decimal

from globalState import GlobalState
from imports.utils import log_message

log_file = ''
def sol_to_lamports(sol_amount_str):
    # Convert SOL amount (string) to Decimal
    sol_amount = Decimal(sol_amount_str)
    # Convert to lamports (1 SOL = 1,000,000,000 lamports)
    lamports = int(sol_amount * Decimal(1_000_000_000))
    return lamports

def send_transaction(hex_private_key, recipient_address, sol_amount_str, log_file):
    try: 
        client = Client("https://api.mainnet-beta.solana.com")

        #Escrow Wallet
        private_key_base58 = base58.b58encode(bytes.fromhex(hex_private_key)).decode('utf-8')
        # Initialize the wallet with the private key
        keypair = Keypair.from_private_key(private_key_base58)

        amount = sol_to_lamports(sol_amount_str)
        fee = 5000  # example fee in lamports (0.000005 SOL)
        send_amount = amount - fee
        
        # Ensure the amount to send is greater than zero
        if send_amount <= 0:
            raise ValueError("The amount to send is too low to cover the transaction fee.")
        
        # Create transfer instruction
        instruction = transfer(
            from_public_key=keypair.public_key,
            to_public_key=PublicKey(recipient_address), 
            lamports=send_amount
        )

        # Create transaction
        transaction = Transaction(instructions=[instruction], signers=[keypair])

        # Send the transaction
        result = client.send_transaction(transaction)
        return result
    except Exception as e:
        error_message = f"An error occurred: {str(e)}\n"
        error_message += ''.join(traceback.format_exception(None, e, e.__traceback__))
        
        # Log the detailed error message
        log_message(error_message, log_file)


def simple_sol_to_sol_transaction(tradeId, bot_state: GlobalState):
    tradeDetails = bot_state.get_var(tradeId)
    walletDetails = bot_state.get_wallet_info(tradeId=tradeId)

    log_file = tradeDetails['ourAddress']
    hex_private_key = walletDetails['secretKey']
    recipient_address = tradeDetails['sellerAddress']
    amount_to_send = tradeDetails["tradeAmount"] 

    log_message(f"Initiating transaction for Trade ID: {tradeId}", log_file)
    log_message(f"Sender: {walletDetails['publicKey']}, Recipient: {recipient_address}, Amount: {amount_to_send} USDT", log_file)

    response = send_transaction(hex_private_key, recipient_address, amount_to_send, log_file)
    log_message(f"Transaction response: {response}", log_file)
