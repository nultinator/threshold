import json
import wallet_utils

from bitcoinutils.setup import setup
from bitcoinutils.utils import to_satoshis
from bitcoinutils.transactions import Transaction, TxInput, TxOutput
from bitcoinutils.keys import P2pkhAddress, PrivateKey, P2wpkhAddress
from bitcoinutils.script import Script
from bloxplorer import bitcoin_explorer, bitcoin_testnet_explorer

from operator import itemgetter

def get_fees(network):
    if network == "mainnet":
        return bitcoin_explorer.fees.get_estimates().data["1"]
    elif network == "testnet":
        return bitcoin_testnet_explorer.fees.get_estimates().data["1"]
    else:
        print("An error occured, network not supported")



##Get a list of all spendable UTXOs from a parent wallet and its children
def get_all_outputs(wallet: dict):
    #declare an empty list for addresses to check
    addresses = []
    #declare an empty list where we can add spendable UTXOs
    spendable = []
    #check the parent wallet for UTXOs and add them to the list
    for address in wallet["addresses"].values():
        utxos = wallet_utils.listunspent(address)
        for utxo in utxos:
            #add private key for signing transactions
            utxo["signing_key"] = wallet["private_key"]
            spendable.append(utxo)
    #check our receiving children for spendable UTXOs and add them to the list
    for child in wallet["receiving"]:
        for address in child["addresses"].values():
            utxos = wallet_utils.listunspent(address)
            for utxo in utxos:
                #add private key for signing transactions
                utxo["signing_key"] = child["private_key"]
                spendable.append(utxo)
    #check our change children for spendable UTXOs and add the to the list
    for child in wallet["change"]:
        for address in child["addresses"].values():
            utxos = wallet_utils.listunspent(address)
            for utxo in utxos:
                #add private key for signing transactions
                utxo["signing_key"] = child["private_key"]
                spendable.append(utxo)
    #once we've counted all the spendable UTXOs, return the list
    return spendable

def createrawtransaction(wallet: dict):
    #get our spendable coins
    outputs = get_all_outputs(wallet)
    #allow the user to decide which ones to spend
    inputs = input_selector(outputs)
    #print the coins that we're about to spend
    print("You chose the following UTXOS")
    print(inputs)
    #We'll build the unsigned transaction here
    #Afterward, we'll sign it here
    #Then we'll submit to the network
    
#Takes a list of UTXOs and returns a list of UTXOs to be used in a new transaction
def input_selector(tx_array):
    #building is our miniture runtime loop
    building: bool = True
    #we dislay a selector next to each UTXO so the user can add to the list easily
    selector: int = 0
    #the list of UTXOs to be used in a new transaction
    spends = []
    while building:
        #Display the selector, txid, and the value of each UTXO
        print("Available UTXOs")
        for tx in tx_array:
            btcvalue = tx["value"]/100_000_000
            print(selector, tx["txid"], tx["value"], "sat", btcvalue, "BTC")
            selector += 1
        #user selects the utxo to use here
        resp: int = int(input())
        selection = tx_array[resp]
        print("You selected", selection)
        #add the selected utxo to our "spends list"
        spends.append(selection)
        #remove it from the list of available utxos in "tx_array"
        tx_array.pop(resp)
        #reset the selector before we display the mutated tx_array
        selector = 0
        if len(tx_array) == 0:
            #no coins left to spend, exit the loop
            building = False
        else:
            print("Would you like to add another UTXO? Y/n")
            resp: str = input()
            if resp.lower() == "n" or len(tx_array) == 0:
                #user does not wish to spend anymore coins, exit the loop
                building = False
            else:
                print(spends)
                continue
    #return the list
    return spends