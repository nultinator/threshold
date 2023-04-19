####THIS FILE GENERATES ELECTRUM COMPATIBLE SEEDS AND KEYS CREATE A BACKUP BEFORE CHANGING####


from hdwallet import HDWallet
from hdwallet.utils import generate_entropy
from typing import Optional
import json
import requests
from os import path
from blockstream import blockexplorer
import qrcode
import io

import wallet_utils
import tx_builder
import run_tests


#We are not running yet, only enter runtime if the user chooses to
running: bool = False


print("Welcome to Threshold Wallet")
print("Checking for config file")

#Instantiate an empty dict, We'll load our wallets into this variable
wallets: dict = {}
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
    response: str = input()
    if response.lower() == "y":
        print("Please select an option below")
        print("1 Create a new wallet")
        print("2 Restore a wallet")
        #user may enter either a '1' or a '2'
        resp: int = int(input())
        if resp == 1:
            #create a new wallet
            new_wallet: dict = wallet_utils.create_wallet()
        elif resp == 2:
            print("Please enter a private key or seed phrase")
            resp: str = input()
            #restore an existing wallet
            new_wallet: dict = wallet_utils.restore_wallet(resp)
        else:
            #Invalid input, make the user try again
            print("Not a valid response, please try again")
            print("1 Create a new wallet")
            print("2 Restore a wallet")
            resp: int = int(input)
        #open the wallet file
        config_file = open(".config.json", "w")
        print("Please name your wallet")
        #give the wallet a name
        name: str = input()
        wallets[name] = new_wallet
        #save the wallet file
        config_file.write(json.dumps(wallets))
        config_file.close()
        #Set config to true so we are not stuck in the setup loop
        config = True
#Ask the user if they'd like to run in interactive mode
print("Would you like to run the wallet in interactive mode? Y/n")
resp: str = input()
#If user says yes, begin runtime loop
if resp.lower() == "y":
    running: bool = True
#Retrieve the total balance
print("Fetching balance")
for key, value in wallets.items():
    #print the wallet name
    print(key)
    #get the total balance
    total_balance: float = wallet_utils.getwalletbalance(value)
    #print the balance and the coin ticker
    print("Total Balance", total_balance, value["symbol"])
#Runtime loop...Let the user choose what to do, and then restart the loop
while running:
    print("What would you like to do?")
    print("1 Create a New Wallet")
    print("2 Check Address balances")
    print("3 Create a Testnet Wallet")
    print("4 Restore a Mainnet Wallet")
    print("5 Generate Receiving Address")
    print("6 Send a transaction (Multi_Inputs are Partially working), WARNING: THIS WILL DISPLAY YOUR PRIVATE KEYS")
    print("7 Export Wallet")
    print("8 Run Tests")
    print("9 Quit")
    print("10 Experimental Features")
    resp: int = int(input())
    #Generate a wallet
    if resp == 1:
        print("Generating addresses")
        print("Please choose a name for your new wallet")
        #user gives the wallet a name
        name: str = input()
        new_wallet: dict = wallet_utils.create_wallet()
        #add the wallet to our existing wallets
        wallets[name] = new_wallet
        print(wallets)
        #save the wallet file
        config_file = open(".config.json", "w")
        config_file.write(json.dumps(wallets))
        config_file.close()
    #Fetch balances/UTXOS through API
    elif resp == 2:
        print("Wallets")
        for key, value in wallets.items():
            print(key)
            total_balance: float = wallet_utils.getwalletbalance(value)
            print("Total Balance", total_balance, value["symbol"])
    #Create a testnet wallet
    elif resp == 3:
        print("Generate a testnet wallet")
        print("Please enter a name for your wallet")
        name: str = input()
        #append the wallet name with '_TESTNET'
        walletname: str = "{}_TESTNET".format(name)
        print(walletname)
        #ask if the user wants to create from a seed phrase
        print("Create from seed phrase? Y/n")
        resp: str = input()
        if resp.lower() == "y":
            #create from seed phrase
            print("Please input a seed phrase")
            seed_phrase: str = input()
            test_wallet: dict = wallet_utils.seed_testnet_wallet(seed_phrase)
        else:
            #default to building a new wallet
            test_wallet: dict = wallet_utils.create_testnet_wallet()
        #Save wallet to the wallet file
        wallets[walletname] = test_wallet
        config_file = open(".config.json", "w")
        config_file.write(json.dumps(wallets))
        config_file.close()
        print("You can fund your new testnet wallet at one of the addresses below")
        #tell the user where to find testnet bitcoin
        print("https://bitcoinfaucet.uo1.net/send.php")
        print("https://testnet-faucet.com/btc-testnet/")
    #Restore a wallet from seed phrase
    elif resp == 4:
        print("Fetching Wallet Info")
        print("Please enter your private key or seed phrase:")
        # have the user enter either a seed phrase, private key, or WIF private key
        key: str = input()
        #rebuild the wallet from the user's restore keys
        wallet: dict = wallet_utils.restore_wallet(key)
        print("Please give your wallet a name")
        name: str = input()
        wallets[name] = wallet
        #Save the wallet file
        config_file = open(".config.json", "w")
        config_file.write(json.dumps(wallets))
        config_file.close()
    #Generate Child Wallets
    elif resp == 5:
        print("Generate Reciving Address")
        print("Please choose one of the wallets below")
        #have the user select a wallet
        for wallet in wallets.keys():
            print("Wallet name:", wallet)
        resp: str = input()
        #if they select an invalid wallet, try again until they get it right
        while resp not in wallets.keys():
            print("The wallet you chose does not exist. Please eneter a valid wallet name")
            for wallet in wallets.keys():
                print("Wallet name:", wallet)
            resp: str = input()
        print("You selected:", resp)
        #find the specified wallet in memory
        wallet = wallets[resp]
        print("Is this a Change Address? Y/n")
        resp: str = input()
        #if we are creating a change address, create a change wallet
        if resp.lower() == "y":
            child: dict = wallet_utils.getchangeaddress(wallet)
            #add the child to our list of change wallets
            wallet["change"].append(child)
        #If not, default to a new receiving wallet
        else:
            child: dict = wallet_utils.gethardaddress(wallet)
            #add the wallet to our listof receiving wallets
            wallet["receiving"].append(child)
        config_file = open(".config.json", "w")
        config_file.write(json.dumps(wallets))
        config_file.close()
        #get all valid payment addresses from the new wallet
        for address in child["addresses"].values():
            #print the address
            print(address)
            #ask the user to display it as a qr code
            print("Display as QR? Y/n")
            resp: str = input()
            #if the user elects to, display the address qr code
            if resp.lower() == "y":
                print("Creating QR Code")
                qr = qrcode.QRCode()
                qr.add_data(address)
                f = io.StringIO()
                qr.print_ascii(out=f)
                f.seek(0)
                print(f.read())
    #create a transaction####NOT WORKING########
    elif resp == 6:
        print("Send a transaction")
        print("Please select a wallet")
        selector: int = 0
        for walletname, walletinfo in wallets.items():
            network: str = walletinfo["network"]
            print(selector, walletname,"--"+network)
            selector += 1
        print("Please enter the name of the wallet you wish to use")
        #user chooses a wallet to transact from
        resp: str = input()
        #find the wallet in memory
        choice = wallets[resp]
        #attempt to build a transaction
        tx_builder.multi_input_transaction(choice)
    #Export Wallet
    elif resp == 7:
        print("Exporting Wallet")
        print("Please select a wallet")
        #user enters an existing wallet name
        for wallet in wallets:
            print(wallet)
        resp: str = input()
        #if user enters an invalid wallet name, mke them try again until they get it
        while resp not in wallets:
            print("Please choose a valid wallet")
            for wallet in wallets:
                print(wallet)
            resp: str = input()
        #find the wallet in memory
        wallet = wallets[resp]
        print("Seed Phrase:")
        #display the seed phrase as text
        print(wallet["mnemonic"])
        #display it as a qr code as well
        seed_qr = qrcode.QRCode()
        seed_qr.add_data(wallet["mnemonic"])
        f = io.StringIO()
        seed_qr.print_ascii(out=f)
        f.seek(0)
        print(f.read())
        print("WIF Private Key:")
        #display the WIF private key as text
        print(wallet["wif"])
        #display it as a qr code as well
        wif_qr = qrcode.QRCode()
        wif_qr.add_data(wallet["wif"])
        f = io.StringIO()
        wif_qr.print_ascii(out=f)
        f.seek(0)
        print(f.read())
    #Run the tests
    elif resp == 8:
        run_tests.runtests()
    #Terminate the program
    elif resp == 9:
        print("Terminating Program")
        #change the running boolean to false and exit program
        running: bool = False
    elif resp == 10:
        print("Available Features:")
        print("1 Unconfirmed Balance (not working)")
        print("2 Get fee estimates")
        resp: int = int(input())
        if resp == 1:
            print("Please enter an address")
            resp: str = input()
            print(wallet_utils.getpendingbalance(resp))
        elif resp == 2:
            print("Please select a network")
            print("1 Mainnet")
            print("2 Testnet")
            resp: int = int(input())
            if resp == 1:
                print(tx_builder.get_fees("mainnet"), "sat/vb")
            elif resp == 2:
                print(tx_builder.get_fees("testnet"), "sat/vb")
            else:
                print("Network not valid")
        else:
            print("Sorry, your choice is not valid")
    else:
        print("Please select a valid choice")

