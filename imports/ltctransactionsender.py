import os
import hashlib
import base58
import traceback
from blockcypher import create_unsigned_tx, make_tx_signatures, broadcast_signed_transaction
from blockcypher.api import get_address_full
from ecdsa import SECP256k1, SigningKey
from decimal import Decimal, ROUND_DOWN
from imports.utils import log_message

def hex_to_wif(hex_key, compressed=True):
    extended_key = 'b0' + hex_key  # 0xb0 is the Litecoin mainnet prefix
    if compressed:
        extended_key += '01'
    first_sha256 = hashlib.sha256(bytes.fromhex(extended_key)).hexdigest()
    second_sha256 = hashlib.sha256(bytes.fromhex(first_sha256)).hexdigest()
    checksum = second_sha256[:8]
    final_key = extended_key + checksum
    wif = base58.b58encode(bytes.fromhex(final_key)).decode('utf-8')
    return wif


def privkey_to_pubkey(hex_key):
    priv_key = SigningKey.from_string(bytes.fromhex(hex_key), curve=SECP256k1)
    pub_key = priv_key.get_verifying_key().to_string('compressed').hex()
    return pub_key

# Logging function to print and save to file

    print(message)
    with open(log_file, 'a') as f:
        f.write(message + '\n')

def send_ltc_transaction(ltc_address, ltc_private_key_hex, recipient_address, amount_to_send, api_token):
    log_file = ltc_address

    try:
       
        ltc_public_key_hex = privkey_to_pubkey(ltc_private_key_hex)

       
        amount_to_send = Decimal(amount_to_send) * Decimal('1e8')  # In LTC
        amount_to_send_satoshis = int(amount_to_send.quantize(Decimal('1'), rounding=ROUND_DOWN))  # Convert to satoshis
        fee = 0.00002  # In LTC
        fee_satoshis = int(fee * 1e8)
        amount_to_send_satoshis = amount_to_send_satoshis - fee_satoshis
        log_message(f"Sending {str(amount_to_send_satoshis)} Satoshi with fee of {str(fee_satoshis)}", log_file)
        address_details = get_address_full(address=ltc_address, coin_symbol='ltc', api_key=api_token)
        utxos = []
        for tx in address_details['txs']:
            for idx, output in enumerate(tx['outputs']):
                if ltc_address in output['addresses']:
                    utxos.append({
                        'tx_hash': tx['hash'],
                        'tx_output_n': idx,
                        'value': output['value']
                    })

        utxo = utxos[0]
        txid = utxo['tx_hash']
        vout = utxo['tx_output_n']
        value = utxo['value']
        log_message(f"UTXO value: {value}", log_file)

        if value < amount_to_send_satoshis + fee_satoshis:
            raise Exception('Insufficient funds')
        change_amount_satoshis = value - (amount_to_send_satoshis + fee_satoshis)
        inputs = [{'address': ltc_address}]
        outputs = [{'address': recipient_address, 'value': amount_to_send_satoshis}]
        if change_amount_satoshis > 0:
            outputs.append({'address': ltc_address, 'value': change_amount_satoshis})
        unsigned_tx = create_unsigned_tx(inputs=inputs, outputs=outputs, coin_symbol='ltc', api_key=api_token)
        unsigned_tx['tx']['preference'] = 'medium'
        unsigned_tx['tx']['fees'] = fee_satoshis
        log_message(f"Unsigned TX: {unsigned_tx}", log_file)
        privkey_list = [ltc_private_key_hex]
        pubkey_list = [ltc_public_key_hex]
        tx_signatures = make_tx_signatures(txs_to_sign=unsigned_tx['tosign'], privkey_list=privkey_list, pubkey_list=pubkey_list)
        tx_signatures[0] = tx_signatures[0] + '01'
        log_message(f"Signed signatures: {tx_signatures}", log_file)
        log_message("Broadcasting TX", log_file)
        response = broadcast_signed_transaction(unsigned_tx=unsigned_tx, signatures=tx_signatures, pubkeys=pubkey_list, coin_symbol='ltc', api_key=api_token)
        log_message(f'Transaction hash: {response["tx"]["hash"]}', log_file)
        log_message(f"Transaction Push Response: {response}", log_file)
    except Exception as e:
        error_message = f"An error occurred: {str(e)}\n{traceback.format_exc()}"
        log_message(error_message, log_file)
        raise



def send_transaction(bot_state, action_id):
    # Extract trade and wallet details
    tradeDetails = {}
    if action_id.startswith('TRADE'):
        tradeDetails = bot_state.get_var(action_id)
    elif action_id.startswith('TXID'):
        tradeDetails = bot_state.get_tx_var(action_id)
    walletDetails = bot_state.get_wallet_info(action_id)

    # Source Escrow Wallet
    ltc_address = walletDetails["publicKey"]
    ltc_private_key_hex = walletDetails["secretKey"]

    # To Wallet 
    recipient_address = tradeDetails['sellerAddress']
    amount_to_send = tradeDetails["tradeAmount"]  # String

    send_ltc_transaction(ltc_address, ltc_private_key_hex, recipient_address, amount_to_send, os.getenv('BLOCK_CYPHER_API_TOKEN'))


