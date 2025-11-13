import base64
import base58, traceback, os
from solathon.core.instructions import transfer
from solathon import Client, Transaction, PublicKey, Keypair
from decimal import Decimal
from globalState import GlobalState
from imports.utils import log_message
from solana.constants import SYSTEM_PROGRAM_ID
from solathon.core.instructions import Instruction, AccountMeta
import struct

log_file = ''

def sol_to_lamports(sol_amount_str):
    """Convert SOL string amount to lamports (int)."""
    sol_amount = Decimal(sol_amount_str)
    return int(sol_amount * Decimal(1_000_000_000))

def is_account_initialized(client: Client, pub_key):
    """Check if a Solana account exists and is initialized."""
    try:
        account_info = client.get_account_info(pub_key)
        if account_info is None or "error" in account_info:
            return False
        balance = account_info.get("lamports", 0)
        return balance > 0
    except Exception:
        return False

def send_transaction(hex_private_key, recipient_address, sol_amount_str, log_file, tradeDetails, fee_payer_private_key):
    try:
        client = Client("https://api.mainnet-beta.solana.com")
        RENT_EXEMPT_BALANCE = client.get_minimum_balance_for_rent_exemption(0)

        brokerAddress = tradeDetails['brokerAddress'] if tradeDetails.get('brokerTrade') else None

        # Escrow wallet (sender)
        private_key_base58 = base58.b58encode(bytes.fromhex(hex_private_key)).decode('utf-8')
        keypair = Keypair.from_private_key(private_key_base58)

        # Fee wallet
        fee_wallet_key_base58 = base58.b58encode(bytes.fromhex(fee_payer_private_key)).decode('utf-8')
        fee_wallet_keypair = Keypair.from_private_key(fee_wallet_key_base58)

        # Convert fees and trade amount
        our_fee = sol_to_lamports(tradeDetails.get('fee', '0'))
        broker_fee = sol_to_lamports(tradeDetails.get('broker_fee', '0'))
        sol_amount_str = Decimal(sol_amount_str)
        requested_amount = sol_to_lamports(sol_amount_str)

        # Check sender balance
        sender_balance = client.get_balance(keypair.public_key)
        if sender_balance <= 0:
            raise ValueError("Wallet balance is empty.")

        # Safety buffer
        FEE_BUFFER = 10_000  # ~0.00001 SOL

        # Ensure we leave rent exempt balance
        available_to_spend = sender_balance - (RENT_EXEMPT_BALANCE + FEE_BUFFER)
        if available_to_spend <= 0:
            raise ValueError("Not enough funds after reserving rent exemption and network fee.")

        # Calculate total transfer requirements
        total_required = our_fee + broker_fee + requested_amount

        if total_required > available_to_spend:
            # Reduce the recipient amount if total fees exceed available balance
            requested_amount = max(0, available_to_spend - (our_fee + broker_fee))
            log_message("Adjusted transfer amount to preserve rent exemption.", log_file)

        instructions = []

        # Developer fee
        if our_fee > 0:
            instructions.append(
                transfer(
                    from_public_key=keypair.public_key,
                    to_public_key=fee_wallet_keypair.public_key,
                    lamports=our_fee
                )
            )

        # Broker fee (if applicable)
        actual_broker_fee = 0
        if broker_fee > 0 and brokerAddress:
            broker_acc_initialized = is_account_initialized(client, PublicKey(brokerAddress))
            actual_broker_fee = broker_fee if broker_acc_initialized else max(broker_fee, RENT_EXEMPT_BALANCE)
            instructions.append(
                transfer(
                    from_public_key=keypair.public_key,
                    to_public_key=PublicKey(brokerAddress),
                    lamports=actual_broker_fee
                )
            )

        # Recipient transfer (respect rent exemption)
        remaining_balance = client.get_balance(keypair.public_key)
        drainable_amount = remaining_balance - (RENT_EXEMPT_BALANCE + FEE_BUFFER + our_fee + actual_broker_fee)

        if drainable_amount <= 0:
            raise ValueError("Insufficient funds to send after leaving rent exemption balance.")

        instructions.append(
            transfer(
                from_public_key=keypair.public_key,
                to_public_key=PublicKey(recipient_address),
                lamports=drainable_amount
            )
        )

        # Build and send transaction
        transaction = Transaction(instructions=instructions, signers=[keypair])
        result = client.send_transaction(transaction)
        return result

    except Exception as e:
        error_message = f"An error occurred: {str(e)}\n"
        error_message += ''.join(traceback.format_exception(None, e, e.__traceback__))
        log_message(error_message, log_file)
        return None


def simple_sol_to_sol_transaction(action_id, bot_state: GlobalState):
    tradeDetails = {}
    if action_id.startswith('TRADE'):
        tradeDetails = bot_state.get_var(action_id)
    elif action_id.startswith('TXID'):
        tradeDetails = bot_state.get_tx_var(action_id)
    walletDetails = bot_state.get_wallet_info(action_id)

    log_file = tradeDetails['ourAddress']
    hex_private_key = walletDetails['secretKey']
    recipient_address = tradeDetails['sellerAddress']
    amount_to_send = tradeDetails["tradeAmount"] 
    
    log_message(f"Initiating transaction for Trade ID: {action_id}", log_file)
    log_message(f"Sender: {walletDetails['publicKey']}, Recipient: {recipient_address}, Amount: {amount_to_send} USDT", log_file)

    response = send_transaction(
        hex_private_key,
        recipient_address,
        amount_to_send,
        log_file,
        tradeDetails,
        os.getenv('SOLANA_FEE_PAYER_SECRET')
    )

    log_message(f"Transaction response: {response}", log_file)
