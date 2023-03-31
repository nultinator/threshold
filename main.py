####THIS FILE GENERATES ELECTUM COMPATIBLE SEEDS AND KEYS CREATE A BACKUP BEFORE CHANGING####


from hdwallet import HDWallet
from hdwallet.utils import generate_entropy
from hdwallet.symbols import BTC as SYMBOL
from typing import Optional
import json

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
print("Would you like to run the wallet in interactive mode? Y/n")
resp = input()

if resp.lower() == "y":
    running = True


while running:
    print("What would you like to do?")
    print("1 Generate Addresses")
    print("2 quit")
    resp = int(input())
    if resp == 1:
        print("Generating addresses")
        print(create_wallet())
    elif resp == 2:
        print("Terminating Program")
        running = False
    else:
        print("Please select a valid choice")

