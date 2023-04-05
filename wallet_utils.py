from hdwallet import HDWallet, BIP44HDWallet
from hdwallet.utils import generate_entropy
from hdwallet.symbols import BTC, BTCTEST
from typing import Optional
import json
import requests
from os import path
from blockstream import blockexplorer

#Generate 24 word seed phrases by default
STRENGTH: int = 256
ENTROPY: str = generate_entropy(strength=STRENGTH)

hdwallet: HDWallet = HDWallet(symbol=BTC, use_default_path=False)

hdwallet.from_entropy(
    entropy=ENTROPY, language="english", passphrase=""
)


LEGACY: int = 44

SEGWIT_P2SH: int = 49

SEGWIT_NATIVE: int = 84

#Create a new wallet from entropy
def create_wallet():
    hdwallet.from_index(LEGACY, hardened=True)
    hdwallet.from_index(0, hardened=True)
    hdwallet.from_index(0, hardened=True)

    hdwallet.from_index(0)
    hdwallet.from_index(0)

    dumps = json.dumps(hdwallet.dumps(), indent=4, ensure_ascii=False)
    loads = json.loads(dumps)
    return loads

#Generates child wallets based on the root xpublic key
def generate_children(wallet: dict, amount: int, testnet: bool):
    counter = 0
    if testnet:
        symbol = BTCTEST
    else:
        symbol = BTC
    seed_phrase = wallet["mnemonic"]
    pubkey = wallet["root_xpublic_key"]
    print("Your seed phrase\n" + seed_phrase)
    new_addresses = []
    for new_wallet in range(1, amount+1):
        hdwallet: HDWallet = BIP44HDWallet(symbol=symbol)
        hdwallet.from_xpublic_key(xpublic_key=pubkey)
        hdwallet.from_index(LEGACY)
        hdwallet.from_index(0)
        hdwallet.from_index(0)
        hdwallet.from_index(0)
        hdwallet.from_index(counter)
        dumps = json.dumps(hdwallet.dumps(), indent=4, ensure_ascii=False)
        loads = json.loads(dumps)
        new_addresses.append(loads["addresses"])
        counter += 1
    return new_addresses

#Restore a wallet
def restore_wallet(restore_keys: str):
    hdwallet: HDWallet = HDWallet(symbol=SYMBOL)
    length = len(restore_keys)
    #Restore from a private key
    if length == 64:
        hdwallet.from_private_key(private_key=restore_keys)
    #Restore from a WIF private key
    elif restore_keys[0] == "K" or restore_keys[0] == "L" or restore_keys[0] == "5":
        hdwallet.from_wif(wif=restore_keys)
    #Restore from a seed phrase
    else:
        hdwallet = BIP44HDWallet(symbol=SYMBOL)
        hdwallet.from_mnemonic(mnemonic=restore_keys)
    return hdwallet.dumps()
#Retrieve all balances....DOES NOT SUPPORT CHILD WALLETS YET
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