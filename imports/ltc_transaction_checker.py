import requests
def ltcTransactionChecker(publicKey):
    url = f"https://litecoinspace.org/api/address/{publicKey}/txs"

    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            txs = response.json()

            if isinstance(txs, list) and len(txs) > 0:
                latest_tx = txs[0]
                vouts = latest_tx.get('vout', [])
                amount_received = 0

                # Find outputs belonging to this address
                for vout in vouts:
                    if vout.get('scriptpubkey_address') == publicKey:
                        amount_received = vout.get('value', 0)  # in satoshis
                        amount_received_ltc = amount_received / 1e8
                        break

                if amount_received > 0:
                    status = latest_tx.get('status', {})
                    confirmed = status.get('confirmed', False)
                    txid = latest_tx.get('txid', '')

                    if confirmed:
                        return [
                            {
                                "code": "confirmed",
                                "amount": amount_received_ltc,
                                "publicKey": publicKey
                            },
                            f"https://litecoinspace.org/tx/{txid}"
                        ]
                    else:
                        return [
                            {
                                "code": "unconfirmed",
                                "amount": amount_received_ltc,
                                "publicKey": publicKey
                            },
                            ""
                        ]
                else:
                    return [
                        {"code": "undetected", "publicKey": publicKey},
                        ""
                    ]
            else:
                return [
                    {"code": "undetected", "publicKey": publicKey},
                    ""
                ]
        else:
            return [
                {
                    "code": "error",
                    "message": f"Failed to retrieve data. Status code: {response.status_code}",
                    "publicKey": publicKey
                },
                ""
            ]

    except Exception as e:
        return [
            {
                "code": "error",
                "message": f"An error occurred: {e}",
                "publicKey": publicKey
            },
            ""
        ]
