# Import Python Dev Tools
import dill
from pathlib import Path
import requests
import click
from treelib import *
from typing import Union
import os
import unicodedata

# Import Python Crypto Libraries
import secrets
import base58
from mnemonic import Mnemonic
import hashlib

# Import Python HD Wallet Modules
from helper import *
from ecc import *
from txn import *
from script import *
from op import *
from bech32 import *
from p2sh import *
from bip32 import *
from constants import *



SECP256k1 = ecdsa.curves.SECP256k1
CURVE_GEN = ecdsa.ecdsa.generator_secp256k1
CURVE_ORDER = CURVE_GEN.order()
FIELD_ORDER = SECP256k1.curve.p()
INFINITY = ecdsa.ellipticcurve.INFINITY
Point_or_PointJacobi = Union[
    ecdsa.ellipticcurve.Point, 
    ecdsa.ellipticcurve.PointJacobi
]

class InvalidKeyError(Exception):
    """Raised when derived key is invalid"""

'''Create a dictionary to map address type to the appropriate pubkey-to-address transformation function. That way, we can avoid 
using if loops to apply the relevant function. The importance of avoiding if loops comes into play when we want to expand the types of addresses we want the wallet to create.
We can just update this dictionary once, rather than update the codebase with multiple if conditions in each relevant section.'''

addrTypeDict = {
    '1': pub_to_legacy,
    '3': pub_to_p2sh,
    'b': pub_to_bech32,
    'legacy': pub_to_legacy,
    'p2sh': pub_to_p2sh,
    None: pub_to_bech32
    }

mnemo = Mnemonic("english")


'''
Below functions represent the future core front-end features. 
'''

@click.group()
def cli():
    pass
    
'''
Create a new Wallet

User input parameters: None
Expected behavior: New wallet initialized with base BTC hierarchy. 24 word mnemonic displayed for user. 
If wallet already exists, then program cannot create a new wallet. 
'''

@click.command()
@click.option('--password', help='Add a custom password for extra security.')
@click.option('--type', help='Default: P2WPKH. Options: p2sh, legacy')
def create_wallet(password, type):
    """Create a new wallet"""

    if os.path.isdir('wallet'):
        print('Wallet or Master Key already exists. Cannot create new wallet.')
    else:
        mnemonic_new = WalletClass.generate(strength=256)
        seed_new = WalletClass.bip39_seed_from_mnemonic(mnemonic_new, password)
        [master_priv_key, master_chain_code] = WalletClass.master_key(seed_new)
        master_pub_key = priv_to_pub_ecdsa(master_priv_key)
        
        try: 
            master_pub_address = addrTypeDict[type](master_pub_key)
        except Exception as e:
            print('Invalid wallet type input. Enter "p2sh" for pay-to-script-hash, "legacy" for legacy, or leave type option blank for SegWit wallet.')  
            exit()

        # Create the Root Node:
        HDWalletTree = Tree()
        HDWalletTree.create_node(master_pub_address, master_pub_address, parent=None, data=Node_Data(
            publickey = None,
            pubaddress = None,
            btc_balance = 0,
            parentnode = None,
            childnode = None,
            branches = 0,
            index = 1
        )) 

        # Create 44' Purpose level from master private key (Root Node):
        purpose_44 = ChildPrivateKey(master_priv_key, master_chain_code, HARDENED).ckdpriv()  
        purpose_44_pubkey = priv_to_pub_ecdsa(purpose_44[1]) # Temporarily use this until we can figure out ckd algorithm for deriving child public key from master public key. 
        purpose_44_pubaddress = addrTypeDict[type](purpose_44_pubkey)
        HDWalletTree.create_node(purpose_44_pubaddress, purpose_44_pubaddress, parent=master_pub_address, data=Node_Data(
            publickey = purpose_44_pubkey, 
            pubaddress = purpose_44_pubaddress,
            btc_balance = 0,
            parentnode = master_pub_address,
            childnode = None,
            branches = 0,
            index = HARDENED
        ))

        # Create 0' Coin Type level from Purpose private key
        coin_type = ChildPrivateKey(purpose_44[1], purpose_44[0].chain_code, HARDENED).ckdpriv()  
        coin_type_pubkey = priv_to_pub_ecdsa(coin_type[1]) # Temporarily use this until we can figure out ckd algorithm for deriving child public key from master public key. 
        coin_type_pubaddress = addrTypeDict[type](coin_type_pubkey)
        HDWalletTree.create_node(coin_type_pubaddress, coin_type_pubaddress, parent=purpose_44_pubaddress, data=Node_Data(
            publickey = coin_type_pubkey,
            pubaddress = coin_type_pubaddress,
            btc_balance = 0,
            parentnode = purpose_44_pubaddress,
            childnode = None,
            branches = 0,
            index = HARDENED
        ))

        # Create 0' Account level from Coin Type private key
        account_level = ChildPrivateKey(coin_type[1], coin_type[0].chain_code, HARDENED).ckdpriv()  
        account_level_pubkey = priv_to_pub_ecdsa(account_level[1]) # Temporarily use this until we can figure out ckd algorithm for deriving child public key from master public key. 
        account_level_pubaddress = addrTypeDict[type](account_level_pubkey)
        HDWalletTree.create_node(account_level_pubaddress, account_level_pubaddress, parent=coin_type_pubaddress, data=Node_Data(
            publickey = coin_type_pubkey,
            pubaddress = coin_type_pubaddress,
            btc_balance = 0,
            parentnode = coin_type_pubaddress,
            childnode = None,
            branches = 0,
            index = HARDENED
        ))

        # Create Receiving and Change Root Nodes
        receive_change = []

        count = 1
        for i in range(BRANCHES_PER_ACCOUNT):
            receive_change_level = ChildPrivateKey(account_level[1], account_level[0].chain_code, count).ckdpriv() 
            if count == 1:
                receive_priv_key = receive_change_level[1]
                receive_chain_code = receive_change_level[0].chain_code
            count += 1
            receive_change_pubkey = priv_to_pub_ecdsa(receive_change_level[1]) # Temporarily use this until we can figure out ckd algorithm for deriving child public key from master public key. 
            receive_change_pubaddress = addrTypeDict[type](receive_change_pubkey)
            receive_change.append(receive_change_pubaddress)
            HDWalletTree.create_node(receive_change_pubaddress, receive_change_pubaddress, parent=account_level_pubaddress, data=Node_Data(
                publickey = receive_change_pubkey,
                pubaddress = receive_change_pubaddress,
                btc_balance = 0,
                parentnode = account_level_pubaddress,
                childnode = None,
                branches = 0,
                index = count))
            

        # Create data structures for modifying tree object
        receiving_dict = {}
        change_dict = {}

        # Display relevant information to user
        print("24 Word Mnemonic:" + " " + mnemonic_new)
        
        # Create the directory for the two wallet files
        os.mkdir('wallet')

        # Save the master key information on device to use later
        with open('wallet/masterkey.pkl', 'wb') as file:
            dill.dump(master_priv_key, file)
            dill.dump(master_chain_code, file)
            dill.dump(master_pub_key, file)
            dill.dump(master_pub_address, file)
            dill.dump(receive_priv_key, file)
            dill.dump(receive_chain_code, file)    

        # Serialize and save relevant objects + data structures
        with open('wallet/wallet.pkl', 'wb') as file:
            dill.dump(HDWalletTree, file)
            dill.dump(receive_change, file)
            dill.dump(receiving_dict, file)
            dill.dump(change_dict, file)


'''
Display Wallet BTC balance

User input parameters: None
Expected behavior: Wallet displays total BTC amount.
If the wallet was never created, let user know. 
'''

@click.command()
def balance():
    """Display wallet BTC balance"""

    # .is_file() method returns 'True' if file already exists. 
    if os.path.isdir('wallet'):
        with open('wallet/wallet.pkl', 'rb') as file:
            HDWalletTree = dill.load(file)
            receive_change = dill.load(file)
            receiving_dict = dill.load(file)
            change_dict = dill.load(file)

        # Add logic to clean up no longer needed receiving and change addresses so as to keep wallet performant

        for key in receiving_dict:
            address = receiving_dict[key]
            address_data = (requests.get("https://blockstream.info/api/address/" + address)).json()
            address_balance = address_data['chain_stats']['funded_txo_sum'] - address_data['chain_stats']['spent_txo_sum']
            setattr(HDWalletTree.get_node(address).data, 'btc_balance', address_balance)

        for key in change_dict:
            address = change_dict[key]
            address_data = (requests.get("https://blockstream.info/api/address/" + address)).json()
            address_balance = address_data['chain_stats']['funded_txo_sum'] - address_data['chain_stats']['spent_txo_sum']
            setattr(HDWalletTree.get_node(address).data, 'btc_balance', address_balance)

        # The balance_total method produces a result in Satoshis
        btc_balance = to_btc(WalletClass.balance_total(HDWalletTree, receiving_dict, change_dict))   
        print("BTC Balance:" + " " + str(btc_balance))     
    else:
        print('Wallet does not exist. Please run the "create-wallet" command to create a wallet.')


'''
Transfer in BTC

User input parameters: None
Expected behavior: Wallet displays new public address for transferring BTC
If the wallet was never created, let user know. 
'''

@click.command()
def deposit():
    """Deposit BTC into wallet"""
    
    if os.path.isdir('wallet'):
        # Load object and data structures
        with open('wallet/wallet.pkl', 'rb') as file1:
            HDWalletTree = dill.load(file1)
            receive_change = dill.load(file1)
            receiving_dict = dill.load(file1)
            change_dict = dill.load(file1)

        with open('wallet/masterkey.pkl', 'rb') as file2:
            master_priv_key = dill.load(file2)
            master_chain_code = dill.load(file2)
            master_pub_key = dill.load(file2)
            master_pub_address = dill.load(file2)
            receive_priv_key = dill.load(file2)
            receive_chain_code = dill.load(file2) 

        receive_root = receive_change[0]
        
        '''
        Determine index and create a new address. Note: only hardened child addresses are being created for improved security. 
        '''
        if bool(receiving_dict):
            # Workflow if wallet already has receiving addresses
            i = list(receiving_dict.values())
            # Check the most recent address 
            address = getattr(HDWalletTree.get_node(i[-1]).data, 'pubaddress')
            address_data = (requests.get("https://blockstream.info/api/address/" + address)).json()
            tx_count = address_data['chain_stats']['tx_count']
            if tx_count == 0:
                # Workflow if user has unused address already. Wallet will continually reflect unused address for user until 
                # address sees UTXO. 
                print("Send only BTC to this address:" + " " + address)
            else:        
                # Workflow if previous index address already has UTXO usage
                index = getattr(HDWalletTree.get_node(i[-1]).data, 'index')
                [privatekey_obj, privatekey] = ChildPrivateKey(receive_priv_key, receive_chain_code, index+1).ckdpriv()  
                new = addrTypeDict[receive_root[0]](privatekey)
                HDWalletTree.create_node(new, new, parent=receive_root, data=Node_Data(
                    publickey = priv_to_pub_ecdsa(privatekey),
                    pubaddress = new,
                    btc_balance = 0,
                    parentnode = receive_root,
                    childnode = None,
                    branches = 0,
                    index = index+1))

                new_entry = {index + 1:new}
                receiving_dict.update(new_entry)
                print("Send only BTC to this address:" + " " + new)
        else:
            # Workflow if no receiving addresses have been created at all (brand new wallet)
            index = HARDENED
            [privatekey_obj, privatekey] = ChildPrivateKey(receive_priv_key, receive_chain_code, index).ckdpriv()  
            new = addrTypeDict[receive_root[0]](privatekey)
            HDWalletTree.create_node(new, new, parent=receive_root, data=Node_Data(
                publickey = priv_to_pub_ecdsa(privatekey),
                pubaddress = new,
                btc_balance = 0,
                parentnode = receive_root,
                childnode = None,
                branches = 0,
                index = HARDENED))

            new_entry = {index:new}
            receiving_dict.update(new_entry)
            print("Send only BTC to this address:" + " " + new)

        # Save modified object and data structures back onto pickle file
        with open('wallet/wallet.pkl', 'wb') as file:  
            dill.dump(HDWalletTree, file)
            dill.dump(receive_change, file)
            dill.dump(receiving_dict, file)
            dill.dump(change_dict, file)

    else:
        print('Wallet does not exist. Please run the "create-wallet" command to create a wallet.')


'''
Transfer out BTC

User input parameters: BTC Amount Requested, Target BTC Address
Expected behavior: Wallet displays Transaction ID associated with BTC transfer.
If the wallet was never created, let user know. 

'''

@click.command()
@click.option('--btc_amount', help='Requested BTC transfer amount')
@click.option('--target_address', help='Target Transfer Address')
def withdraw(btc_amount, target_address):
    """Withdraw BTC from wallet"""  
    '''
    NOTE: All BTC amounts converted into Satoshi for consistency! 
    This function returns the signed transaction object, ready for broadcasting. 
    '''
    
    if os.path.isdir('wallet'):
        # Load object and data structures
        with open('wallet/wallet.pkl', 'rb') as file:
            HDWalletTree = dill.load(file)
            receive_change = dill.load(file)
            receiving_dict = dill.load(file)
            change_dict = dill.load(file)
            wallettype = dill.load(file)

        '''
        This function parses the child accounts until the requested BTC balance amount + necessary fees can be summed up. 
        '''
        address_list = []
        balance_list = []
        prev_txn_list = []
        prev_index_list = []
        prev_tx_script_pubkey_list = []
        txn_ins = []
        btc_balance = WalletClass.balance_total(HDWalletTree, receiving_dict, change_dict)

        '''
        Parse the receiving only dictionary storing the BTC addresses for requisite BTC balance in the receiving addresses 
        While parsing, append corresponding address and balance in the address and balance lists. 
        '''
        btc_requested = to_sats(float(btc_amount))   # float and integer can be freely mixed in python mathematical operations

        if btc_balance < btc_requested + WalletClass.fee_estimate():      # Ensures no infinite while loop due to wallet BTC balance < requested BTC amount. 
            print("Requested BTC amount & transaction fee exceeds wallet balance") 
        else:
            while sum(balance_list) < btc_requested + WalletClass.fee_estimate():       #+ WalletClass.fee_estimate():   
                for key, value in receiving_dict.items():
                    balance = getattr(HDWalletTree.get_node(value).data, 'btc_balance')  # balance is returned in Satoshis    
                    if balance > 0:
                        address_list.append(value)
                        balance_list.append(balance)


        '''
        Create previous transaction list from querying each address that is sending the BTC
        '''

        for address in address_list:
            address_info = requests.get("https://blockstream.info/api/address/" + address + "/txs").json()
            for i in address_info:
                input = i['txid']
                prev_txn = bytes.fromhex(input)
                prev_txn_list.append(prev_txn)

        '''
        Create previous index list corresponding to each transaction ID in the previous transaction list
        In the below code, the first index is always 0, so if there is a match, 0 is returned as index position. 
        However, if no match, then we keep looping in the 'out' section and increment index position by 1 for each loop
        until we find a match. 
        '''
        index_pos = 0
        for txn_id in prev_txn_list:
            txn_info = requests.get("https://blockstream.info/api/tx/" + txn_id.hex()).json()
            for i in txn_info['vout']:
                if i['scriptpubkey_address'] == address:
                    value = index_pos
                    prev_tx_script_pubkey_list.append(i['scriptpubkey'])
                else:
                    index_pos += 1
            prev_index_list.append(value)

        '''
        Create a new hardened change address for UTXO, regardless if change actually exists. 
        '''
        change_root = receive_change[1]
        if bool(change_dict):
            i = list(change_dict.values())
            address = getattr(HDWalletTree.get_node(i[-1]).data, 'pubaddress')
            address_data = (requests.get("https://blockstream.info/api/address/" + address)).json()
            tx_count = address_data['chain_stats']['tx_count']
            if tx_count == 0:
                # Workflow if user has unused address already. Wallet will continually reflect unused address for user until 
                # address sees UTXO. 
                change_address = address
            else:
                i = list(change_dict.values())
                index = getattr(HDWalletTree.get_node(i[-1]).data, 'index')
                new = WalletClass.create_address(HDWalletTree, change_root, index, type)
                change_address = new[1]
                new_entry = {index:change_address}
                change_dict.update(new_entry)
        else:
            index = HARDENED
            new = WalletClass.create_address(HDWalletTree, change_root, index, type)
            change_address = new[1]
            new_entry = {index:change_address}
            change_dict.update(new_entry)


        # Create and transaction object
        txn_obj = WalletClass.build_txn_object(address_list, prev_txn_list, prev_index_list, target_address, change_address, btc_requested, btc_balance)
        
        for address in address_list:
            [chain_code, privkey] = WalletClass.derive_key(address)

    
        priv = PrivateKey(secret_key=privkey)
        txn_obj.sign_input(0, priv)
        raw_txn = txn_obj.serialize().hex()

        broadcast_txn = requests.post('https://blockstream.info/api/tx', data = raw_txn)
        print(broadcast_txn.text)

        '''
        1) Convert private key into integer format for signing
        2) For each input address in the transaction being created, sign the message using the private key associated with the input address. The output of this signature
        is the tuple (r,s), which specify the signature. 
            Note: when you sign each input, remove the script of the input you are not signing (leave it empty) 
        3) Encode the signature tuple (r,s) to create the DER signature. The result is byte form that can be called sig_bytes. Value "r" is the x-coordinate of the resulting point
        k*G. Value k is the private key. k*G is the public key pair to the private key.  
        4) Generate the SEC format for the public key associated with each private key/address. 
        5) Use the sig_bytes and SEC format public key to create the script_sig object for a particular input. This is done by instantiating the Script class with the two 
        aforementioned elements as input arguments. 
        6) Insert the script_sig output into the script_sig attribute of the tx_ins object. This is essentially, "populating" the empty script sig field we marked as NONE earlier. 
        I think by inserting the script_sig back in, we are modifying the txn_bj (the instance of Tx class), so we can run len(txn_obj.encode().hex()) to obtain the transaction
        size in bytes. 
        7) Calculate the Transaction ID of the finished transaction.    
        '''
        '''
        print(address_list)

        if len(address_list) > 1:
            # Loop through each input address in order to sign the message for each address:
            for address in address_list:
                # Convert private key into integer format and sign the message to create the DER signature
                [chain_code, privkey] = WalletClass.derive_key(address)
                # Prior to signing, need to modify the message so the script of the input not being signed is empty...


                private_key = PrivateKey(secret_key=privkey)
                der = private_key.sign(message).der()
                sig = der + SIGHASH_ALL.to_bytes(1, 'big')
                # Generate the SEC public key and create the script_sig
                publickey_sec = big_endian_to_int(privkey) * G
                script_sig = Script([sig, publickey_sec])
        
                # Assign script sig to the script_sig attribute for the correct txn_in object int he txn_ins list:
                for i in txn_ins:
                    i.script_sig = script_sig
        
        elif len(address_list) == 1:
            [chain_code, privkey] = WalletClass.derive_key(address_list[0])
            print('derived private key: ' + privkey.hex())
            print('Address which contains the balance: ' + address_list[0])
            print('Address from derived privatekey: ' + str(pubkey_to_address(priv_to_pub_ecdsa(privkey))))

            private_key = PrivateKey(secret_key=privkey)
            der = private_key.sign(message).der()
            print('DER: ' + str(der.hex()))
            sig = der + SIGHASH_ALL.to_bytes(1, 'big')
            print('signature: ' + str(sig.hex()))
            # Generate the SEC public key and create the script_sig
            publickey_sec = (big_endian_to_int(privkey) * G).sec()
            print('publickey in SEC format: ' + str(publickey_sec.hex()))
            script_sig = Script([sig, publickey_sec])
            print('script_sig: ' + str(script_sig))
            print(txn_obj.tx_ins[0].script_sig)
            txn_obj.tx_ins[0].script_sig = script_sig
            print(txn_obj.tx_ins[0].script_sig)
            raw_txn = txn_obj.serialize().hex()
            #print(raw_txn)
            print("Transaction size in bytes: ", len(txn_obj.serialize()))
            print("Transaction ID: ", two_round_hash256(txn_obj.serialize())[::-1].hex())  # little/big endian conventions require byte order swap
        
        else:
            print('BTC balance not enough for fee & requested amount. Please double check if BTC balance has enough.')

        # Broadcast raw transaction to the network

        broadcast_txn = requests.post('https://blockstream.info/api/tx', data = raw_txn)
        print(broadcast_txn.text)

        with open('wallet.pkl', 'wb') as file:
            dill.dump(HDWalletTree, file)
            dill.dump(receive_change, file)
            dill.dump(receiving_dict, file)
            dill.dump(change_dict, file)
        '''
    else:
        print('Wallet does not exist. Please run the "create-wallet" command to create a wallet.')


'''
Display past tansactions

User input parameters: None
Expected behavior: Wallet displays list of historical Transaction IDs. This allows users to keep track of transfers in and out.  
Note: Bitcoin blocks and transactions do not have timestamps. Any "timestamps" would have to be generated from the application side.  
'''

@click.command()
def display_txn():
    """Display all past wallet transactions""" 
      
    if os.path.isdir('wallet'):
        # Load object and create data structures
        txn_dict = {}
        with open('wallet/wallet.pkl', 'rb') as file:
            HDWalletTree = dill.load(file)
            receive_change = dill.load(file)
            receiving_dict = dill.load(file)
            change_dict = dill.load(file)
    
        print('Wallet Transaction History:')
        print(' ')
        for key in receiving_dict:
            address = receiving_dict[key]
            txn_info = requests.get("https://blockstream.info/api/address/" + address + "/txs").json()
            if len(txn_info) == 0:
                continue
            else:
                txid = txn_info[0]['txid']
                for scriptpubkey_address in txn_info[0]['vout']:
                    if scriptpubkey_address['scriptpubkey_address'] == address:
                        transfer_amount = to_btc(scriptpubkey_address['value'])
                        new_entry = {txid:transfer_amount}
                        txn_dict.update(new_entry)
                        print('Transaction ID: ' + txid + '   ' + 'BTC Amount: ' + str(transfer_amount))

        for key in change_dict:
            address = change_dict[key]
            txn_info = requests.get("https://blockstream.info/api/address/" + address + "/txs").json()
            if len(txn_info) == 0:
                continue
            else:
                txid = txn_info[0]['txid']
                for scriptpubkey_address in txn_info[0]['vout']:
                    if scriptpubkey_address['scriptpubkey_address'] == address:
                        transfer_amount = to_btc(scriptpubkey_address['value'])
                        new_entry = {txid:transfer_amount}
                        txn_dict.update(new_entry)
                        print('Transaction ID: ' + txid + '   ' + 'BTC Amount: ' + str(transfer_amount))
        print(' ')
        print('Complete')

    else:
        print('Wallet does not exist. Please run the "create-wallet" command to create a wallet.')


'''
Display current HD Wallet Hierarchy

User input parameters: None
Expected behavior: Wallet displays entire tree hierarchy. 
If the wallet was never created, let user know. 
'''

@click.command()
def tree():
    """Display wallet hierarchy"""
 
    if os.path.isdir('wallet'):
        with open('wallet/wallet.pkl', 'rb') as f:
            HDWalletTree = dill.load(f)
            HDWalletTree.show()
    else:
        print('Wallet does not exist. Please run the "create-wallet" command to create a wallet.')


'''
Sync Wallet

User input parameters: None
Expected behavior: Wallet updates each child key BTC balance in the Tree Data object, using the blockchain as the source of truth. 
If the wallet was never created, let user know. 
'''

@click.command()
def sync_wallet():
    """Sync wallet BTC amount"""
    
    if os.path.isdir('wallet'):
        # Load object and data structures
        with open('wallet/wallet.pkl', 'rb') as file:
            HDWalletTree = dill.load(file)
            receive_change = dill.load(file)
            receiving_dict = dill.load(file)
            change_dict = dill.load(file)

        for key in receiving_dict:
            address = receiving_dict[key]
            address_data = (requests.get("https://blockstream.info/api/address/" + address)).json()
            address_balance = address_data['chain_stats']['funded_txo_sum'] - address_data['chain_stats']['spent_txo_sum']
            setattr(HDWalletTree.get_node(address).data, 'btc_balance', address_balance)

        for key in change_dict:
            address = change_dict[key]
            address_data = (requests.get("https://blockstream.info/api/address/" + address)).json()
            address_balance = address_data['chain_stats']['funded_txo_sum'] - address_data['chain_stats']['spent_txo_sum']
            setattr(HDWalletTree.get_node(address).data, 'btc_balance', address_balance)

        with open('wallet/wallet.pkl', 'wb') as file:
            dill.dump(HDWalletTree, file)
            dill.dump(receive_change, file)
            dill.dump(receiving_dict, file)
            dill.dump(change_dict, file)

        print('Wallet sync successfully completed.')
    
    else:
        print('Wallet does not exist. Please run the "create-wallet" command to create a wallet.')


'''
Set a Gap Limit of 20 keys in wallet recovery. The wallet will also limit address creation for transferring in 
by ensuring that a new address is not created unless the previous index address has UTXOs
'''

@click.command()
@click.option('--type', help='Default: P2WPKH. Options: p2sh, legacy')
@click.option('--recovery_phrase', help='Enter your recovery phrase')
@click.option('--password', help='Enter your password')
def recover_wallet(type, recovery_phrase, password):
    """Recover wallet from seed phrase"""
    
    try: 
        # Create necessary data structures:
        # receive_change = [receive root address, change root address]
        receive_change = []
        receiving_dict = {}
        change_dict = {}

        if os.path.isdir('wallet'):        
            print('Wallet or Master Key already exists. Cannot create new wallet.')
        else:
            seed_new = WalletClass.bip39_seed_from_mnemonic(recovery_phrase, password)
            [master_priv_key, chain_code] = WalletClass.master_key(seed_new)
            master_pub_key = priv_to_pub_ecdsa(master_priv_key)
            
            # Need to serialize information that marks wallet type. Then uses the appropriate logic. 
            try: 
                master_pub_address = addrTypeDict[type](master_pub_key)
            except Exception as e:
                print('Invalid wallet type input. Enter "p2sh" for pay-to-script-hash, or leave type option blank for SegWit wallet.')  
                exit()

            print('Wallet recovery in progress, please wait... ')

            # Create the Root Node:
            HDWalletTree = Tree()
            HDWalletTree.create_node(master_pub_address, master_pub_address, parent=None, data=Node_Data(
                publickey = None,
                pubaddress = None,
                btc_balance = 0,
                parentnode = None,
                childnode = None,
                branches = 0,
                index = 1
            )) 

            # Save the master key information on device to use later
            os.mkdir('wallet')
            with open('wallet/masterkey.pkl', 'wb') as file:
                dill.dump(master_priv_key, file)
                dill.dump(chain_code, file)
                dill.dump(master_pub_key, file)
                dill.dump(master_pub_address, file)
                  
            with open('wallet/wallet.pkl', 'wb') as file:  
                dill.dump(HDWalletTree, file)
                dill.dump(receive_change, file)
                dill.dump(receiving_dict, file)
                dill.dump(change_dict, file)


            # Create 44' Purpose level from master private key (Root Node):
            purpose_44 = ChildPrivateKey(master_priv_key, chain_code, HARDENED).ckdpriv()  
            purpose_44_pubkey = priv_to_pub_ecdsa(purpose_44[1]) # Temporarily use this until we can figure out ckd algorithm for deriving child public key from master public key. 
            purpose_44_pubaddress = addrTypeDict[type](purpose_44_pubkey)
            HDWalletTree.create_node(purpose_44_pubaddress, purpose_44_pubaddress, parent=master_pub_address, data=Node_Data(
                publickey = purpose_44_pubkey, 
                pubaddress = purpose_44_pubaddress,
                btc_balance = 0,
                parentnode = master_pub_address,
                childnode = None,
                branches = 0,
                index = HARDENED
            ))

            # Create 0' Coin Type level from Purpose private key
            coin_type = ChildPrivateKey(purpose_44[1], purpose_44[0].chain_code, HARDENED).ckdpriv()  
            coin_type_pubkey = priv_to_pub_ecdsa(coin_type[1]) # Temporarily use this until we can figure out ckd algorithm for deriving child public key from master public key. 
            coin_type_pubaddress = addrTypeDict[type](coin_type_pubkey)
            HDWalletTree.create_node(coin_type_pubaddress, coin_type_pubaddress, parent=purpose_44_pubaddress, data=Node_Data(
                publickey = coin_type_pubkey,
                pubaddress = coin_type_pubaddress,
                btc_balance = 0,
                parentnode = purpose_44_pubaddress,
                childnode = None,
                branches = 0,
                index = HARDENED
            ))

            # Create 0' Account level from Coin Type private key
            account_level = ChildPrivateKey(coin_type[1], coin_type[0].chain_code, HARDENED).ckdpriv()  
            account_level_pubkey = priv_to_pub_ecdsa(account_level[1]) # Temporarily use this until we can figure out ckd algorithm for deriving child public key from master public key. 
            account_level_pubaddress = addrTypeDict[type](account_level_pubkey)
            HDWalletTree.create_node(account_level_pubaddress, account_level_pubaddress, parent=coin_type_pubaddress, data=Node_Data(
                publickey = coin_type_pubkey,
                pubaddress = coin_type_pubaddress,
                btc_balance = 0,
                parentnode = coin_type_pubaddress,
                childnode = None,
                branches = 0,
                index = HARDENED
            ))

            # Create Receiving and Change Root Nodes

            count = 1
            for i in range(BRANCHES_PER_ACCOUNT):
                receive_change_level = ChildPrivateKey(account_level[1], account_level[0].chain_code, count).ckdpriv() 
                count += 1
                receive_change_pubkey = priv_to_pub_ecdsa(receive_change_level[1]) # Temporarily use this until we can figure out ckd algorithm for deriving child public key from master public key. 
                receive_change_pubaddress = addrTypeDict[type](receive_change_pubkey)
                receive_change.append(receive_change_pubaddress)
                HDWalletTree.create_node(receive_change_pubaddress, receive_change_pubaddress, parent=account_level_pubaddress, data=Node_Data(
                    publickey = receive_change_pubkey,
                    pubaddress = receive_change_pubaddress,
                    btc_balance = 0,
                    parentnode = account_level_pubaddress,
                    childnode = None,
                    branches = 0,
                    index = count
            ))

            # Loop through creating child receiving addresses until the designated gap limit is reached. 
            receive_root = receive_change[0]
            gap_count = 0
            index = HARDENED
            while gap_count <= GAP_LIMIT:
                new = WalletClass.create_address(HDWalletTree, receive_root, index, type)
                index += 1
                new_address = new[1]
                address_data = (requests.get("https://blockstream.info/api/address/" + new_address)).json()
                tx_count = address_data['chain_stats']['tx_count']
                if tx_count > 0:
                    # reset gap count if encounter a previously active address
                    gap_count = 0
                else: 
                    # otherwise, continue adding to gap count if address was never active
                    gap_count += 1
                new_entry = {index:new_address}
                receiving_dict.update(new_entry)

            update_files(HDWalletTree, receive_change, receiving_dict, change_dict)

            # Loop through creating child change addresses until the designated gap limit is reached. 
            change_root = receive_change[1]
            gap_count = 0
            index = HARDENED
            while gap_count <= GAP_LIMIT:
                new = WalletClass.create_address(HDWalletTree, change_root, index, type)
                index += 1
                new_address = new[1]
                address_data = (requests.get("https://blockstream.info/api/address/" + new_address)).json()
                tx_count = address_data['chain_stats']['tx_count']
                if tx_count > 0:
                    # reset gap count if encounter a previously active address
                    gap_count = 0
                else: 
                    # otherwise, continue adding to gap count if address was never active
                    gap_count += 1
                new_entry = {index:new_address}
                change_dict.update(new_entry)
        
            update_files(HDWalletTree, receive_change, receiving_dict, change_dict)
        
            for key in receiving_dict:
                address = receiving_dict[key]
                address_data = (requests.get("https://blockstream.info/api/address/" + address)).json()
                address_balance = address_data['chain_stats']['funded_txo_sum'] - address_data['chain_stats']['spent_txo_sum']
                setattr(HDWalletTree.get_node(address).data, 'btc_balance', address_balance)

            for key in change_dict:
                address = change_dict[key]
                address_data = (requests.get("https://blockstream.info/api/address/" + address)).json()
                address_balance = address_data['chain_stats']['funded_txo_sum'] - address_data['chain_stats']['spent_txo_sum']
                setattr(HDWalletTree.get_node(address).data, 'btc_balance', address_balance)

            btc_balance = to_btc(WalletClass.balance_total(HDWalletTree, receiving_dict, change_dict)) 
            print('Wallet recovery successfully completed. Total BTC balance:' + str(btc_balance))

            receive_priv_key = receive_change_level[1]
            receive_chain_code = receive_change_level[0].chain_code

            with open('wallet/masterkey.pkl', 'wb') as file:
                dill.dump(master_priv_key, file)
                dill.dump(chain_code, file)
                dill.dump(master_pub_key, file)
                dill.dump(master_pub_address, file)
                dill.dump(receive_priv_key, file)
                dill.dump(receive_chain_code, file)    
        
            with open('wallet/wallet.pkl', 'wb') as file:  
                dill.dump(HDWalletTree, file)
                dill.dump(receive_change, file)
                dill.dump(receiving_dict, file)
                dill.dump(change_dict, file)

    except Exception as e:
        print(e)
        print('Wallet recovery failed. Please double check your recovery phrase and password.')    
    

'''
End Core User Side Features
'''

# HD Wallet Key Derivation Path

# m (master priv/pub key) / 44' (purpose) / 0' (cointype - 0 for Bitcoin) / 0 ' (account) / 0 (recieving/change) / 0 (address_index)

################################################################################################################################################################################

class WalletClass(object):

    '''
    The Wallet class creates a new instance of a wallet. This class includes methods for generating a mnemonic, deriving the seed,
    deriving the master pub/priv keys, and creating addresses.    
    '''  
    receiving_dict = {} 
    change_dict = {}
    accounts_dict = {}

    def __init__(self, tree, strength, password):

        self.tree = tree
        self.strength = strength
        self.password = password
        self.key = []
        self.chain_code = []

    def generate(strength):
        """
        Create a new mnemonic using a random generated number as entropy.
        As defined in BIP39, the entropy must be a multiple of 32 bits, and its size must be between 128 and 256 bits.
        Therefore the possible values for `strength` are 128, 160, 192, 224 and 256.
        If not provided, the default entropy length will be set to 128 bits.
        The return is a list of words that encodes the generated entropy.
        :param strength: Number of bytes used as entropy
        :type strength: int
        :return: A randomly generated mnemonic
        :rtype: str
        """
        if strength not in [128, 160, 192, 224, 256]:
                raise ValueError(
                    "Invalid strength value. Allowed values are [128, 160, 192, 224, 256]."
                )
        mnemonic_new = mnemo.to_mnemonic(secrets.token_bytes(strength // 8))
        return mnemonic_new
        

    # Next step is to generate the 64 byte hexadecimal seed, given the Mnemonic:

    def bip39_seed_from_mnemonic(mnemonic: str, password: str) -> bytes:
        """
        Generates bip39 seed from mnemonic (and optional password).
        If an optional password is supplied, the salt is the utf-8 encoding of "mnemonic" concatenated with the password. 
        If no optional password is supplied, the salt is simply the utf-8 encoding of "mnemonic". 
        This is per BIP39 rules. 
        """
        PBKDF2_ROUNDS = 2048
        mnemonic = unicodedata.normalize("NFKD", mnemonic)
        try:
            password = unicodedata.normalize("NFKD", password)
            passphrase = unicodedata.normalize("NFKD", "mnemonic") + password
            seed = hashlib.pbkdf2_hmac(
            "sha512",
            mnemonic.encode("utf-8"),
            passphrase.encode("utf-8"),
            PBKDF2_ROUNDS
            )
            return seed
        except: 
            seed = hashlib.pbkdf2_hmac(
            "sha512",
            mnemonic.encode("utf-8"),
            ('mnemonic').encode("utf-8"), 
            PBKDF2_ROUNDS
            )
            return seed
        

    def master_key(bip39_seed: bytes) -> bytes:
       
        '''
        Function to generate Parent Extended Private Key from Mnemonic. Then check if extended private key is valid.
        '''

        # BIP32 specifically states to use the text string "Bitcoin seed" in calculating HMAC-SHA512 of the seed 
        I = hmac_sha512(key=b"Bitcoin seed", msg=bip39_seed)
            # private key
        IL = I[:32]
            # In case IL is 0 or ≥ n, the master key is invalid
        int_left_key = big_endian_to_int(IL)
        if int_left_key == 0:
            raise InvalidKeyError("master key is zero")
        if int_left_key >= CURVE_ORDER:
            raise InvalidKeyError(
                "master key {} is greater/equal to curve order".format(
                    int_left_key
                    )
                )
            # chain code
        IR = I[32:]
        masterprivkey = IL
        chain_code = IR
        return [masterprivkey, chain_code]


    def serialize(key_type, addr_type, depth, index, chain_code, key):

        '''
        Per BIP-32, there is a serialization format for extended public and private keys. This serialization format results in native segwit extended public keys starting with
        a `zpub` human readable prefix (h.r.p.), and p2sh extended public keys starting with an `xpub` prefix. For extended private keys, the h.r.p. are `zprv`and `xprv`, respectively. 
        If you create or recover a native segwit wallet on Trezor and display the master public key, it will display the extended master public key with zpub prefix. 


        This is a function to serialize public and private keys into extended keys
        '''
        if addr_type == "p2sh" and key_type == "public":    
            version = '0x0488b21e'
        elif addr_type == "p2sh" and key_type == "private": 
            version = '0x0488ade4'
        elif addr_type == "bech32" and key_type == "public":
            version = '0x04b24746'
        elif addr_type == "bech32" and key_type == "private":
            version = '0x04b2430c' 
        else:
            print('Wallet type does not exist')

        key_hash = hashlib.new('ripemd160', key).digest()
        fingerprint = str(key_hash[0:4].hex())

        chain_code_str = str(chain_code.hex())

        key_str = str(key.hex())

      
        serialized_str = version + str(depth) + fingerprint + str(index) + chain_code_str + key_str
        checksum_hash = hashlib.sha256(hashlib.sha256(serialized).digest()).digest()
        checksum = checksum_hash[0:4]

        serialized = base58.b58encode(version + int_to_big_endian(depth, 4) + fingerprint + int_to_big_endian(index, 4) + chain_code + key + checksum).decode()
        return serialized



    def create_address(HDWalletTree, parent_node_id, index, type):

        '''
        Create_address function creates the Child Private Key based on ckd algorithm, derives the corresponding Child Public Key, produces a public address
        based on the Child Public Key, and adds the information to the most recent level of the tree. 

        Create_node is simply a method in the Treelib library that creates and assigns node objects in the tree heirarchy. However, create_node by itself does not 
        expose the child public address. Create_address uses the derive_key method to deterministically expose the public address of a child key, given the parent public address. 
        '''
        
        [chain_code, privatekey] = WalletClass.derive_key(parent_node_id)
        [CKD_object, ckd_priv_key] = ChildPrivateKey(privatekey, chain_code, index).ckdpriv() 
        #[CKD_object, ckd_pub_key] = ChildPublicKey(privatekey, chain_code, index).ckdpub()

        '''
        After further analysis, the below function is true and safe for all situations. What we cannot do is derive a hardened child public key from the parent public key. 
        Most importantly, we need to ensure an attacker does not get ahold of both the parent public key and the non-hardened child private key. They could unlock the entire
        wallet from these two pieces. Therefore, a key requirement is ensuring that only hardened child private keys are created for accounts.  
        '''
        xpubkey = priv_to_pub_ecdsa(ckd_priv_key) # Temporarily use this until we can figure out ckd algorithm for deriving child public key from master public key. 
        xpubaddress = addrTypeDict[type](xpubkey)
    
        # Check if number of # of branches for node related to this 
        HDWalletTree.create_node(xpubaddress, xpubaddress, parent=parent_node_id, data=Node_Data(
            publickey = xpubkey,
            pubaddress = xpubaddress,
            btc_balance = 0,
            parentnode = parent_node_id,
            childnode = None,
            branches = 0,
            index = index + 1
        ))
        return [HDWalletTree, xpubaddress]


    def derive_key(public_address):

        '''
        This function derives a private key corresponding to a public address, via the 24 word seed phrase. 
        ''' 
        try:
            with open('wallet/masterkey.pkl', 'rb') as file1:
                master_privkey = dill.load(file1)
                chain_code = dill.load(file1)
            with open('wallet/wallet.pkl', 'rb') as file2:
                HDWalletTree = dill.load(file2)
                receive_change = dill.load(file2)
                receiving_dict = dill.load(file2)
                change_dict = dill.load(file2)
        except:
            print("Master key does not exist")

        # Derive 44' Purpose level from master private key
        purpose_44 = ChildPrivateKey(master_privkey, chain_code, HARDENED).ckdpriv()
        priv_key = purpose_44[1]
        chain_code = purpose_44[0].chain_code

        # Derive 0' Coin Type level from Purpose private key
        coin_type = ChildPrivateKey(priv_key, chain_code, HARDENED).ckdpriv()
        priv_key = coin_type[1]
        chain_code = coin_type[0].chain_code

        # Derive 0' Account level from Coin Type private key
        account =  ChildPrivateKey(priv_key, chain_code, HARDENED).ckdpriv()
        priv_key = account[1]
        chain_code = account[0].chain_code

        # Derive Receive and Change root addresses
        receive_root = ChildPrivateKey(priv_key, chain_code, 1).ckdpriv()
        receive_priv_key = receive_root[1]
        receive_chain_code = receive_root[0].chain_code
        change_root = ChildPrivateKey(priv_key, chain_code, 2).ckdpriv()
        change_priv_key = change_root[1]
        change_chain_code = change_root[0].chain_code

        # Derive desired private key
        # Need 2 pieces of information: 1) whether address is a receiving or change address. 2) Address index
        # Can parse the two dictionaries for a matching public address. Easy to return index, but difficult to return whether receiving or change. 


        # If no receiving keys have been created yet, then the private key is the 1st child private key of the receiving root address. 
        if len(receiving_dict) == 0:
            new_key = ChildPrivateKey(receive_priv_key, receive_chain_code, 1).ckdpriv()
            priv_key = new_key[1]
            chain_code = new_key[0].chain_code
        # If the public address is the receive address? Then the private key is the receiving root address private key. 
        elif public_address == receive_change[0]:
            priv_key = receive_priv_key
            chain_code = receive_root[0].chain_code
        # If the public address is the change address? Then the private key is the change root address private key. 
        elif public_address == receive_change[1]:
            priv_key = change_priv_key
            chain_code = change_root[0].chain_code
        # Case when receiving dictionary has keys populated.         
        else:
            for k,v in receiving_dict.items():
                if v == public_address:
                    new_key = ChildPrivateKey(receive_priv_key, receive_chain_code, k).ckdpriv()
                else:
                    continue
            for k,v in change_dict.items():
                if v == public_address:
                    new_key = ChildPrivateKey(change_priv_key, change_chain_code, k).ckdpriv()
            priv_key = new_key[1]
            chain_code = new_key[0].chain_code

        return [chain_code, priv_key]    


    def build_txn_object(address_list, prev_txn_list, prev_index_list, target_address, change_address, target_amount, btc_balance):

        '''
        This function uses the multiple in, 2 out BTC txn template. The 2 outputs are the target address and the 
        HD wallet change address. The output is a signed raw transaction object which only needs to be broadcasted.  
        '''
        txn_ins = []
        txn_outs = []
        change_amount = btc_balance - (target_amount + WalletClass.fee_estimate())

        count = 0
        for i in prev_txn_list:
            txn_ins.append(TxIn(prev_txn_list[count], prev_index_list[count]))
            count += 1
    
        '''Outputs TxOut for target address'''
        h160 = decode_base58(target_address)
        script_pubkey = p2pkh_script(h160)
        target_satoshis = int(target_amount)
        txn_outs.append(TxOut(target_satoshis, script_pubkey))

        '''Outputs TxOut for change address'''
        h160 = decode_base58(change_address)
        script_pubkey = p2pkh_script(h160)
        change_satoshis = int(change_amount)
        txn_outs.append(TxOut(change_satoshis, script_pubkey))

        '''Builds the raw transaction data object'''
        txn_obj = Tx(1, txn_ins, txn_outs, 0, testnet=False)
    
        return txn_obj

        

    def balance_total(tree, receiving, change):

        balance = 0
        for key in receiving:
            address_balance = getattr(tree.get_node(receiving[key]).data, 'btc_balance')
            balance = balance + address_balance
        for key in change:
            address_balance = getattr(tree.get_node(change[key]).data, 'btc_balance')
            balance = balance + address_balance
        
        return balance

    def fee_estimate():

        fee_data = requests.get("https://mempool.space/api/v1/fees/recommended").json()
        recommended_fee = fee_data['fastestFee']
        fee = recommended_fee * 250
        return fee

    
# Data Structure for Nodes

class Node_Data(object):

    def __init__(self, publickey, pubaddress, btc_balance: int, parentnode, childnode, branches: int, index: int):
        self.publickey = publickey
        self.pubaddress = pubaddress
        self.btc_balance = btc_balance
        self.parentnode = parentnode     # The public key of the parent node.
        self.childnode = childnode       # The public key of the child node.
        self.branches = branches         # The counter for number of child nodes attached to this node.
        self.index = index               # The index level this node resides at.


cli.add_command(recover_wallet)
cli.add_command(create_wallet)
cli.add_command(balance)
cli.add_command(deposit)
cli.add_command(tree)
cli.add_command(sync_wallet)
cli.add_command(withdraw)
cli.add_command(display_txn)

if __name__ == "__main__":
    cli()