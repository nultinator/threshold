####THIS FILE GENERATES ELECTUM COMPATIBLE SEEDS AND KEYS CREATE A BACKUP BEFORE CHANGING####


from hdwallet import HDWallet
from hdwallet.utils import generate_entropy
from hdwallet.symbols import BTC as SYMBOL
from typing import Optional
import json
import requests
from os import path
from blockstream import blockexplorer
import wallet_utils
import testnet

STRENGTH: int = 256
ENTROPY: str = generate_entropy(strength=STRENGTH)

hdwallet: HDWallet = HDWallet(symbol=SYMBOL, use_default_path=False)

hdwallet.from_entropy(
    entropy=ENTROPY, language="english", passphrase=""
)


LEGACY: int = 44

SEGWIT_P2SH: int = 49

SEGWIT_NATIVE: int = 84

running = False

print("Welcome to Threshold Wallet")
print("Checking for config file")


wallets = {}


config = path.isfile(".config.json") and path.getsize(".config.json") > 0
if config:
    wallet_file = open(".config.json", "r")
    existing_wallets = json.load(wallet_file)
    wallets.update(existing_wallets)

while not config:
    print("No config file found")
    print("Would you like to create one? Y/n")
    response = input()
    if response.lower() == "y":
        config_file = open(".config.json", "w")
        new_wallet = wallet_utils.create_wallet()
        print("Please name your wallet")
        name = input()
        wallets[name] = new_wallet
        config_file.write(json.dumps(wallets))
        config_file.close()
        config = True


print("Would you like to run the wallet in interactive mode? Y/n")
resp = input()






print("Existing wallets\n", wallets)

if resp.lower() == "y":
    running = True


while running:
    print("What would you like to do?")
    print("1 Generate Addresses")
    print("2 Check balances")
    print("3 Testnet Wallet")
    print("4 Restore Wallet")
    print("5 Generate child wallets")
    print("6 Run Tests")
    print("7 Quit")
    resp = int(input())
    #Generate a wallet
    if resp == 1:
        print("Generating addresses")
        print("Please choose a name for your new wallet")
        name = input()
        new_wallet = wallet_utils.create_wallet()
        wallets[name] = new_wallet
        print(wallets)
        config_file = open(".config.json", "w")
        config_file.write(json.dumps(wallets))
        config_file.close()
    #Fetch balances/UTXOS through API
    elif resp == 2:
        print("Wallets")
        balances = wallet_utils.get_all_balances(wallets)
        for k,v in balances.items():
            print(k, v)
        total_balances = sum(balances.values())
        print("Total: ", total_balances)
        print("Would you like to see the UXTOs? Y/n")
        resp = input()
        if resp.lower() == "y":
            print("Fetching UTXOs")
            for k in balances:
                UTXOs = blockexplorer.get_address_transactions(k)
                for UTXO in UTXOs:
                    Dict = UTXO.serialized()
                    print(UTXO.id, UTXO.vout[0]["value"], "sats")
    #Create a testnet wallet
    elif resp == 3:
        print("Generate a testnet wallet")
        test_wallet = testnet.create_testnet_wallet()
        print(test_wallet)
    #Restore a wallet from seed phrase
    elif resp == 4:
        wallet = open(".config.json", "r", encoding="UTF-8")
        print("Fetching Wallet Info")
        print("Please enter your private key or seed phrase:")
        key = input()
        wallet = wallet_utils.restore_wallet(key)
        print("Please give your wallet a name")
        name = input()
        wallets[name] = wallet
        config_file = open(".config.json", "w")
        config_file.write(json.dumps(wallets))
        config_file.close()
    #Generate Child Wallets
    elif resp == 5:
        print("How many children?")
        amount = int(input())
        print("Please select a network")
        print("1 Mainnet")
        print("2 Testnet")
        network = int(input())
        if network == 2:
            testnet: bool = True
        else:
            testnet: bool = False
        for wallet in wallets.values():
            wallet["children"] = wallet_utils.generate_children(wallet, amount, testnet)
        print(wallets)
        #config_file = open(".config.json", "w")
        #config_file.write(json.dumps(wallets))
        #config_file.close()

    #Run the tests
    elif resp == 6:
        testnet.runtests()
    #Terminate the program
    elif resp == 7:
        print("Terminating Program")
        running = False
    else:
        print("Please select a valid choice")

