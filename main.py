####THIS FILE GENERATES ELECTUM COMPATIBLE SEEDS AND KEYS CREATE A BACKUP BEFORE CHANGING####


from hdwallet import HDWallet
from hdwallet.utils import generate_entropy
from hdwallet.symbols import BTC as SYMBOL
from typing import Optional
import json
import requests
from os import path
from blockstream import blockexplorer
import wallet_utils

STRENGTH: int = 256
ENTROPY: str = generate_entropy(strength=STRENGTH)

hdwallet: HDWallet = HDWallet(symbol=SYMBOL, use_default_path=False)

hdwallet.from_entropy(
    entropy=ENTROPY, language="english", passphrase=""
)


LEGACY: int = 44

SEGWIT_P2SH: int = 49

SEGWIT_NATIVE: int = 84

running = False

print("Welcome to Threshold Wallet")
print("Checking for config file")

config = path.isfile(".config.json")
while not config:
    print("No config file found")
    print("Would you like to create one? Y/n")
    response = input()
    if response.lower() == "y":
        config_file = open(".config.json", "w")
        config_file.close()
        config = True


print("Would you like to run the wallet in interactive mode? Y/n")
resp = input()

if resp.lower() == "y":
    running = True


while running:
    print("What would you like to do?")
    print("1 Generate Addresses")
    print("2 Check balances")
    print("3 Restore a Wallet")
    print("4 Quit")
    resp = int(input())
    if resp == 1:
        print("Please enter a name for your wallet")
        name = input()
        print("Generating addresses")
        wallet = wallet_utils.create_wallet()
        wallet["name"] = name
        config_file = open(".config.json", "a")
        config_file.write(json.dumps(wallet))
        config_file.close()
    elif resp == 2:
        print("Wallets")
        balances = wallet_utils.get_all_balances()
        for k,v in balances.items():
            print(k, v)
        print("Would you like to see the UXTOs? Y/n")
        resp = input()
        if resp.lower() == "y":
            print("Fetching UTXOs")
            for k in balances:
                UTXOs = blockexplorer.get_address_transactions(k)
                for UTXO in UTXOs:
                    Dict = UTXO.serialized()
                    print(UTXO.id, UTXO.vout[0]["value"], "sats")
    elif resp == 3:
        wallet = open(".config.json", "r", encoding="UTF-8")
        print("Fetching Wallet Info")
        print("Please enter your private key or seed phrase:")
        key = input()
        wallet_utils.restore_wallet(key)
    elif resp == 4:
        print("Terminating Program")
        running = False
    else:
        print("Please select a valid choice")

