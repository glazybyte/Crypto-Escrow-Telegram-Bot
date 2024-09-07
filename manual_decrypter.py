import dotenv

from imports.utils import decrypt_text

# Example usage with your wallet data
dotenv.load_dotenv()
wallet = {"tradeId": "TRADE458174374973", "memonic": "viyB4GHCuolDuTBBHohafaZH8gOTjmPJBUbK2EFUdhjiqJXyXQdXyey1xX0Y4rpuArqQct31LOgUCe0oRaV+UHhuB1Q+9BVnB8uaYfuo6ejhju5Abxlh0mwNPwGRdtQx", "secretKey": "154eA9mQKmlo9hVfRKOwz3ixhSv5dI8vD4pwGQ0Bzv9okkkEVot4pb5LmxKBFcBlKCsNrbnwQk/zFu6ll7hAyEWpyATM3PQIUJjsDxGUbBA=", "publicKey": "D8S1xrro5y9dhUp7334qnx8rsPsemdwZk2", "currency": "DOGE", "tradeType": "escrow", "__time_added": 1725725938}

print(decrypt_text(wallet['memonic']))
print(decrypt_text(wallet['secretKey']))
