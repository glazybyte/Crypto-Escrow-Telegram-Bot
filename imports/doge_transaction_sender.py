import hashlib, os, base58, traceback
from blockcypher import create_unsigned_tx, make_tx_signatures, broadcast_signed_transaction
from blockcypher.api import get_address_full
from ecdsa import SECP256k1, SigningKey
from decimal import Decimal, ROUND_DOWN
from imports.utils import log_message

# Function to convert a hex private key to WIF format
def hex_to_wif(hex_key, compressed=True):
    extended_key = 'c0' + hex_key  # 0xc0 is the Dogecoin mainnet prefix
    if compressed:
        extended_key += '01'
    first_sha256 = hashlib.sha256(bytes.fromhex(extended_key)).hexdigest()
    second_sha256 = hashlib.sha256(bytes.fromhex(first_sha256)).hexdigest()
    checksum = second_sha256[:8]
    final_key = extended_key + checksum
    wif = base58.b58encode(bytes.fromhex(final_key)).decode('utf-8')
    return wif

# Function to get the public key from a private key in hex format
def privkey_to_pubkey(hex_key):
    priv_key = SigningKey.from_string(bytes.fromhex(hex_key), curve=SECP256k1)
    pub_key = priv_key.get_verifying_key().to_string('compressed').hex()
    return pub_key


def send_doge_transaction(doge_address, doge_private_key_hex, recipient_address, amount_to_send, api_token):
    # Create log directory if it doesn't exist
    log_file = doge_address

    try:
        # Generated wallet details
        #doge_private_key_wif = hex_to_wif(doge_private_key_hex)
        doge_public_key_hex = privkey_to_pubkey(doge_private_key_hex)

        # Define the recipient address and amount
        amount_to_send = Decimal(amount_to_send) * Decimal('1e8')  # In DOGE
        amount_to_send_satoshis = int(amount_to_send.quantize(Decimal('1'), rounding=ROUND_DOWN))  # Convert to satoshis
        print(amount_to_send_satoshis)
        fee = 0.2  # In DOGE
        fee_satoshis = int(fee * 1e8)  # Convert to satoshis
        
        amount_to_send_satoshis = amount_to_send_satoshis - fee_satoshis

        log_message(f"Sending {str(amount_to_send_satoshis)} Satoshi with fee of {str(fee_satoshis)}", log_file)

        # Fetch UTXO details for the address
        address_details = get_address_full(address=doge_address, coin_symbol='doge', api_key=api_token)
        utxos = []

        # Extract UTXOs from txs
        for tx in address_details['txs']:
            for idx, output in enumerate(tx['outputs']):
                if doge_address in output['addresses']:
                    utxos.append({
                        'tx_hash': tx['hash'],
                        'tx_output_n': idx,
                        'value': output['value']
                    })

        # Select the first UTXO for simplicity
        utxo = utxos[0]
        txid = utxo['tx_hash']
        vout = utxo['tx_output_n']
        value = utxo['value']  # In satoshis

        log_message(f"UTXO value: {value}", log_file)

        if value < amount_to_send_satoshis + fee_satoshis:
            raise Exception('Insufficient funds')

        # Calculate change amount
        change_amount_satoshis = value - (amount_to_send_satoshis + fee_satoshis)

        # Create an unsigned transaction
        inputs = [{'address': doge_address}]
        outputs = [{'address': recipient_address, 'value': amount_to_send_satoshis}]
        if change_amount_satoshis > 0:
            outputs.append({'address': doge_address, 'value': change_amount_satoshis})

        unsigned_tx = create_unsigned_tx(inputs=inputs, outputs=outputs, coin_symbol='doge', api_key=api_token)
        unsigned_tx['tx']['preference'] = 'low'
        unsigned_tx['tx']['fees'] = fee_satoshis
        unsigned_tx.pop("errors")
        log_message(f"Unsigned TX: {unsigned_tx}", log_file)

        # Sign the transaction
        privkey_list = [doge_private_key_hex]
        pubkey_list = [doge_public_key_hex]
        tx_signatures = make_tx_signatures(txs_to_sign=unsigned_tx['tosign'], privkey_list=privkey_list, pubkey_list=pubkey_list)
        #tx_signatures[0] = tx_signatures[0] + '01'

        log_message(f"Signed signatures: {tx_signatures}", log_file)
        
        # Broadcast the signed transaction
        log_message("Broadcasting TX", log_file)
        response = broadcast_signed_transaction(unsigned_tx=unsigned_tx, signatures=tx_signatures, pubkeys=pubkey_list, coin_symbol='doge', api_key=api_token)

        log_message(f'Transaction hash: {response["tx"]["hash"]}', log_file)
        log_message(f"Transaction Push Response: {response}", log_file)

    except Exception as e:
        error_message = f"An error occurred: {str(e)}\n{traceback.format_exc()}"
        log_message(error_message, log_file)
        raise

def send_transaction(bot_state, tradeId):

    # Extract trade and wallet details
    tradeDetails = bot_state.get_var(tradeId)
    walletDetails = bot_state.get_wallet_info(tradeId)

    # Source Escrow Wallet Details
    doge_address = walletDetails["publicKey"]
    doge_private_key_hex = walletDetails["secretKey"]

    # To Wallet 
    recipient_address = tradeDetails['sellerAddress']
    amount_to_send = tradeDetails["tradeAmount"]  # String

    send_doge_transaction(doge_address, doge_private_key_hex, recipient_address, amount_to_send, os.getenv('BLOCK_CYPHER_API_TOKEN'))


