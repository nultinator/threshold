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
    funded_value: int = 0
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
        funded_value += value
        txin = TxInput(txid, vout)
        spending.append(txin)
    toAddress = P2wpkhAddress(to_address)
    #script_code = Script(["OP_DUP", "OP_HASH160", pubkey.to_hash160(),
    #                        "OP_EQUALVERIFY", "OP_CHECKSIG"])
    txout = TxOutput(to_satoshis(amount), toAddress.to_script_pub_key())
    tx = Transaction(spending, outs, has_segwit=True)

    outs.append(txout)
    selector: int = 0
    print("SIZE:", tx.get_size())
    feerate: float = get_fees(network)
    estimated_fee: int = (feerate * tx.get_size())
    if estimated_fee < 110:
        estimated_fee = 150
    print("Estimatedfee:", estimated_fee)
    change: int = funded_value - to_satoshis(amount) - estimated_fee
    print("Change:", change)
    changeAddress = P2wpkhAddress(wallet_utils.getchangeaddress(wallet)["addresses"]["p2wpkh"])
    print("Change:", changeAddress.to_string(), change)
    changeout = TxOutput(change, changeAddress.to_script_pub_key())
    outs.append(changeout)
    tx = Transaction(spending, outs, has_segwit=True)

    
    for utxo in inputs:

        #print("\nRaw transaction:\n" + tx.serialize())

        print("WIF", wif)

        priv_key = PrivateKey(wif=wif)
        pubkey = priv_key.get_public_key()
        from_address = pubkey.get_segwit_address()
        sig = priv_key.sign_segwit_input(tx, selector, Script([
            "OP_DUP", "OP_HASH160", pubkey.to_hash160(),
            "OP_EQUALVERIFY", "OP_CHECKSIG"]
        ), funded_value)


        tx.witnesses.append(Script([sig, pubkey.to_hex()]))

        selector += 1

    print("\nSigned transaction:\n" + tx.serialize())

    print("\nTxid:\n" + tx.get_txid())

    attempt = explorer.tx.post(tx.serialize())

    print(attempt.data)

def sendmany(wallet: dict):
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
    target = to_satoshis(amount)
    spending = []
    outs = []
    funded_value: int = 0

    while funded_value < target:
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
            funded_value += value
            txin = TxInput(txid, vout)
            spending.append(txin)
    toAddress = P2wpkhAddress(to_address)
    script_code = Script(["OP_DUP", "OP_HASH160", pubkey.to_hash160(),
                            "OP_EQUALVERIFY", "OP_CHECKSIG"])
    txout = TxOutput(to_satoshis(amount), toAddress.to_script_pub_key())
    outs.append(txout)
    tx = Transaction(spending, outs, has_segwit=True)
    selector: int = 0
    for utxo in inputs:

        print("\nRaw transaction:\n" + tx.serialize())

        sig = priv_key.sign_segwit_input(tx, selector, script_code, funded_value)

        tx.witnesses.append(Script([sig, pubkey.to_hex()]))

        selector += 1

    print("\nSigned transaction:\n" + tx.serialize())

    print("\nTxid:\n" + tx.get_txid())

    attempt = explorer.tx.post(tx.serialize())

    print(attempt.data)



    #get and print the current feerate
    fee: int = get_fees(network)
    

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
