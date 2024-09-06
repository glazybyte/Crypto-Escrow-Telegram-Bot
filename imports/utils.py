import re
from decimal import Decimal, InvalidOperation
from concurrent.futures import ThreadPoolExecutor
from telegram.ext import CallbackContext
from telegram.error import BadRequest
from solathon import PublicKey
from base58 import b58decode, b58decode_check
from binascii import Error as BinasciiError
import os, hashlib

def log_message(message, log_file="error_log", mainThread=False):
    log_dir = 'log'
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    
    if mainThread:
        log_file = f'{log_dir}/{log_file}.txt'
    else:
        log_file = f'{log_dir}/wallet_log_{log_file}.txt'

    print(message)
    with open(log_file, 'a') as f:
        f.write(message + '\n')

def validate_text(input_text, extra = []):
    allowed_pattern = r'^[a-zA-Z0-9 ,\-$@.]+$'
    if re.match(allowed_pattern, input_text):
        return True
    else:
        for char in input_text:
            if not re.match(r'[a-zA-Z0-9 ,\-$@.]', char):
                if char not in extra:
                    return f"Illegal character found: '{char}'"
        return True
        #return "Invalid input detected."
def is_number(input_string):
    try:
        # Try converting to an integer
        number = int(input_string)
        return number
    except ValueError:
        try:
            # If not an integer, try converting to a Decimal for precision
            number = Decimal(input_string)
            return number
        except InvalidOperation:
            # If conversion to Decimal fails, it's not a number
            return False

def is_valid_user(input_value, context: CallbackContext):
    try:
        if input_value.isdigit():
            user_chat = context.bot.get_chat(int(input_value))
        else:
            if not input_value.startswith("@"):
                input_value = f"@{input_value}"
            user_chat = context.bot.get_chat(input_value)
        return user_chat.id
    
    except (BadRequest, ValueError):
        return False

def is_address_valid(address: str, symbol: str) -> bool:
    if symbol.upper() == "SOL":
        return is_solana_address_valid(address)
    elif symbol.upper() == "LTC":
        return is_litecoin_address_valid(address)
    elif symbol.upper() == "BSC":
        return validate_bsc_address(address)
    elif symbol.upper() == "DOGE":
        return validate_doge_address(address)
    else:
        return False

def is_solana_address_valid(address: str) -> bool:
    try:
        PublicKey(address)
        return True
    except (ValueError, BinasciiError):
        return False

def is_litecoin_address_valid(address: str) -> bool:
    patterns = [
        r'^[LM][1-9A-HJ-NP-Za-km-z]{26,33}$',  # Legacy (P2PKH)
        r'^3[1-9A-HJ-NP-Za-km-z]{26,33}$',    # SegWit (P2SH)
        r'^ltc1[qpzry9x8gf2tvdw0s3jn54khce6mua7l]{39,59}$'  # Bech32
    ]
    if any(re.match(pattern, address) for pattern in patterns):
        return True
    else:
        return False

def validate_doge_address(address: str) -> bool:
    try:
        decoded = b58decode(address)
        if len(decoded) != 25:
            return False
        payload, checksum = decoded[:-4], decoded[-4:]
        hash1 = hashlib.sha256(payload).digest()
        hash2 = hashlib.sha256(hash1).digest()
        return checksum == hash2[:4]
    except Exception as e:
        return False

def validate_bsc_address(address: str) -> bool:
    if not re.match(r"^0x[a-fA-F0-9]{40}$", address):
        return False
    
    #someone recommended me below 2 line tch
    if address != address.lower() and address != address.upper():
        return is_checksum_valid(address)
    
    return True

def is_checksum_valid(address: str) -> bool:
    address = address.replace('0x', '')
    address_hash = hashlib.sha3_256(address.lower().encode('utf-8')).hexdigest()
    for i in range(40):
        if int(address_hash[i], 16) > 7 and address[i].upper() != address[i]:
            return False
        elif int(address_hash[i], 16) <= 7 and address[i].lower() != address[i]:
            return False
    return True

def multi_task(task_list):
    with ThreadPoolExecutor() as executor:
        futures = []
        for task in task_list:
            fxn = task.pop(0)  
            if type(task[0]).__name__ == 'dict':
                future = executor.submit(fxn, **task[0])
            else:
                future = executor.submit(fxn, *task)
            futures.append(future)

        result = []
        for future in futures:
            response = future.result()
            result.append(response)
    return result
        
