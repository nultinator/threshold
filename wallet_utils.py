from hdwallet import HDWallet
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

def get_all_balances():
    config_file = open(".config.json", "r", encoding="UTF-8")
    jsoninfo = json.load(config_file)
    config_file.close()
    addresses = jsoninfo["addresses"]
    address_balances = {}
    for key, address in addresses.items():
        info = blockexplorer.get_address(address)
        balance = (info.chain_stats["funded_txo_sum"])/100_000_000
        address_balances[address] = balance
    return address_balances