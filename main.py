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
        #Add it to the memory
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
    print("1 Create/Restore Wallet")
    print("2 Check Address balances")
    print("3 Remove a Wallet")
    print("4 Block Explorer")
    print("5 Generate Receiving Address")
    print("6 Send a transaction")
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
        #user chooses the currency
        print("Please enter a ticker name, examples: BTC, BTCTEST")
        ticker: str = input().upper()
        print("Restore from seed phrase? (Leave blank to generate a new one)")
        mnemonic: str = input()
        #Choose derivation
        print("Is this a Legacy wallet?")
        resp: str = input()
        if resp.lower() == "y":
            derivation = 44
        else:
            derivation = 84
        #create the wallet
        new_wallet = wallet_utils.new_wallet(ticker, mnemonic, derivation)
        #add the wallet to our existing wallets
        wallets[name] = wallet_utils.create_wallet_set(new_wallet)
        print(new_wallet)
        #save the wallet file
        config_file = open(".config.json", "w")
        config_file.write(json.dumps(wallets))
        config_file.close()
    #Fetch balances through API
    elif resp == 2:
        print("Wallets")
        for key, value in wallets.items():
            #Print the wallet name
            print(key)
            total_balance: float = wallet_utils.getwalletbalance(value)
            #Display the total balance
            print("Total Balance", total_balance, value["symbol"])
    #Create a testnet wallet
    elif resp == 3:
        print("Remove a wallet")
        print("Please enter the name off the wallet you wish to remove")
        for key in wallets.keys():
            print(key)
        resp: str = input()
        wallets.pop(resp)
        config_file = open(".config.json", "w")
        config_file.write(json.dumps(wallets))
        config_file.close()
    #Restore a wallet from seed phrase
    elif resp == 4:
        print("Block Explorer")
        print("What would you like to do?")
        print("0 Get an unconfirmed balance")
        print("1 Lookup a transaction")
        resp: int = int(input())
        if resp == 0:
            print("Please enter an address")
            address: str = input()
            print(wallet_utils.getpendingbalance(address))
        elif resp == 1:
            print("Please enter a txid")
            txid: str = input()
            print("Is this a testnet transaction?")
            resp: str = input()
            if resp.lower() == "y":
                network = "testnet"
            else:
                network = "testnet"
            print(tx_builder.get_tx(txid, network))
    #Generate Child Wallets
    elif resp == 5:
        print("Generate Receiving Address")
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
    #Create a transaction
    elif resp == 6:
        print("Send a transaction")
        print("Please select a wallet")
        selector: int = 0
        #List the user's wallets and each network that the wallet is on
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
        print("PLease select an option below")
        #Build the transaction automatically
        print("0 Simple Send")
        #Allow theuser to build the transaction manually
        print("1 Raw Transaction Builder (Not Recommended)")
        resp: int = int(input())
        if resp == 0:
            #Follow "Simple Send" protocol (build transaction automatically)
            print(tx_builder.sendmany(choice))
        elif resp == 1:
            #User creates the transaction manually
            tx_builder.multi_input_transaction(choice)
        else:
            print("Choice not supported")
        #The code below is a bug fix, we already created the change address, but didn't save it
        #Create the address again
        change = wallet_utils.getchangeaddress(choice)
        #Add it to the parent wallet
        choice["change"].append(change)
        #Save the wallet file
        config_file = open(".config.json", "w")
        config_file.write(json.dumps(wallets))
        config_file.close()
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
        #Display the experimental features
        print("Available Features:")
        print("1 Unconfirmed Balance")
        print("2 Get fee estimates")
        print("3 Get transaction")
        print("4 Remove a Wallet")
        print("5 Non-interactive Send")
        print("6 Create unsigned transaction")
        resp: int = int(input())
        if resp == 1:
            #Get pending balance
            print("Please enter an address")
            resp: str = input()
            #Send the query to the block explorer and print the result
            print(wallet_utils.getpendingbalance(resp))
        elif resp == 2:
            print("Please select a network")
            print("1 Mainnet")
            print("2 Testnet")
            resp: int = int(input())
            #Print the mainnet feerate
            if resp == 1:
                print(tx_builder.get_fees("mainnet"), "sat/vb")
            #Print the testnet feerate
            elif resp == 2:
                print(tx_builder.get_fees("testnet"), "sat/vb")
            else:
                print("Network not valid")
        elif resp == 3:
            print("Is this a testnet transaction? Y/n")
            resp: str = input()
            if resp.lower() == "y":
                network = "testnet"
            else:
                network = "mainnet"
            print("Please enter a txid")
            resp: str = input()
            print(tx_builder.get_tx(resp, network))
        elif resp == 4:
            print("Remove a wallet")
            print("Please enter the name off the wallet you wish to remove")
            for key in wallets.keys():
                print(key)
            resp: str = input()
            wallets.pop(resp)
            config_file = open(".config.json", "w")
            config_file.write(json.dumps(wallets))
            config_file.close()
        elif resp == 5:
            print("Please enter the name of the wallet you wish to send from")
            wallet: str = input()
            available: float = wallet_utils.getwalletbalance(wallets[wallet])
            print("How much coin do you wish to send? Max:", available)
            amount: float = float(input())
            print("Please enter the address you wish to send to")
            to_address: str = input()
            print("Result")
            attempt = tx_builder.non_interactive_send(wallets[wallet], amount, to_address)
            print(attempt)

            change_wallet = wallet_utils.getchangeaddress(wallets[wallet])
            wallets[wallet]["change"].append(change_wallet)
            config_file = open(".config.json", "w")
            config_file.write(json.dumps(wallets))
            config_file.close()
        elif resp == 6:
            print("Please select a wallet")
            resp: str = input()
            wallet = wallets[resp]
            print("Please enter an address to send to")
            to_address: str = input()
            print("Please enter an amount to send")
            amount: float = float(input())
            print(tx_builder.create_unsigned_tx(wallet, amount, to_address))
        else:
            print("Sorry, your choice is not valid")
    else:
        print("Please select a valid choice")

