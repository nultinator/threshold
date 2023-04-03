from hdwallet import HDWallet, BIP44HDWallet
from hdwallet.utils import generate_entropy
from hdwallet.symbols import BTC as SYMBOL
from typing import Optional
import json
import requests
from os import path
from blockstream import blockexplorer

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

def restore_wallet(restore_keys: str):
    hdwallet: HDWallet = HDWallet(symbol=SYMBOL)
    length = len(restore_keys)
    if length == 64:
        hdwallet.from_private_key(private_key=restore_keys)
    
    elif restore_keys[0] == "K" or restore_keys[0] == "L" or restore_keys[0] == "5":
        hdwallet.from_wif(wif=restore_keys)
    else:
        hdwallet = BIP44HDWallet(symbol=SYMBOL)
        hdwallet.from_mnemonic(mnemonic=restore_keys)
    return hdwallet.dumps()

def get_all_balances(wallets: dict):
    print("Fetching balances")
    address_balances = {}
    addresses = []
    for wallet in wallets.values():
        for address in wallet["addresses"].values():
            addresses.append(address)
        for address in addresses:
            info = blockexplorer.get_address(address)
            balance = (info.chain_stats["funded_txo_sum"])/100_000_000
            address_balances[address] = balance
    return address_balances