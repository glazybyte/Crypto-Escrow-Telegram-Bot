from solana.rpc.api import Client
from spl.token.instructions import get_associated_token_address
from solders.pubkey import Pubkey
import base58
from decimal import Decimal
USDT_MINT_ADDRESS = 'Es9vMFrzaCERmJfrF4H2FYD4KCoNkY11McCe8BenwNYB'
def get_finalized_sol_balance(public_address: str, spl_token: str = None) -> float:
    public_key = Pubkey(base58.b58decode(public_address))
    client = Client("https://api.mainnet-beta.solana.com")
    if spl_token:
        mint_pubkey = Pubkey(base58.b58decode(spl_token))
        token_account_pubkey = get_associated_token_address(public_key, mint_pubkey)
        response = client.get_token_account_balance(token_account_pubkey, commitment="finalized")
    else:
        response = client.get_balance(public_key, commitment="finalized")
    amount = 0
    if response and hasattr(response, 'value') and response.value is not None:
        if spl_token:
            if hasattr(response, 'message') and response.message =="Invalid param: could not find account":
                return 0
            else:
                amount = Decimal(response.value.ui_amount_string)
        else:
            amount = (int(response.value) / 10**9)  # Convert lamports to SOL
    else:
        amount = 0  
    return {"publicKey": public_address, "amount": amount}


# Testing
#print(get_finalized_sol_balance("9eeneoxQmxbYFTrffFS5rDz1VsdCpQuzd4D67UNE5D8W", USDT_MINT_ADDRESS))
