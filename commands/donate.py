from telegram import Update
from telegram.ext import CallbackContext
import re

from imports.utils import escape_markdown_v2

def execute(update: Update, context: CallbackContext, bot_state) -> None:
    addresses = {
        "SOLANA": bot_state.config.get("solana_donor_address", ""),
        "BSC": bot_state.config.get("bsc_donor_address", ""),
        "BITCOIN": bot_state.config.get("bitcoin_donor_address", ""),
        "SOLANA (Duplicate Key)": bot_state.config.get("bot_state.config['solana_donor_address']", "")
    }
    
    valid_addresses = {k: v for k, v in addresses.items() if v}
    
    if valid_addresses:
        message = "OHH? What a generous person we have here\!\n\n"
        message += "\n".join(
            f"{escape_markdown_v2(k)}: `{escape_markdown_v2(v)}`" for k, v in valid_addresses.items()
            #f"{escape_markdown_v2(k)}: [Copy Address](https://example.com/{escape_markdown_v2(v)})" for k, v in valid_addresses.items()
           #f"{escape_markdown_v2(k)}: [Click to Copy](https://t.me/share/text?url={escape_markdown_v2(v)})" for k, v in valid_addresses.items()
            

        )
    else:
        message = "No donor addresses are currently available."
    print(message)
    update.message.reply_text(message, parse_mode="MarkdownV2")

description = "Donate for good work"
aliases = ['/donate', '/sex']
enabled = False
hidden = True
OperaterCommand = False
