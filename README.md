# Crypto Escrow Telegram Bot
 This python written bot acts as mediator between a product seller and buyer in telegram. It holds Crypto in its wallet and release payment to seller upon both party's approval

![License](https://img.shields.io/badge/license-MIT-blue) ![Python](https://img.shields.io/badge/Python-v3.9.8-blue)

## Features
Users can use /escrow command and bot will generates a wallet which receives funds for parties and hold it until both are satisfied.

Users can steup their shop items which can have automatic or manual key/product delivery system, and release the funds to seller after Delivery automatically

The crypto wallets are generated and stored in mysql database in encrypted state, does not depend on any other external service to manage wallets

Supported Networks: Solana, Litecoin, Dogecoin

Networks to be added: Binance Smart Chain

The reason bitcoin will not be added is because of huge fee and slow time.

I am open for discussions on which networks to add.

## Installation
Needs [Python version 3.9.8](https://www.python.org/downloads/release/python-398/) to be installed

1. Clone the repository:
   ```bash
   git clone https://github.com/glazybyte/Crypto-Escrow-Telegram-Bot.git
   ```
2. Navigate to the project directory:
   ```bash
   cd Crypto-Escrow-Telegram-Bot
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Install a extra library
   ```bash
   pip install solathon==1.0.2
   ```

5. edit .env.example:

   Get bot token from [Botfather](https://t.me/BotFather)
   Get Blockcypher api Key from [here](https://accounts.blockcypher.com/)
   PRIVATE_KEY and SOLANA_FEE_PAYER_SECRET are generated upon first run be sure to save these values safely
   ```python
   BOT_TOKEN = '73777777:jFc4Tvs0bM' # Get this from Bot Father
   BLOCK_CYPHER_API_TOKEN = '' # Free one works just fine | Will be used to push doge and ltc transactions
   PRIVATE_KEY='not_set'
   SOLANA_FEE_PAYER_SECRET = 'not_set' #used to pay tx fee for USDT, receives 2% of amount in turn
   ```
   Add Mysql Database Credentials
   ```Python
   #MYSQL credential below 
   ENABLEDB = True
   HOST = "192.168.29.69"
   PORT = 33042
   USER = "root"
   PASSWORD = "cnOlZnSgv"
   DATABASE = "cryptoescrow"
   ```

6. Mysql Setup
    Using phpmyadmin or mysql terminal run the commands in db.sql to create tables

7. Start the bot
    Rename '.env.example' to '.env' and you are good to go for starting the bot
   ```bash
   python escrowBot.py
   ```
## Donation Section?! Damnn

BTC: bc1q2zlqujfvrauvge8t33wtm6xp4akuw5u0l9jn34

BSC: 0xFB96DA72ecF2382b562219545CC8329823e119fA

SOL: 54QdnQKAY1QbPZAfAn3YCnYLNuJVTgyArLvPGUB8X7Ag
