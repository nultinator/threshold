import json
import requests
import wallet_utils

from bitcoinutils.setup import setup
from bitcoinutils.utils import to_satoshis
from bitcoinutils.transactions import Transaction, TxInput, TxOutput, Sequence
from bitcoinutils.keys import P2pkhAddress, PrivateKey, P2wpkhAddress
from bitcoinutils.script import Script
from bitcoinutils.constants import SIGHASH_ALL, SIGHASH_ANYONECANPAY, TYPE_REPLACE_BY_FEE


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
    #Initialze each protocol as a false boolean variable
    Segwit: bool = False
    Legacy: bool = False
    #If the wallet is SegWit, follow SegWit protocol
    if wallet["path"][0:5] == "m/84'":
        Segwit: bool = True
    #If the wallet is Legacy, follow Legacy protocol
    elif wallet["path"][0:5] == "m/44'":
        Legacy: bool = True
    #Let the user know that their wallet is not using a supported protocol
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
        seq = Sequence(TYPE_REPLACE_BY_FEE)
        txin = TxInput(txid, vout, sequence=seq.for_input_sequence())
        #txin.sequence = TYPE_REPLACE_BY_FEE
        #add the input to our spending list
        spending.append(txin)
    #If we're sending to a Legacy address, make a p2pkh object out of it
    if to_address[0] == "1" or to_address[0] == "m" or to_address[0] == "n":
        toAddress = P2pkhAddress(to_address)
    #Otherwise, assume we're sending to a SegWit address
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
    #If this is a legacy transaction, raise our fee by 75% to make sure it gets through
    if Legacy:
        estimated_fee = estimated_fee * 1.75
    #update the fee by the amount of inputs
    estimated_fee = estimated_fee * len(inputs)
    print("Estimatedfee:", estimated_fee)
    print("Would you like to use a custom fee? Y/n")
    resp: str = input()
    if resp.lower() == "y":
        print("Please enter a fee amount (in sats)")
        fee: int = int(input())
        print("Custom fee:", fee)
        estimated_fee = fee
    #Calculate the change left over
    change: int = int(funded_value - to_satoshis(amount) - estimated_fee)
    print("Change:", change)
    #create an unused address for the change
    #Following SegWit protocol, use a Segwit change address
    if Segwit:
        changeAddress = P2wpkhAddress(wallet_utils.getchangeaddress(wallet)["addresses"]["p2wpkh"])
    #Legacy protocol, use a legacy change address
    elif Legacy:
        changeAddress = P2pkhAddress(wallet_utils.getchangeaddress(wallet)["addresses"]["p2pkh"])
    #Tell the user how much change they have and where it's going to
    print("Change:", changeAddress.to_string(), change)
    #create an output for the change
    changeout = TxOutput(change, changeAddress.to_script_pub_key())
    #add the output to our outs list
    outs.append(changeout)
    #update the transaction with our change output
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
            sig = priv_key.sign_segwit_input(tx, i, Script([seq.for_script(),
                "OP_DUP", "OP_HASH160", pubkey.to_hash160(),
                "OP_EQUALVERIFY", "OP_CHECKSIG"])
            , values[i])
            #This is SegWit, you have to add a witness to the signature
            tx.witnesses.append(Script([sig, pubkey.to_hex()]))
        elif Legacy:
            #Get the address we're sending from
            from_addr = P2pkhAddress(pubkey.get_address().to_string())
            #Sign it with the RIPEMD160 hash of the from address
            sig = priv_key.sign_input(tx, i, Script([seq.for_script(),
                "OP_DUP", "OP_HASH160", from_addr.to_hash160(),
                "OP_EQUALVERIFY", "OP_CHECKSIG"]))
            #Create a string of the from address pubkey hex
            pk = pubkey.to_hex()
            #Add the signature and the pubkey hex to the transaction
            #Nodes use the pubkey to verify the signature
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
    #Create a false boolean variable for each transaction protocol
    SegWit: bool = False
    Legacy: bool = False
    #Follow SegWit protocol
    if wallet["path"][0:5] == "m/84'":
        SegWit: bool = True
        print("Segwit enabled")
    #Follow legacy protocol
    elif wallet["path"][0:5] == "m/44'":
        Legacy: bool = True
        print("Legacy enabled")
    #Wallet protocol is not supported
    else:
        print("Wallet type not supported")
    #get our spendable coins
    print("Fetching your coins...")
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
    while funded_value < to_satoshis(amount) + 1000:
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
            seq = Sequence(TYPE_REPLACE_BY_FEE)
            txin = TxInput(txid, vout, sequence=seq.for_input_sequence())
            #add the input to our spending list
            spending.append(txin)
    #Create an Address object from the receiving address
    #If we're sending to a legacy address, instantiate a legacy address
    if to_address[0] == "1" or to_address[0] == "m" or to_address[0] == "n":
        toAddress = P2pkhAddress(to_address)
        #Create the output
        txout = TxOutput(to_satoshis(amount), toAddress.to_script_pub_key())
    #Default to a Segwit address
    else:
        toAddress = P2wpkhAddress(to_address)
        #Create the output
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
    #If this is a legacy transaction, up the fee by 75%, we want it to go through
    if Legacy:
        estimated_fee = estimated_fee * 1.75
    #update the fee by the amount of inputs
    estimated_fee = estimated_fee * len(spending)
    print("Estimatedfee:", estimated_fee)
    print("Would you like to use a custom fee Y/n")
    resp: str = input()
    if resp.lower() == "y":
        print("Please enter a fee amount (in sats)")
        custom_fee: int = int(input())
        print("Custom fee:", custom_fee)
        estimated_fee = custom_fee
    #Calculate the change left over
    change: int = int(funded_value - to_satoshis(amount) - estimated_fee)
    print("Change:", change)
    #create an unused address for the change
    #If we're on SegWit, send change to a SegWit address
    if SegWit:
        changeAddress = P2wpkhAddress(wallet_utils.getchangeaddress(wallet)["addresses"]["p2wpkh"])
        #Tell the user how much change and where it's going to
        print("Change:", changeAddress.to_string(), change)
    #If we're on Legacy, send change to a Legacy address
    elif Legacy:
        changeAddress = P2pkhAddress(wallet_utils.getchangeaddress(wallet)["addresses"]["p2pkh"])
        #Tell the user how much change and where it's going to
        print("Change:", changeAddress.to_string(), change)
    else:
        print("Unsupported Change Address")
    #create an output for the change
    changeout = TxOutput(change, changeAddress.to_script_pub_key())
    #add the output to our outs list
    outs.append(changeout)
    #update the transaction with the change output
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
        #sign the UTXO with its corresponding value from the values list we created earlier
        if SegWit:
            sig = priv_key.sign_segwit_input(tx, i, Script([
                "OP_DUP", "OP_HASH160", pubkey.to_hash160(),
                "OP_EQUALVERIFY", "OP_CHECKSIG"])
            , values[i])
            #This is SegWit, you have to add a witness to the signature
            tx.witnesses.append(Script([sig, pubkey.to_hex()]))
        #Legacy signature
        elif Legacy:
            #Get the from address
            from_addr = P2pkhAddress(pubkey.get_address().to_string())
            #Sign the output and add the RIPEMD160 if the from address
            sig = priv_key.sign_input(tx, i, Script([
                "OP_DUP", "OP_HASH160", from_addr.to_hash160(),
                "OP_EQUALVERIFY", "OP_CHECKSIG"]))
            #Get the hex of the public key we're sending from
            pk = pubkey.to_hex()
            #Add our signature and the pubkey hex
            #Nodes need to compare the signature to the public key
            utxo.script_sig = Script([sig, pk])
    #Now that we're done building the transaction, print the hex
    print("\nSigned transaction:\n" + tx.serialize())
    #Calculate and show the txid
    print("\nTxid:\n" + tx.get_txid())
    #Submit the transaction to the network through the block explorer
    try:
        attempt = str(explorer.tx.post(tx.serialize()).data)
    #Print the response, IT SHOULD BE EXACTLY THE SAME AS THE TXID ABOVE
    #If not, we have a problem
        print("\nServer Response:\n")
        print(attempt)
    except:
        print("Transaction failed")
    print("Would you like to attempt RBF?(Replace by fee) Y/n")
    print("WARNING: RBF is currently only supported for Legacy wallets")
    resp: str = input()
    if resp.lower() == "y":
        outs.clear()
        outs.append(txout)
        print("Original fee:", estimated_fee)
        print("Minimum RBF: ", estimated_fee * 2)
        fee: int = int(input())
        change = int(funded_value - to_satoshis(amount) - fee)
        new_changeout = TxOutput(change, changeAddress.to_script_pub_key())
        outs.append(new_changeout)
    
        new_tx = Transaction(spending, outs, has_segwit=True)
        for i, utxo in enumerate(spending):
            #find the corresponding private key in the keys list
            wif = keys[i]
            #turn in into a PrivateKey object
            priv_key = PrivateKey(wif=wif)
            #get the pubkey from the private key
            pubkey = priv_key.get_public_key()
            #sign the UTXO with its corresponding value from the values list we created earlier
            if SegWit:
                sig = priv_key.sign_segwit_input(new_tx, i, Script([
                "OP_DUP", "OP_HASH160", pubkey.to_hash160(),
                "OP_EQUALVERIFY", "OP_CHECKSIG"])
            , values[i])
            #This is SegWit, you have to add a witness to the signature
            #    new_tx.witnesses.append(Script([sig, pubkey.to_hex()]))
            #Legacy signature
            elif Legacy:
                #Get the from address
                from_addr = P2pkhAddress(pubkey.get_address().to_string())
                #Sign the output and add the RIPEMD160 if the from address
                sig = priv_key.sign_input(new_tx, i, Script([
                "OP_DUP", "OP_HASH160", from_addr.to_hash160(),
                "OP_EQUALVERIFY", "OP_CHECKSIG"]))
                #Get the hex of the public key we're sending from
                pk = pubkey.to_hex()
                #Add our signature and the pubkey hex
                #Nodes need to compare the signature to the public key
                utxo.script_sig = Script([sig, pk])
        if network == "testnet":
            url = "https://blockstream.info/testnet/api/tx"
        else:
            url = "https://blockstream.info/api/tx"
        response = requests.post(url, data=tx.serialize())
        if response.status_code == 200:
            return response.text
        else:
            counter = 0
            for i in response.text:
                if i == "{":
                    return json.loads(response.text[counter:])["message"]
                else:
                    counter += 1

def get_tx(txid: str, network: str):
    if network == "mainnet":
        explorer = bitcoin_explorer
    elif network == "testnet":
        explorer = bitcoin_testnet_explorer
    else:
        print("Unsupported network")
        return None
    return explorer.tx.get(txid).data
    
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
        print("You selected", selection["txid"], tx["value"], "sat")
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
                continue
    #return the list
    return spends

def non_interactive_send(wallet: dict, amount: float, to_address: str):
    #figure out which network we're using
    network: str = wallet["network"]
    if network == "mainnet":
        #mainnet block explorer
        explorer = bitcoin_explorer
    elif network == "testnet":
        #testnet block explorer
        explorer = bitcoin_testnet_explorer
    setup(network)
    #Create a false boolean variable for each transaction protocol
    SegWit: bool = False
    Legacy: bool = False
    #Follow SegWit protocol
    if wallet["path"][0:5] == "m/84'":
        SegWit: bool = True
    #Follow legacy protocol
    elif wallet["path"][0:5] == "m/44'":
        Legacy: bool = True
    #Wallet protocol is not supported
    else:
        print("Wallet type not supported")
        return None
    #get our spendable coins
    outputs: list = get_all_outputs(wallet)
    #Get the address to send to
    #show the maximum amount (i.e. wallet balance)
    #while our amount is greater than our balance, try again
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
    #make sure our transaction is funded for at least the amount and fee
    #1000 sats is arbitrary, just to make sure there will absolutely be enough for the fee
    while funded_value < to_satoshis(amount) + 1000:
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
            #add the value to our total funded value
            funded_value += value
            #add the value to our values list
            values.append(value)
            #create the input
            txin = TxInput(txid, vout)
            #add the input to our spending list
            spending.append(txin)
    #Create an Address object from the receiving address
    #If we're sending to a legacy address, instantiate a legacy address
    if to_address[0] == "1" or to_address[0] == "m" or to_address[0] == "n":
        toAddress = P2pkhAddress(to_address)
        #Create the output
        txout = TxOutput(to_satoshis(amount), toAddress.to_script_pub_key())
    #Default to a Segwit address
    else:
        toAddress = P2wpkhAddress(to_address)
        #Create the output
        txout = TxOutput(to_satoshis(amount), toAddress.to_script_pub_key())
    #Create the output for the address
    #txout = TxOutput(to_satoshis(amount), toAddress.to_script_pub_key())
    #instantiate the transaction
    tx = Transaction(spending, outs, has_segwit=True)
    #add the output to our list of outs
    outs.append(txout)
    #show the current size of the transaction
    #get the current fee rate
    feerate: float = get_fees(network)
    #estimate the fee per input
    estimated_fee: int = (feerate * tx.get_size())
    #if the estimated fee is too low, bring it to 150 sat per input
    if estimated_fee < 110:
        estimated_fee = 150
    #If this is a legacy transaction, up the fee by 75%, we want it to go through
    if Legacy:
        estimated_fee = estimated_fee * 1.75
    #update the fee by the amount of inputs
    estimated_fee = estimated_fee * len(spending)
    #Calculate the change left over
    change: int = int(funded_value - to_satoshis(amount) - estimated_fee)
    #create an unused address for the change
    #If we're on SegWit, send change to a SegWit address
    if SegWit:
        changeAddress = P2wpkhAddress(wallet_utils.getchangeaddress(wallet)["addresses"]["p2wpkh"])
        #Tell the user how much change and where it's going to
    #If we're on Legacy, send change to a Legacy address
    elif Legacy:
        changeAddress = P2pkhAddress(wallet_utils.getchangeaddress(wallet)["addresses"]["p2pkh"])
        #Tell the user how much change and where it's going to
    else:
        print("Unsupported Change Address")
        return None
    #create an output for the change
    changeout = TxOutput(change, changeAddress.to_script_pub_key())
    #add the output to our outs list
    outs.append(changeout)
    #update the transaction with the change output
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
        #sign the UTXO with its corresponding value from the values list we created earlier
        if SegWit:
            sig = priv_key.sign_segwit_input(tx, i, Script([
                "OP_DUP", "OP_HASH160", pubkey.to_hash160(),
                "OP_EQUALVERIFY", "OP_CHECKSIG"])
            , values[i])
            #This is SegWit, you have to add a witness to the signature
            tx.witnesses.append(Script([sig, pubkey.to_hex()]))
        #Legacy signature
        elif Legacy:
            #Get the from address
            from_addr = P2pkhAddress(pubkey.get_address().to_string())
            #Sign the output and add the RIPEMD160 if the from address
            sig = priv_key.sign_input(tx, i, Script([
                "OP_DUP", "OP_HASH160", from_addr.to_hash160(),
                "OP_EQUALVERIFY", "OP_CHECKSIG"]))
            #Get the hex of the public key we're sending from
            pk = pubkey.to_hex()
            #Add our signature and the pubkey hex
            #Nodes need to compare the signature to the public key
            utxo.script_sig = Script([sig, pk])
    #Submit the transaction to the network and return the result
    if network == "testnet":
        url = "https://blockstream.info/testnet/api/tx"
    else:
        url = "https://blockstream.info/api/tx"
    response = requests.post(url, data=tx.serialize())
    if response.status_code == 200:
        return response.text
    else:
        counter = 0
        for i in response.text:
            if i == "{":
                return json.loads(response.text[counter:])["message"]
            else:
                counter += 1

def create_unsigned_tx(wallet: dict, amount: float, to_address: str):
    #figure out which network we're using
    network: str = wallet["network"]
    if network == "mainnet":
        #mainnet block explorer
        explorer = bitcoin_explorer
    elif network == "testnet":
        #testnet block explorer
        explorer = bitcoin_testnet_explorer
    setup(network)
    #Create a false boolean variable for each transaction protocol
    SegWit: bool = False
    Legacy: bool = False
    #Follow SegWit protocol
    if wallet["path"][0:5] == "m/84'":
        SegWit: bool = True
    #Follow legacy protocol
    elif wallet["path"][0:5] == "m/44'":
        Legacy: bool = True
    #Wallet protocol is not supported
    else:
        print("Wallet type not supported")
        return None
    #get our spendable coins
    outputs: list = get_all_outputs(wallet)
    #Get the address to send to
    #show the maximum amount (i.e. wallet balance)
    #while our amount is greater than our balance, try again
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
    #make sure our transaction is funded for at least the amount and fee
    #1000 sats is arbitrary, just to make sure there will absolutely be enough for the fee
    while funded_value < to_satoshis(amount) + 1000:
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
            #add the value to our total funded value
            funded_value += value
            #add the value to our values list
            values.append(value)
            #create the input
            txin = TxInput(txid, vout)
            #add the input to our spending list
            spending.append(txin)
    #Create an Address object from the receiving address
    #If we're sending to a legacy address, instantiate a legacy address
    if to_address[0] == "1" or to_address[0] == "m" or to_address[0] == "n":
        toAddress = P2pkhAddress(to_address)
        #Create the output
        txout = TxOutput(to_satoshis(amount), toAddress.to_script_pub_key())
    #Default to a Segwit address
    else:
        toAddress = P2wpkhAddress(to_address)
        #Create the output
        txout = TxOutput(to_satoshis(amount), toAddress.to_script_pub_key())
    #Create the output for the address
    #txout = TxOutput(to_satoshis(amount), toAddress.to_script_pub_key())
    #instantiate the transaction
    tx = Transaction(spending, outs, has_segwit=True)
    #add the output to our list of outs
    outs.append(txout)
    #show the current size of the transaction
    #get the current fee rate
    feerate: float = get_fees(network)
    #estimate the fee per input
    estimated_fee: int = (feerate * tx.get_size())
    #if the estimated fee is too low, bring it to 150 sat per input
    if estimated_fee < 110:
        estimated_fee = 150
    #If this is a legacy transaction, up the fee by 75%, we want it to go through
    if Legacy:
        estimated_fee = estimated_fee * 1.75
    #update the fee by the amount of inputs
    estimated_fee = estimated_fee * len(spending)
    #Calculate the change left over
    change: int = int(funded_value - to_satoshis(amount) - estimated_fee)
    #create an unused address for the change
    #If we're on SegWit, send change to a SegWit address
    if SegWit:
        changeAddress = P2wpkhAddress(wallet_utils.getchangeaddress(wallet)["addresses"]["p2wpkh"])
        #Tell the user how much change and where it's going to
    #If we're on Legacy, send change to a Legacy address
    elif Legacy:
        changeAddress = P2pkhAddress(wallet_utils.getchangeaddress(wallet)["addresses"]["p2pkh"])
        #Tell the user how much change and where it's going to
    else:
        print("Unsupported Change Address")
        return None
    #create an output for the change
    changeout = TxOutput(change, changeAddress.to_script_pub_key())
    #add the output to our outs list
    outs.append(changeout)
    #update the transaction with the change output
    tx = Transaction(spending, outs, has_segwit=True)
    return tx.serialize()
    
    
    
    