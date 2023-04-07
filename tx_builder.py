import json
import wallet_utils

from bitcoinutils.setup import setup
from bitcoinutils.utils import to_satoshis
from bitcoinutils.transactions import Transaction, TxInput, TxOutput
from bitcoinutils.keys import P2pkhAddress, PrivateKey
from bitcoinutils.script import Script




def get_all_outputs(wallet: dict):
    #add addresses from the parent wallet to the addresses list
    addresses = []
    spendable_mainnet = []
    spendable_testnet = []
    mainnet_sum = 0
    testnet_sum = 0
    return_dict = {}
    for address in wallet["addresses"].values():
        addresses.append(address)
    if "children" in wallet.keys():
        print("child wallets detected")
        for child_wallet in wallet["children"]:
            addresses.append(child_wallet)
    for address in addresses:
        balance = wallet_utils.getbalance(address)
        if balance >= 0:
            if wallet_utils.is_testnet(address):                    
                testnet_sum += float(balance)
                utxos = wallet_utils.listunspent(address)
                if len(utxos) > 0:
                    spendable_testnet.append(utxos)
            else:
                mainnet_sum += float(balance)
                utxos = wallet_utils.listunspent(address)
                if len(utxos) > 0:
                    spendable_mainnet.append(utxos)
        else:
            continue
    return_dict["mainnet"] = spendable_mainnet
    return_dict["testnet"] = spendable_testnet
    return return_dict

def createrawtransaction(wallet: dict):
    building_tx: bool = True
    outputs = get_all_outputs(wallet)
    print(outputs)
    if len(outputs["mainnet"]) > 0:
        print("Spendable Mainnet Coins")
        tx_out = []
        while building_tx and len(outputs["mainnet"] > 0):
            selector = 0
            for tx in outputs["mainnet"]:
                for note in tx:
                    for key, value in note.items():
                        if key == "txid":
                            print(key, value)
                        if key == "vout":
                            print(key, value)
                        if key == "value":
                            print(key, value)
                print("Selector:", selector)
                selector += 1
                print("Please select an output")
                resp = int(input())
                print("You selected", outputs["mainnet"][resp])
                choice = outputs["mainnet"][resp]
                tx_out.append(choice)
                outputs["mainnet"].pop(resp)
                if len(outputs["mainnet"]) > 0:
                    print("Would you like to select another output? Y/n")
                    resp = input()
                    if resp.lower() == "n":
                        ####build the transaction####
                        #when finished building, exit the loop
                        building_tx = False
                else:
                    ####build the transaction####
                    #when finished building, exit the loop
                    building_tx = False
    else:
        print("No spendable Mainnet coins")

    if len(outputs["testnet"]) > 0:
        tx_out = []
        while building_tx and len(outputs["testnet"]) > 0:
            print("Spendable Testnet Coins")
            selector = 0
            for tx in outputs["testnet"]:
                for note in tx:
                    for key, value in note.items():
                        if key == "txid":
                            print(key, value)
                        if key == "vout":
                            print(key, value)
                        if key == "value":
                            btc_value = str(value/100_000_000)
                            print(key, value, "sat", "("+btc_value, "BTC)")
                print("Selector:", selector)
                selector += 1
            print("Please select an output")
            resp = int(input())
            print("You selected", outputs["testnet"][resp])
            choice = outputs["testnet"][resp]
            tx_out.append(choice)
            outputs["testnet"].pop(resp)
            print("Currently using", tx_out)
            if len(outputs["testnet"]) > 0:
                print("Would you like to add another output? Y/n")
                resp = input()
                if resp.lower() == "n":
                    ####build the transaction####
                    #when finished building, exit the loop
                    building_tx = False
            else:
                ####build the transaction####
                #when finished building, exit the loop
                building_tx = False
    else:
        print("No spendable Testnet coins")
        

