"""
This can help when something goes wrong while releasing of payment automatically.


"""

import dotenv

from imports.utils import decrypt_text

# Example usage with your wallet data
dotenv.load_dotenv()
wallet = {"tradeId": "TXID697326283290", "memonic": "CZ3ZZtP+wjTK2ROT91aqqbe9hjxGK7dYK0gGOa2jCjLwZj1CXYLZYklU2+2BqZ9/4dJvR8o2LRJCf0c8sZ5JROnZlMpspy8uij9dafhNdGOlQNtw5mEl0A4z+bE=", "secretKey": "lq4RjrWXt5YWye/zn+YX6m7uCgUD/DzWRhFPmZ4mw2ZSKOi8WVPnBxtgTm7MCwwasQeJksY9up0+RSsWj0V2F38JvcKrjgdlERLasn7uIIM=", "publicKey": "FD2DPpy5Rm7oxyHPonH9yA4R5HJwLQFF5i1TQQKDVUM1", "currency": "SOL", "tradeType": "futures", "__time_added": 1725771844}

print(decrypt_text(wallet['memonic']))
print(decrypt_text(wallet['secretKey']))
