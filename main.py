####THIS FILE GENERATES ELECTRUM COMPATIBLE SEEDS AND KEYS CREATE A BACKUP BEFORE CHANGING####


from hdwallet import HDWallet
from hdwallet.utils import generate_entropy
from hdwallet.symbols import BTC as SYMBOL
from typing import Optional
import json
import requests
from os import path
from blockstream import blockexplorer
import qrcode
import io

import wallet_utils
import testnet
import tx_builder


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

#Instantiate an empty dict, We'll load our wallets into this variable
wallets = {}
#Check to see if we have a proper wallet file
config = path.isfile(".config.json") and path.getsize(".config.json") > 0
#If a wallet file is present, load it into memory
if config:
    wallet_file = open(".config.json", "r")
    existing_wallets = json.load(wallet_file)
    wallets.update(existing_wallets)
#If a wallet file is not present, loop until the user creates one
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
#Ask the user if they'd like to run in interactive mode
print("Would you like to run the wallet in interactive mode? Y/n")
resp = input()
#If user says yes, begin runtime loop
if resp.lower() == "y":
    running = True
#Retrieve the total balance
print("Fetching balance")
for key, value in wallets.items():
    print(key)
    total_balance = wallet_utils.getwalletbalance(value)
    print("Total Balance", total_balance, value["symbol"])
#Runtime loop...Let the user choose what to do, and then restart the loop
while running:
    print("What would you like to do?")
    print("1 Generate Addresses")
    print("2 Check Address balances")
    print("3 Testnet Wallet")
    print("4 Restore Wallet")
    print("5 Generate Receiving Address")
    print("6 Send a transaction (NOT WORKING)")
    print("7 Export Wallet")
    print("8 Run Tests")
    print("9 Quit")
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
        for key, value in wallets.items():
            print(key)
            total_balance = wallet_utils.getwalletbalance(value)
            print("Total Balance", total_balance, value["symbol"])
    #Create a testnet wallet
    elif resp == 3:
        print("Generate a testnet wallet")
        print("Please enter a name for your wallet")
        name = input()
        walletname = "{}_TESTNET".format(name)
        print(walletname)
        test_wallet = testnet.create_testnet_wallet()
        test_wallet["children"] = []
        #Currently, testnet addresses are not saved to the wallet file
        wallets[walletname] = test_wallet
        config_file = open(".config.json", "w")
        config_file.write(json.dumps(wallets))
        config_file.close()
        print("You can fund your new testnet wallet at one of the addresses below")
        print("https://bitcoinfaucet.uo1.net/send.php")
        print("https://testnet-faucet.com/btc-testnet/")
    #Restore a wallet from seed phrase
    elif resp == 4:
        print("Fetching Wallet Info")
        print("Please enter your private key or seed phrase:")
        key = input()
        wallet = wallet_utils.restore_wallet(key)
        print("Please give your wallet a name")
        name = input()
        wallets[name] = wallet
        #Save the wallet file
        config_file = open(".config.json", "w")
        config_file.write(json.dumps(wallets))
        config_file.close()
    #Generate Child Wallets
    elif resp == 5:
        print("Generate Reciving Address")
        print("Please choose one of the wallets below")
        for wallet in wallets.keys():
            print("Wallet name:", wallet)
        resp = input()
        while resp not in wallets.keys():
            print("The wallet you chose does not exist. Please eneter a valid wallet name")
            for wallet in wallets.keys():
                print("Wallet name:", wallet)
            resp = input()
        print("You selected:", resp)
        wallet = wallets[resp]
        address = wallet_utils.gethardaddress(wallet)
        wallet["children"].append(address)
        config_file = open(".config.json", "w")
        config_file.write(json.dumps(wallets))
        config_file.close()
        print(address)
        print("Display as QR? Y/n")
        resp = input()
        if resp.lower() == "y":
            print("Creating QR Code")
            qr = qrcode.QRCode()
            qr.add_data(address)
            f = io.StringIO()
            qr.print_ascii(out=f)
            f.seek(0)
            print(f.read())
    #create a transaction
    elif resp == 6:
        print("Send a transaction")
        print("Please select a wallet")
        selector = 0
        for walletname, walletinfo in wallets.items():
            network = walletinfo["network"]
            print(selector, walletname, network)
            selector += 1
        print("Please enter the name of the wallet you wish to use")
        resp = input()
        choice = wallets[resp]
        tx_builder.createrawtransaction(choice)
    #Export Wallet
    elif resp == 7:
        print("Exporting Wallet")
        print("Please select a wallet")
        for wallet in wallets:
            print(wallet)
        resp = input()
        while resp not in wallets:
            print("Please choose a valid wallet")
            for wallet in wallets:
                print(wallet)
            resp = input()
        wallet = wallets[resp]
        print("Seed Phrase:")
        print(wallet["mnemonic"])
        seed_qr = qrcode.QRCode()
        seed_qr.add_data(wallet["mnemonic"])
        f = io.StringIO()
        seed_qr.print_ascii(out=f)
        f.seek(0)
        print(f.read())
        print("WIF Private Key:")
        print(wallet["wif"])
        wif_qr = qrcode.QRCode()
        wif_qr.add_data(wallet["wif"])
        f = io.StringIO()
        wif_qr.print_ascii(out=f)
        f.seek(0)
        print(f.read())
    #Run the tests
    elif resp == 8:
        testnet.runtests()
    #Terminate the program
    elif resp == 9:
        print("Terminating Program")
        running = False
    else:
        print("Please select a valid choice")

