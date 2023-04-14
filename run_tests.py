
from typing import Optional
import json
import requests
from bloxplorer import bitcoin_explorer, bitcoin_testnet_explorer
import wallet_utils



def runtests():
    test_mainnet()

########BTC MAINNET TESTS#############
#256 represents a 24 word seed phrase, less strength means less words... pretty simple
def test_mainnet():
    print("Beginning Mainnet Tests")
    seed_phrase = "spin gadget swap shadow always casual dream clarify hour benefit sustain eternal brand rack infant dream crash adjust patch eagle mouse actor brick royal"
    wallet = wallet_utils.restore_wallet(seed_phrase)

    
    assert wallet_utils.is_mainnet(wallet["addresses"]["p2wpkh"])
    print("SEGWIT NATIVE PREFIXES: PASSED")


    assert wallet["addresses"]["p2wpkh"] == "bc1qmf5vg7zfhmg23aye66g4pmpa75ngyc39wuzqfe"
    print("WALLET RESTORE: PASSED")

    child = wallet_utils.gethardaddress(wallet)
    assert child["addresses"]["p2wpkh"] == "bc1qxh703wa3u5cj6amjzdl490s23ymqau3t23upn5"
    print("RECEIVING ADDRESS DERIVATION: PASSED")

    changewallet = wallet_utils.getchangeaddress(wallet)
    assert changewallet["addresses"]["p2wpkh"] == "bc1qt090r23jjsryv8mcneg53lhtqhm63wc6sduxp7"
    print("CHANGE ADDRESS DERIVATION: PASSED")


##################TESTS###################
#test coin and network

