from hdwallet import HDWallet
from hdwallet.utils import generate_entropy
from hdwallet.symbols import BTCTEST as SYMBOL
from typing import Optional
import json
import requests
from blockstream import blockexplorer
from bloxplorer import bitcoin_testnet_explorer
import wallet_utils



########BTC TESTNET TESTS#############
#256 represents a 24 word seed phrase, less strength means less words... pretty simple
def runtests():
    #Create a test wallet
    STRENGTH: int = 256
    ENTROPY: str = generate_entropy(strength=STRENGTH)
    hdwallet: HDWallet = HDWallet(symbol=SYMBOL, use_default_path=False)
    hdwallet.from_entropy(entropy=ENTROPY, language="english", passphrase="")
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
    #Assign some variables based on the wallet's json values
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
    assert symbol == "BTCTEST"
    assert network == "testnet"
    #Testnet WIF should begin with either a "9" or a "c"
    assert wif[0] == "9" or wif[0] == "c"
    #Make sure the address prefixes are correct
    print("Testing address prefixes")
    #legacy p2pkh addresses begin with n
    assert p2pkh[0] == "m" or p2pkh[0] == "n"
    #legacy p2sh addresses begin with 2
    assert p2sh[0] == "2"
    #pay to witness pubkey hash begins with tb1
    assert p2wpkh[0:3] == "tb1"
    #segwit p2pkh in p2sh begins with 2... Legacy p2sh addresss
    assert p2wpkh_in_p2sh[0] == "2"
    #pay to witness script hash begins with tb1
    assert p2wsh[0:3] == "tb1"
    #pay to witness script hash in p2sh begins with 2... Legacy p2sh addresss
    assert p2wsh_in_p2sh[0] == "2"
    print("Prefix tests: passed")
    #Ensure the addresses are the proper length
    print("Testing address length")
    assert len(p2pkh) >=26 and len(p2pkh) <= 36
    assert len(p2sh) == 35
    assert len(p2wpkh) == 42
    assert len(p2wsh) == 62
    print("Address length: passed")
    #Now it's time to test the high level function that creates a testnet wallet
    wallet = create_testnet_wallet()
    addresses = wallet["addresses"]
    print(addresses)
    #The test address below has transaction history, we use it to test the Bloxplorer API
    TESTNET_ADDY = bitcoin_testnet_explorer.addr.get("tb1q466msmwslgf6rff0kqtucpwxdpx95h5nndwnz49yqqyaevr3wvhqszyekd").data
    print("Testing tb1q466msmwslgf6rff0kqtucpwxdpx95h5nndwnz49yqqyaevr3wvhqszyekd")
    #test address returned against address given
    assert TESTNET_ADDY["address"] == "tb1q466msmwslgf6rff0kqtucpwxdpx95h5nndwnz49yqqyaevr3wvhqszyekd"
    print("Address = tb1q466msmwslgf6rff0kqtucpwxdpx95h5nndwnz49yqqyaevr3wvhqszyekd: PASSED")
    #this address should transactions
    print(TESTNET_ADDY["chain_stats"]["tx_count"])
    print("Has Transactions: PASSED")
    #this address has a balance
    assert TESTNET_ADDY["chain_stats"]["funded_txo_sum"] != 0
    print("Has balance: PASSED")
    #this address has a history
    tx_history = bitcoin_testnet_explorer.addr.get_tx_history(TESTNET_ADDY["address"])
    #Print the history of the test address
    print(tx_history.data)
    #If we've made it this far without an error, we've passed the tests
    print("ALL TESTS PASSED")

#Create a testnet wallet from entropy
def create_testnet_wallet():
    STRENGTH: int = 256
    ENTROPY: str = generate_entropy(strength=STRENGTH)
    hdwallet: HDWallet = HDWallet(symbol=SYMBOL, use_default_path=False)
    hdwallet.from_entropy(entropy=ENTROPY, language="english", passphrase="")
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
    return loads



