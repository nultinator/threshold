import json
import wallet_utils



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
        print("Would you like to select another output? Y/n")
        resp = input()
        if resp.lower() == "n":
            building_tx = False
    else:
        print("No spendable Mainnet coins")

    if len(outputs["testnet"]) > 0:
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
                        print(key, value)
            print("Selector:", selector)
            selector += 1
        print("Please select an output")
        resp = int(input())
        print("You selected", outputs["testnet"][resp])
        print("Would you like to add another output? Y/n")
        resp = input()
        if resp.lower() == "n":
            building_tx = False
    else:
        print("No spendable Testnet coins")
        

