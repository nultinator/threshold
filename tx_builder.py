import json
import wallet_utils

from bitcoinutils.setup import setup
from bitcoinutils.utils import to_satoshis
from bitcoinutils.transactions import Transaction, TxInput, TxOutput
from bitcoinutils.keys import P2pkhAddress, PrivateKey, P2wpkhAddress
from bitcoinutils.script import Script
from bitcoinutils.constants import SIGHASH_ALL, SIGHASH_ANYONECANPAY


from bloxplorer import bitcoin_explorer, bitcoin_testnet_explorer

from operator import itemgetter

#Get the estimated fee (sat/vbyte) on the current network
def get_fees(network):
    #if we are on mainnet, use the mainnet explorer
    if network == "mainnet":
        #return the 1 block fee rate for transaction, we don't wanna wait
        return bitcoin_explorer.fees.get_estimates().data["1"]
    #if we are on testnet, use the testnet explorer
    elif network == "testnet":
        #return the 1 block fee rate for transaction, we don't wanna wait
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
            utxo["signing_key"] = wallet["wif"]
            spendable.append(utxo)
    #check our receiving children for spendable UTXOs and add them to the list
    for child in wallet["receiving"]:
        for address in child["addresses"].values():
            utxos = wallet_utils.listunspent(address)
            for utxo in utxos:
                #add private key for signing transactions
                utxo["signing_key"] = child["wif"]
                spendable.append(utxo)
    #check our change children for spendable UTXOs and add the to the list
    for child in wallet["change"]:
        for address in child["addresses"].values():
            utxos = wallet_utils.listunspent(address)
            for utxo in utxos:
                #add private key for signing transactions
                utxo["signing_key"] = child["wif"]
                spendable.append(utxo)
    #once we've counted all the spendable UTXOs, return the list
    return spendable
#Initial attempt at raw transactions, currently unused, will probably get removed
def createrawtransaction(wallet: dict):
    network: str = wallet["network"]
    if network == "mainnet":
        explorer = bitcoin_explorer
    elif network == "testnet":
        explorer = bitcoin_testnet_explorer
    setup(network)
    #get our spendable coins
    outputs: list = get_all_outputs(wallet)
    print("Please enter an address to send to")
    to_address: str = input()
    max_avail = wallet_utils.getwalletbalance(wallet)
    print("How much would you like to send? Max:", max_avail)
    amount = float(input())
    while amount > max_avail:
        print("Amount higher than balance, please try again")
        amount = float(input())
    #allow the user to decide which ones to spend
    inputs: list = input_selector(outputs)
    #print the coins that we're about to spend
    print("You chose the following UTXOS")
    print(inputs)
    spending = []
    outs = []
    for utxo in inputs:
        wif: str = utxo.get("signing_key")
        priv_key: PrivateKey = PrivateKey(wif=wif)
        print("Signing key: ", priv_key)
        pubkey = priv_key.get_public_key()
        print("Pubkey: ", pubkey)
        from_address = pubkey.get_segwit_address()
        value = utxo.get("value")
        txid = utxo.get("txid")
        vout = utxo.get("vout")
        print("TXINFO")
        print("txid: ", txid)
        print("vout: ", vout)
        print("value: ", value)
        txin = TxInput(txid, vout)
        spending.append(txin)
        toAddress = P2wpkhAddress(to_address)
        script_code = Script(["OP_DUP", "OP_HASH160", pubkey.to_hash160(),
                            "OP_EQUALVERIFY", "OP_CHECKSIG"])
        txout = TxOutput(to_satoshis(amount), toAddress.to_script_pub_key())
        outs.append(txout)
        tx = Transaction(spending, outs, has_segwit=True)

        print("\nRaw transaction:\n" + tx.serialize())

        sig = priv_key.sign_segwit_input(tx, vout, script_code, value)

        tx.witnesses.append(Script([sig, pubkey.to_hex()]))

        print("\nSigned transaction:\n" + tx.serialize())

        print("\nTxid:\n" + tx.get_txid())

        attempt = explorer.tx.post(tx.serialize())

    print(attempt.data)



    #get and print the current feerate
    fee: int = get_fees(network)
    

    #We'll build the unsigned transaction here
    #Afterward, we'll sign it here
    #Then we'll submit to the network

def multi_input_transaction(wallet: dict):
    #figure out which network we're using
    network: str = wallet["network"]
    if network == "mainnet":
        #mainnet block explorer
        explorer = bitcoin_explorer
    elif network == "testnet":
        #testnet block explorer
        explorer = bitcoin_testnet_explorer
    setup(network)
    Segwit: bool = False
    Legacy: bool = False
    if wallet["path"][0:5] == "m/84'":
        Segwit: bool = True
    elif wallet["path"][0:5] == "m/44'":
        Legacy: bool = True
    else:
        print("Wallet type not supported")
    #get our spendable coins
    outputs: list = get_all_outputs(wallet)
    print("Please enter an address to send to")
    #Get the address to send to
    to_address: str = input()
    #show the maximum amount (i.e. wallet balance)
    max_avail = wallet_utils.getwalletbalance(wallet)
    print("How much would you like to send? Max:", max_avail)
    #user decides how much to send
    amount = float(input())
    #while our amount is greater than our balance, try again
    while amount > max_avail:
        print("Amount higher than balance, please try again")
        amount = float(input())
    #allow the user to decide which ones to spend
    inputs: list = input_selector(outputs)
    #print the coins that we're about to spend
    print("You chose the following UTXOS")
    print(inputs)
    #create a list of UTXOs going into the transaction
    spending = []
    #create a list of outputs for the transaction
    outs = []
    #create a list of private keys to sign with
    keys = []
    #create a list of values to sign (Corresponds with our "spending list")
    values = []
    #full value of the transaction before the UTXOs are added
    funded_value: int = 0
    #iterate through our inputs
    for utxo in inputs:
        #get the WIF for each UTXO
        wif: str = utxo.get("signing_key")
        #add it to the list of keys
        keys.append(wif)
        #get the value, txid and vout of each UTXO
        value = utxo.get("value")
        txid = utxo.get("txid")
        vout = utxo.get("vout")
        #display each coin going into the transaction
        print("TXINFO")
        print("txid: ", txid)
        print("vout: ", vout)
        print("value: ", value)
        #add the value to our total funded value
        funded_value += value
        #add the value to our values list
        values.append(value)
        #create the input
        txin = TxInput(txid, vout)
        #add the input to our spending list
        spending.append(txin)
    #Create a SegWit Address object from the receiving address
    if to_address[0] == "1" or to_address[0] == "m" or to_address[0] == "n":
        toAddress = P2pkhAddress(to_address)
    else:
        toAddress = P2wpkhAddress(to_address)
    #Create the output for the address
    txout = TxOutput(to_satoshis(amount), toAddress.to_script_pub_key())
    #instantiate the transaction
    tx = Transaction(spending, outs, has_segwit=True)
    #add the output to our list of outs
    outs.append(txout)
    #show the current size of the transaction
    print("SIZE:", tx.get_size())
    #get the current fee rate
    feerate: float = get_fees(network)
    #estimate the fee per input
    estimated_fee: int = (feerate * tx.get_size())
    #if the estimated fee is too low, bring it to 150 sat per input
    if estimated_fee < 110:
        estimated_fee = 150
    if Legacy:
        estimated_fee = estimated_fee * 1.75
    #update the fee by the amount of inputs
    estimated_fee = estimated_fee * len(inputs)
    print("Estimatedfee:", estimated_fee)
    #Calculate the change left over
    change: int = int(funded_value - to_satoshis(amount) - estimated_fee)
    print("Change:", change)
    #create an unused address for the change
    if Segwit:
        changeAddress = P2wpkhAddress(wallet_utils.getchangeaddress(wallet)["addresses"]["p2wpkh"])
    elif Legacy:
        changeAddress = P2pkhAddress(wallet_utils.getchangeaddress(wallet)["addresses"]["p2pkh"])
    print("Change:", changeAddress.to_string(), change)
    #create an output for the change
    changeout = TxOutput(change, changeAddress.to_script_pub_key())
    #add the output to our outs list
    outs.append(changeout)
    #update the transaction
    tx = Transaction(spending, outs, has_segwit=True)
    #This is where it gets interesting
    #enumerate through the list of coins we're spending    
    for i, utxo in enumerate(spending):
        #find the corresponding private key in the keys list
        wif = keys[i]
        #turn in into a PrivateKey object
        priv_key = PrivateKey(wif=wif)
        #get the pubkey from the private key
        pubkey = priv_key.get_public_key()
        #sign the UTXO and the corresponding value in the values list
        if Segwit:
            sig = priv_key.sign_segwit_input(tx, i, Script([
                "OP_DUP", "OP_HASH160", pubkey.to_hash160(),
                "OP_EQUALVERIFY", "OP_CHECKSIG"])
            , values[i])
            #This is SegWit, you have to add a witness to the signature
            tx.witnesses.append(Script([sig, pubkey.to_hex()]))
        elif Legacy:
            from_addr = P2pkhAddress(pubkey.get_address().to_string())
            sig = priv_key.sign_input(tx, i, Script([
                "OP_DUP", "OP_HASH160", from_addr.to_hash160(),
                "OP_EQUALVERIFY", "OP_CHECKSIG"]))
            pk = pubkey.to_hex()
            utxo.script_sig = Script([sig, pk])
    #Now that we're done building the transaction, print the hex
    print("\nSigned transaction:\n" + tx.serialize())
    #Calculate and show the txid
    print("\nTxid:\n" + tx.get_txid())
    #Submit the transaction to the network through the block explorer
    attempt = explorer.tx.post(tx.serialize())
    #Print the response, IT SHOULD BE EXACTLY THE SAME AS THE TXID ABOVE
    #If not, we have a problem
    print(attempt.data)

#Sendmany function --Unfinished, this will be the equivalent of the full node "sendmany" rpc
#ideally, user inputs an amount and a list of addresses, the function does the rest
def sendmany(wallet: dict):
    #figure out which network we're using
    network: str = wallet["network"]
    if network == "mainnet":
        #mainnet block explorer
        explorer = bitcoin_explorer
    elif network == "testnet":
        #testnet block explorer
        explorer = bitcoin_testnet_explorer
    setup(network)
    SegWit: bool = False
    Legacy: bool = False
    if wallet["path"][0:5] == "m/84'":
        SegWit: bool = True
        print("Segwit enabled")
    elif wallet["path"][0:5] == "m/44'":
        Legacy: bool = True
        print("Legacy enabled")
    else:
        print("Wallet type not supported")
    #get our spendable coins
    outputs: list = get_all_outputs(wallet)
    print("Please enter an address to send to")
    #Get the address to send to
    to_address: str = input()
    #show the maximum amount (i.e. wallet balance)
    max_avail = wallet_utils.getwalletbalance(wallet)
    print("How much would you like to send? Max:", max_avail)
    #user decides how much to send
    amount = float(input())
    #while our amount is greater than our balance, try again
    while amount > max_avail:
        print("Amount higher than balance, please try again")
        amount = float(input())
    #allow the user to decide which ones to spend
    #print the coins that we're about to spend
    #create a list of UTXOs going into the transaction
    spending = []
    #create a list of outputs for the transaction
    outs = []
    #create a list of private keys to sign with
    keys = []
    #create a list of values to sign (Corresponds with our "spending list")
    values = []
    #full value of the transaction before the UTXOs are added
    funded_value: int = 0
    while funded_value < to_satoshis(amount):
    #iterate through our inputs
        for utxo in outputs:
            #get the WIF for each UTXO
            wif: str = utxo.get("signing_key")
            #add it to the list of keys
            keys.append(wif)
            #get the value, txid and vout of each UTXO
            value = utxo.get("value")
            txid = utxo.get("txid")
            vout = utxo.get("vout")
            #display each coin going into the transaction
            print("TXINFO")
            print("txid: ", txid)
            print("vout: ", vout)
            print("value: ", value)
            #add the value to our total funded value
            funded_value += value
            #add the value to our values list
            values.append(value)
            #create the input
            txin = TxInput(txid, vout)
            #add the input to our spending list
            spending.append(txin)
    #Create a SegWit Address object from the receiving address
    if to_address[0] == "1" or to_address[0] == "m" or to_address[0] == "n":
        toAddress = P2pkhAddress(to_address)
        txout = TxOutput(to_satoshis(amount), toAddress.to_script_pub_key())
    else:
        toAddress = P2wpkhAddress(to_address)
        txout = TxOutput(to_satoshis(amount), toAddress.to_script_pub_key())
    #Create the output for the address
    #txout = TxOutput(to_satoshis(amount), toAddress.to_script_pub_key())
    #instantiate the transaction
    tx = Transaction(spending, outs, has_segwit=True)
    #add the output to our list of outs
    outs.append(txout)
    #show the current size of the transaction
    print("SIZE:", tx.get_size())
    #get the current fee rate
    feerate: float = get_fees(network)
    #estimate the fee per input
    estimated_fee: int = (feerate * tx.get_size())
    #if the estimated fee is too low, bring it to 150 sat per input
    if estimated_fee < 110:
        estimated_fee = 150
    if Legacy:
        estimated_fee = estimated_fee * 1.75
    #update the fee by the amount of inputs
    estimated_fee = estimated_fee * len(spending)
    print("Estimatedfee:", estimated_fee)
    #Calculate the change left over
    change: int = int(funded_value - to_satoshis(amount) - estimated_fee)
    print("Change:", change)
    #create an unused address for the change
    if SegWit:
        changeAddress = P2wpkhAddress(wallet_utils.getchangeaddress(wallet)["addresses"]["p2wpkh"])
        print("Change:", changeAddress.to_string(), change)
    elif Legacy:
        changeAddress = P2pkhAddress(wallet_utils.getchangeaddress(wallet)["addresses"]["p2pkh"])
        print("Change:", changeAddress.to_string(), change)
    else:
        print("Unsupported Change Address")
    #create an output for the change
    changeout = TxOutput(change, changeAddress.to_script_pub_key())
    #add the output to our outs list
    outs.append(changeout)
    #update the transaction
    tx = Transaction(spending, outs, has_segwit=True)
    #This is where it gets interesting
    #enumerate through the list of coins we're spending    
    for i, utxo in enumerate(spending):
        #find the corresponding private key in the keys list
        wif = keys[i]
        #turn in into a PrivateKey object
        priv_key = PrivateKey(wif=wif)
        #get the pubkey from the private key
        pubkey = priv_key.get_public_key()
        #sign the UTXO and the corresponding value in the values list
        if SegWit:
            sig = priv_key.sign_segwit_input(tx, i, Script([
                "OP_DUP", "OP_HASH160", pubkey.to_hash160(),
                "OP_EQUALVERIFY", "OP_CHECKSIG"])
            , values[i])
            #This is SegWit, you have to add a witness to the signature
            tx.witnesses.append(Script([sig, pubkey.to_hex()]))
        elif Legacy:
            from_addr = P2pkhAddress(pubkey.get_address().to_string())
            sig = priv_key.sign_input(tx, i, Script([
                "OP_DUP", "OP_HASH160", from_addr.to_hash160(),
                "OP_EQUALVERIFY", "OP_CHECKSIG"]))
            pk = pubkey.to_hex()
            utxo.script_sig = Script([sig, pk])
    #Now that we're done building the transaction, print the hex
    print("\nSigned transaction:\n" + tx.serialize())
    #Calculate and show the txid
    print("\nTxid:\n" + tx.get_txid())
    #Submit the transaction to the network through the block explorer
    attempt = explorer.tx.post(tx.serialize())
    #Print the response, IT SHOULD BE EXACTLY THE SAME AS THE TXID ABOVE
    #If not, we have a problem
    print(attempt.data)
    
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
        print("Please select from your available UTXOs")
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
