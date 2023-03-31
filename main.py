####THIS FILE GENERATES ELECTUM COMPATIBLE SEEDS AND KEYS CREATE A BACKUP BEFORE CHANGING####


from hdwallet import HDWallet
from hdwallet.utils import generate_entropy
from hdwallet.symbols import BTC as SYMBOL
from typing import Optional
import json
import requests
from os import path

STRENGTH: int = 256
ENTROPY: str = generate_entropy(strength=STRENGTH)

hdwallet: HDWallet = HDWallet(symbol=SYMBOL, use_default_path=False)

hdwallet.from_entropy(
    entropy=ENTROPY, language="english", passphrase=""
)


LEGACY: int = 44

SEGWIT_P2SH: int = 49

SEGWIT_NATIVE: int = 84

def create_wallet():
    hdwallet.from_index(LEGACY, hardened=True)
    hdwallet.from_index(0, hardened=True)
    hdwallet.from_index(0, hardened=True)

    hdwallet.from_index(0)
    hdwallet.from_index(0)

    dumps = json.dumps(hdwallet.dumps(), indent=4, ensure_ascii=False)
    loads = json.loads(dumps)
    return loads

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
    print("3 quit")
    resp = int(input())
    if resp == 1:
        print("Please enter a name for your wallet")
        name = input()
        print("Generating addresses")
        wallet = create_wallet()
        wallet["name"] = name
        config_file = open(".config.json", "a")
        config_file.write(json.dumps(wallet))
        config_file.close()
    elif resp == 2:
        config_file = open(".config.json", "r")
        print("Wallets")
        info = config_file
        json = json.load(info)
        config_file.close()
        addresses = json["addresses"]
        for key, address in addresses.items():
            balance = requests.get("https://blockstream.info/api/address/" + address + "/txs").json()
            print(key, ":", str(address), balance)
    elif resp == 3:
        print("Terminating Program")
        running = False
    else:
        print("Please select a valid choice")

