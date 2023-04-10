from hdwallet import HDWallet, BIP44HDWallet
from hdwallet.utils import generate_entropy
from hdwallet.symbols import BTC, BTCTEST
from typing import Optional
import json
import requests
from os import path
from bloxplorer import bitcoin_explorer, bitcoin_testnet_explorer

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
    loads["children"] = []
    return loads

#Generates child wallets based on the root xpublic key
def getnewaddress(wallet: dict):
    symbol = wallet["symbol"]
    seed_phrase = wallet["mnemonic"]
    pubkey = wallet["root_xpublic_key"]
    index = len(wallet["children"])
    print("Current children:", index)
    hdwallet: HDWallet = BIP44HDWallet(symbol=symbol)
    hdwallet.from_xpublic_key(xpublic_key=pubkey)
    hdwallet.from_index(LEGACY)
    hdwallet.from_index(0)
    hdwallet.from_index(0)
    hdwallet.from_index(0)
    hdwallet.from_index(index+1)
    dumps = json.dumps(hdwallet.dumps(), indent=4, ensure_ascii=False)
    loads = json.loads(dumps)
    address = loads["addresses"]["p2pkh"]
    if address not in wallet["children"]:
        return address
    else:
        return "Address already in wallet... We may have a bug"

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
#Retrieve a balance...Children supported, testnet not supported yet
def getbalance(address: str):
    if address[0:3] == "bc1" or address[0] == "1" or address[0] == "3":
        return bitcoin_explorer.addr.get(address).data["chain_stats"]["funded_txo_sum"]/100_000_000
    elif address[0:3] == "tb1" or address[0] =="m" or address[0] == "n" or address[0] == "2":
        return bitcoin_testnet_explorer.addr.get(address).data["chain_stats"]["funded_txo_sum"]/100_000_000
    else:
        return "address {} not a valid BTC or BTCTEST address".format(address)

def getwalletbalance(wallet: dict):
    sum: float = 0
    #create an addresses list
    addresses = []
    #add addresses from the parent wallet to the addresses list
    for address in wallet["addresses"].values():
        addresses.append(address)
    #add child wallets to the addresses list
    for receiving_address in wallet["children"]:
        addresses.append(receiving_address)
        amount: float = getbalance(address)
        print(receiving_address, amount, wallet["symbol"])
        sum += amount
    #return the total balance
    return sum

def is_testnet(address: str):
    if address[0:3] == "tb1" or address[0] == "m" or address[0] == "n" or address[0] == "2":
        return True

def is_mainnet(address: str):
    if address[0:3] == "bc1" or address[0] == "1" or address[0] == "3":
        return True

def listunspent(address: str):
    if is_testnet(address):
        return bitcoin_testnet_explorer.addr.get_utxo(address).data
    elif is_mainnet(address):
        return bitcoin_explorer.addr.get_utxo(address).data
    else:
        return "Address {} not valid".format(address)