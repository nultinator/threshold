from hdwallet import HDWallet
from hdwallet.utils import generate_entropy
from hdwallet.symbols import BTC as SYMBOL
from typing import Optional
import json
import requests
from blockstream import blockexplorer

#256 represents a 24 word seed phrase, less strength means less words... pretty simple
STRENGTH: int = 256
ENTROPY: str = generate_entropy(strength=STRENGTH)

hdwallet: HDWallet = HDWallet(symbol=SYMBOL, use_default_path=False)

hdwallet.from_entropy(
    entropy=ENTROPY, language="english", passphrase=""
)

LEGACY: int = 44

SEGWIT_P2SH: int = 49

SEGWIT_NATIVE: int = 84

hdwallet.from_index(LEGACY, hardened=True)
hdwallet.from_index(0, hardened=True)
hdwallet.from_index(0, hardened=True)

hdwallet.from_index(0)
hdwallet.from_index(0)

dumps = json.dumps(hdwallet.dumps(), indent=4, ensure_ascii=False)

loads = json.loads(dumps)



symbol = loads["symbol"]
network = loads["network"]
wif = loads["wif"]
addresses = loads["addresses"]
p2pkh = addresses["p2pkh"]
p2sh = addresses["p2sh"]
p2wpkh = addresses["p2wpkh"]
p2wpkh_in_p2sh = addresses["p2wpkh_in_p2sh"]
p2wsh = addresses["p2wsh"]
p2wsh_in_p2sh = addresses["p2wsh_in_p2sh"]


##################TESTS###################
#test coin and network
assert symbol == "BTC"
assert network == "mainnet"

#private keys begin with K, L, or 5
assert wif[0] == "K" or wif[0] == "L" or wif[0] == "5"


print("Testing address prefixes")
#legacy p2pkh addresses begin with 1
assert p2pkh[0] == "1"
#legacy p2sh addresses begin with 3
assert p2sh[0] == "3"

#pay to witness pubkey hash begins with bc1
assert p2wpkh[0:3] == "bc1"
#segwit p2pkh in p2sh begins with 3... Legacy p2sh addresss
assert p2wpkh_in_p2sh[0] == "3"
#pay to witness script hash begins with bc1
assert p2wsh[0:3] == "bc1"
#pay to witness script hash in p2sh begins with 3... Legacy p2sh addresss
assert p2wsh_in_p2sh[0] == "3"
print("Prefix tests: passed")

print("Testing address length")
assert len(p2pkh) >=26 and len(p2pkh) <= 36
assert len(p2sh) == 34
assert len(p2wpkh) == 42
assert len(p2wsh) == 62
print("Address length: passed")


print("Satoshi balance test")
SATOSHI = "1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa"
address = blockexplorer.get_address(SATOSHI)
print("Satoshi's Address", SATOSHI, "INFO")
balance = (address.chain_stats["funded_txo_sum"])/100_000_000
sat_balance = address.chain_stats["funded_txo_sum"]
print("Balance", balance)
print("Balance in SATS", sat_balance)
assert balance != 0
print("Satoshi's Balance: PASSED")


print("UTXO Test")
outputs = blockexplorer.get_address_transactions(SATOSHI)
for output in outputs:
    Dict = output.serialized()
    print(output.id)
    print(output.vout[0]["value"], "sats")
    print(output.vout[0]["value"]/100_000_000, "BTC")
assert type(outputs) == list
print("UTXO Test: PASSED")


print("ALL TESTS PASSED")