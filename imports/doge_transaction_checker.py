import requests
def dogeTransactionChecker(publicKey):
    url = f"https://api.blockcypher.com/v1/doge/main/addrs/{publicKey}/full"
    try:
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            if 'txs' in data and len(data['txs']) > 0:
                latest_transaction = data['txs'][0]
                outputs = latest_transaction.get('outputs', [])
                amount_received = 0
                for output in outputs:
                    if publicKey in output.get('addresses', []):
                        amount_received = output.get('value', 0)
                        amount_received_ltc = amount_received / 1e8
                        break
                if amount_received > 0:
                    if latest_transaction.get('confirmations') >= 3:
                        return {"code": "confirmed", "amount": amount_received_ltc , "publicKey": publicKey}
                    else:
                        return {"code": "unconfirmed", "amount": amount_received_ltc , "publicKey": publicKey}
                else:
                    return {"code": "undetected", "publicKey": publicKey}
            else:
                return {"code": "undetected" , "publicKey": publicKey}
        else:
            return {"code": "error", "message": f"Failed to retrieve data. Status code: {response.status_code}" , "publicKey": publicKey}
    except Exception as e:
        return {"code": "error", "message": f"An error occurred: {e}" , "publicKey": publicKey}