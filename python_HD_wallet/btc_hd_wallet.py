from constants import *

# Import Python Tools
import dill
from pathlib import Path
import requests
import click
from treelib import *
import secrets
from typing import Union
import json

# Import Python Crypto Libraries
from helper import *
from ecc import *
from txn import *
from script import *
from op import *
import secrets
import unicodedata
import base58
from mnemonic import Mnemonic
from bitcoinrpc.authproxy import AuthServiceProxy, JSONRPCException


SECP256k1 = ecdsa.curves.SECP256k1
CURVE_GEN = ecdsa.ecdsa.generator_secp256k1
CURVE_ORDER = CURVE_GEN.order()
FIELD_ORDER = SECP256k1.curve.p()
INFINITY = ecdsa.ellipticcurve.INFINITY
Point_or_PointJacobi = Union[
    ecdsa.ellipticcurve.Point, 
    ecdsa.ellipticcurve.PointJacobi
]

#G = S256Point(gx, gy)

class InvalidKeyError(Exception):
    """Raised when derived key is invalid"""

mnemo = Mnemonic("english")


'''
Below functions represent the future core front-end features. Each of these functions will have Click decorators attached to allow for CLI use. 
A help menu will be written to facilitate the user in using the wallet. 
'''

'''
Create a new Wallet

User input parameters: None
Expected behavior: New wallet initialized with base BTC hierarchy. 24 word mnemonic displayed for user. 
If wallet already exists, then program cannot create a new wallet. 
'''

@click.group()
def cli():
    pass
    

@click.command()
def connectnode():
    """Test Node Connection"""
    rpc_user = 'bitcoinrpc'
    rpc_password = 'simayi112'
    rpc_connection = AuthServiceProxy("http://bitcoinrpc:simayi1129@ec2-44-192-121-159.compute-1.amazonaws.com:8332")
    best_block_hash = rpc_connection.getbestblockhash()
    print(rpc_connection.getblock(best_block_hash))
     

@click.command()
@click.option('--password', help='User selected password')
def newwallet(password):
    """Create a new wallet"""

    walletpath_to_file = 'HDWalletTree_dill.pkl'
    masterkeypath_to_file = 'masterkey.pkl'
    wallet_path = Path(walletpath_to_file)
    masterkey_path = Path(masterkeypath_to_file)
    if wallet_path.is_file() or masterkey_path.is_file():        # .is_file() method returns 'True' if file already exists. 
        print('Wallet or Master Key already exists. Cannot create new wallet.')
    else:
        mnemonic_new = WalletClass.generate(strength=256)
        seed_new = WalletClass.bip39_seed_from_mnemonic(mnemonic_new, password)
        [master_priv_key, chain_code] = WalletClass.master_key(seed_new)
        master_pub_key = priv_to_pub_ecdsa(master_priv_key)
        master_pub_address = pubkey_to_address(master_pub_key)
        
        # Save the master key information on device to use later
        with open('masterkey.pkl', 'wb') as file:
            dill.dump(master_priv_key, file)
            dill.dump(chain_code, file)
            dill.dump(master_pub_key, file)
            dill.dump(master_pub_address, file)

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
        purpose_44 = ChildPrivateKey(master_priv_key, chain_code, HARDENED).ckdpriv()  
        purpose_44_pubkey = priv_to_pub_ecdsa(purpose_44[1]) # Temporarily use this until we can figure out ckd algorithm for deriving child public key from master public key. 
        purpose_44_pubaddress = pubkey_to_address(purpose_44_pubkey)
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
        coin_type_pubaddress = pubkey_to_address(coin_type_pubkey)
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
        account_level_pubaddress = pubkey_to_address(account_level_pubkey)
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
        # receive_change = [receive root address, change root address]
        receive_change = []

        count = 1
        for i in range(BRANCHES_PER_ACCOUNT):
            receive_change_level = ChildPrivateKey(account_level[1], account_level[0].chain_code, count).ckdpriv() 
            count += 1
            receive_change_pubkey = priv_to_pub_ecdsa(receive_change_level[1]) # Temporarily use this until we can figure out ckd algorithm for deriving child public key from master public key. 
            receive_change_pubaddress = pubkey_to_address(receive_change_pubkey)
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

        # Create data structures for modifying tree object
        receiving_dict = {}
        change_dict = {}

        # Display relevant information to user
        print("24 Word Mnemonic:" + " " + mnemonic_new)
        
        # Serialize and save relevant objects + data structures
        with open('HDWalletTree_dill.pkl', 'wb') as file:
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
    path_to_file = 'HDWalletTree_dill.pkl'
    path = Path(path_to_file)
    # .is_file() method returns 'True' if file already exists. 
    if path.is_file():
        with open('HDWalletTree_dill.pkl', 'rb') as file:
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

        btc_balance = to_btc(WalletClass.balance_total(HDWalletTree, receiving_dict, change_dict))   
        print("BTC Balance:" + " " + str(btc_balance))     
    else:
        print('Wallet does not exist. Please run the "newwallet" command to create a wallet.')

'''
Transfer in BTC

User input parameters: None
Expected behavior: Wallet displays new public address for transferring BTC
If the wallet was never created, let user know. 
'''

@click.command()
def transferin():
    """Transfer BTC into wallet"""
    path_to_file = 'HDWalletTree_dill.pkl'
    path = Path(path_to_file)
    # .is_file() method returns 'True' if file already exists. 
    if path.is_file():
        # Load object and data structures
        with open('HDWalletTree_dill.pkl', 'rb') as file:
            HDWalletTree = dill.load(file)
            receive_change = dill.load(file)
            receiving_dict = dill.load(file)
            change_dict = dill.load(file)

        receive_root = receive_change[0]
        
        '''
        Determine index and create a new address. Note: only hardened child addresses are being created for improved security. 
        '''
        if bool(receiving_dict):
            # Workflow if wallet already has receiving addresses
            i = list(receiving_dict.values())
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
                new = WalletClass.create_address(HDWalletTree, receive_root, index)
                new_address = new[1]
                new_entry = {index:new_address}
                receiving_dict.update(new_entry)
                print("Send only BTC to this address:" + " " + new_address)
                # No need to increment index by 1, since the create address function automatically increments by 1 
                # when it creates the data object for the new node. 
        else:
            # Workflow if no receiving addresses have been created at all (brand new wallet)
            index = HARDENED
            new = WalletClass.create_address(HDWalletTree, receive_root, index)
            new_address = new[1]
            new_entry = {index:new_address}
            receiving_dict.update(new_entry)
            print("Send only BTC to this address:" + " " + new_address)

        # Save modified object and data structures back onto pickle file
        with open('HDWalletTree_dill.pkl', 'wb') as file:  
            dill.dump(HDWalletTree, file)
            dill.dump(receive_change, file)
            dill.dump(receiving_dict, file)
            dill.dump(change_dict, file)

    else:
        print('Wallet does not exist. Please run the "newwallet" command to create a wallet.')


'''
Transfer out BTC

User input parameters: BTC Amount Requested, Target BTC Address
Expected behavior: Wallet displays Transaction ID associated with BTC transfer.
If the wallet was never created, let user know. 

NOTE: Need a feature that automatically detects the type of address a user inputs. 
Then reflects type back to user (i.e. BTC address, Ethereum address, etc.)
'''

@click.command()
@click.option('--btc_amount', help='Requested BTC transfer amount')
@click.option('--target_address', help='Target Transfer Address')
def transferout(btc_amount, target_address):
    """Transfer BTC from wallet"""  
    '''
    NOTE: All BTC amounts converted into Satoshi for consistency! 
    '''
    path_to_file = 'HDWalletTree_dill.pkl'
    path = Path(path_to_file)
    # .is_file() method returns 'True' if file already exists. 
    if path.is_file():
        # Load object and data structures
        with open('HDWalletTree_dill.pkl', 'rb') as file:
            HDWalletTree = dill.load(file)
            receive_change = dill.load(file)
            receiving_dict = dill.load(file)
            change_dict = dill.load(file)

        '''
        This function parses the child accounts until the requested BTC balance amount + necessary fees can be summed up. 
        '''
        address_list = []
        balance_list = []
        prev_txn_list = []
        prev_index_list = []
        txn_ins = []
        btc_balance = to_sats(WalletClass.balance_total(HDWalletTree, receiving_dict, change_dict))

        '''
        Parse the receiving only dictionary storing the BTC addresses for requisite BTC balance in the receiving addresses 
        While parsing, append corresponding address and balance in the address and balance lists. 
        '''
        if btc_balance < to_sats(btc_amount):      # Ensures no infinite while loop due to wallet BTC balance < requested BTC amount. 
            print("Requested BTC amount exceeds wallet balance") 
        else:
            while sum(balance_list) < to_sats(btc_amount) + WalletClass.fee_estimate():   
                count = 1
                value = receiving_dict[count]
                balance = to_sats(getattr(HDWalletTree.get_node(value).data, 'btc_balance'))
                count += 1
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
            txn_info = requests.get("https://blockstream.info/api/tx/" + txn_id).json()
            for i in txn_info['vout']:
                if i['scriptpubkey_address'] == address:
                    return index_pos
                else:
                    index_pos += 1
            prev_index_list.append(index_pos)

        '''
        Create a new hardened change address for UTXO, regardless if change actually exists. 
        '''
        change_root = receive_change[1]
        if bool(change_dict):
            i = list(change_dict.values())
            index = getattr(HDWalletTree.get_node(i[-1]).data, 'index')
        else:
            index = HARDENED
        new = WalletClass.create_address(HDWalletTree, change_root, index)
        change_address = new[1]

        # Update change_dict with new public address
        new_entry = {index:change_address}
        change_dict.update(new_entry)
        

        # Create and sign transaction object
        txn_obj = WalletClass.build_txn_object(prev_txn_list, prev_index_list, target_address, change_address, btc_amount, btc_balance)
        print(txn_obj)
        for i in address_list:
            [chain_code, secret] = WalletClass.derive_key(i)
            private_key = PrivateKey(secret=secret)
            der = private_key.sign(txn_obj).der()   # Signing the transaction object
            print(der)
            sig = der + SIGHASH_ALL.to_bytes(1, 'big')
            print(sig)
            sec = private_key.point.sec()
            print(sec)
            script_sig = Script([sig, sec])
            print(script_sig)
            txn_obj.tx_ins[i].script_sig = script_sig
            print(txn_obj.serialize().hex())
    
    else:
        print('Wallet does not exist. Please run the "newwallet" command to create a wallet.')



'''
Display past tansactions

User input parameters: None
Expected behavior: Wallet displays list of historical Transaction IDs. This allows users to keep track of transfers in and out.  
Note: Bitcoin blocks and transactions do not have timestamps. Any "timestamps" would have to be generated from the application side.  
'''

@click.command()
def display_txn():
    """Display all past wallet transactions""" 
    txn_dict = {}    
    path_to_file = 'HDWalletTree_dill.pkl'
    path = Path(path_to_file)
    # .is_file() method returns 'True' if file already exists. 
    if path.is_file():
        # Load object and data structures
        with open('HDWalletTree_dill.pkl', 'rb') as file:
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

'''
Display current HD Wallet Hierarchy

User input parameters: None
Expected behavior: Wallet displays entire tree hierarchy. 
If the wallet was never created, let user know. 
'''

@click.command()
def tree():
    """Display wallet hierarchy"""
    path_to_file = 'HDWalletTree_dill.pkl'
    path = Path(path_to_file)
    # .is_file() method returns 'True' if file already exists. 
    if path.is_file():
        with open('HDWalletTree_dill.pkl', 'rb') as f:
            HDWalletTree = dill.load(f)
            HDWalletTree.show()
    else:
        print('Wallet does not exist. Please run the "newwallet" command to create a wallet.')


'''
Sync Wallet

User input parameters: None
Expected behavior: Wallet updates each child key BTC balance in the Tree Data object, using the blockchain as the source of truth. 
If the wallet was never created, let user know. 
'''

@click.command()
def syncwallet():
    """Sync wallet BTC amount"""
    path_to_file = 'HDWalletTree_dill.pkl'
    path = Path(path_to_file)
    # .is_file() method returns 'True' if file already exists. 
    if path.is_file():
        # Load object and data structures
        with open('HDWalletTree_dill.pkl', 'rb') as file:
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

        with open('HDWalletTree_dill.pkl', 'wb') as file:
            dill.dump(HDWalletTree, file)
            dill.dump(receive_change, file)
            dill.dump(receiving_dict, file)
            dill.dump(change_dict, file)

        print('Wallet sync successfully completed.')
    
    else:
        print('Wallet does not exist. Please run the "newwallet" command to create a wallet.')


'''
Set a Gap Limit of 20 keys in wallet recovery. The wallet will also limit address creation for transferring in 
by ensuring that a new address is not created unless the previous index address has UTXOs
'''

@click.command()
@click.option('--recovery_phrase', help='Enter your recovery phrase')
@click.option('--password', help='Enter your password')
def recover_wallet(recovery_phrase, password):
    """Recover wallet from seed phrase"""
    
    try: 
        # Create necessary data structures:
        # receive_change = [receive root address, change root address]
        receive_change = []
        receiving_dict = {}
        change_dict = {}

        walletpath_to_file = 'HDWalletTree_dill.pkl'
        masterkeypath_to_file = 'masterkey.pkl'
        wallet_path = Path(walletpath_to_file)
        masterkey_path = Path(masterkeypath_to_file)
        if wallet_path.is_file() or masterkey_path.is_file():        # .is_file() method returns 'True' if file already exists. 
            print('Wallet or Master Key already exists. Cannot create new wallet.')
        else:
            seed_new = WalletClass.bip39_seed_from_mnemonic(recovery_phrase, password)
            [master_priv_key, chain_code] = WalletClass.master_key(seed_new)
            master_pub_key = priv_to_pub_ecdsa(master_priv_key)
            master_pub_address = pubkey_to_address(master_pub_key)

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
            with open('masterkey.pkl', 'wb') as file:
                dill.dump(master_priv_key, file)
                dill.dump(chain_code, file)
                dill.dump(master_pub_key, file)
                dill.dump(master_pub_address, file)

            # Serialize and save relevant objects + data structures
            with open('HDWalletTree_dill.pkl', 'wb') as file:
                dill.dump(HDWalletTree, file)
                dill.dump(receive_change, file)
                dill.dump(receiving_dict, file)
                dill.dump(change_dict, file)
        

            # Create 44' Purpose level from master private key (Root Node):
            purpose_44 = ChildPrivateKey(master_priv_key, chain_code, HARDENED).ckdpriv()  
            purpose_44_pubkey = priv_to_pub_ecdsa(purpose_44[1]) # Temporarily use this until we can figure out ckd algorithm for deriving child public key from master public key. 
            purpose_44_pubaddress = pubkey_to_address(purpose_44_pubkey)
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
            coin_type_pubaddress = pubkey_to_address(coin_type_pubkey)
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
            account_level_pubaddress = pubkey_to_address(account_level_pubkey)
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
                receive_change_pubaddress = pubkey_to_address(receive_change_pubkey)
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
                new = WalletClass.create_address(HDWalletTree, receive_root, index)
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
                new = WalletClass.create_address(HDWalletTree, change_root, index)
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
        
            with open('HDWalletTree_dill.pkl', 'wb') as file:  
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
        :param mnemonic: mnemonic sentence
        :param password: password (default="")
        :return: bip39 seed
        """
        PBKDF2_ROUNDS = 2048
        mnemonic = unicodedata.normalize("NFKD", mnemonic)
        password = unicodedata.normalize("NFKD", password)
        passphrase = unicodedata.normalize("NFKD", "mnemonic") + password
        seed = hashlib.pbkdf2_hmac(
            "sha512",
            mnemonic.encode("utf-8"),
            passphrase.encode("utf-8"),
            PBKDF2_ROUNDS
            )
        return seed
        

    def master_key(bip39_seed: bytes) -> bytes:
       
        '''
        Function to generate Parent Extended Private Key from Mnemonic. Then check if extended private key is valid.
        '''

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

    def create_address(HDWalletTree, parent_node_id, index):

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
        xpubaddress = pubkey_to_address(xpubkey)
    
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
            with open('masterkey.pkl', 'rb') as file1:
                master_privkey = dill.load(file1)
                chain_code = dill.load(file1)
            with open('HDWalletTree_dill.pkl', 'rb') as file2:
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


    def build_txn_object(prev_txn_list, prev_index_list, target_address, change_address, target_amount, btc_balance):

        '''
        This function uses the multiple in, 2 out BTC txn template. The 2 outputs are the target address and the 
        HD wallet change address. The output is a signed raw transaction object which only needs to be broadcasted.  
        '''
        txn_ins = []
        txn_outs = []
        change_amount = btc_balance - (target_amount + WalletClass.fee_estimate(prev_txn_list, prev_index_list, target_address, change_address, target_amount, btc_balance))

        for txn_id in prev_txn_list.items():
            txn_ins.append(TxIn(bytes.fromhex(prev_txn_list(txn_id)), prev_index_list(txn_id)))
    
        '''Outputs TxOut for target address'''
        h160 = decode_base58(target_address)
        script_pubkey = p2pkh_script(h160)
        target_satoshis = int(target_amount * 100000000)
        txn_outs.append(TxOut(target_satoshis, script_pubkey))

        '''Outputs TxOut for change address'''
        h160 = decode_base58(change_address)
        script_pubkey = p2pkh_script(h160)
        change_satoshis = int(change_amount * 100000000)
        txn_outs.append(TxOut(change_satoshis, script_pubkey))

        '''Builds the raw transaction data object'''
        txn_obj = Tx(1, txn_ins, txn_outs, 0, testnet=False)
    
        return txn_obj


    def fee_estimate(prev_txn_list, prev_index_list, target_address, change_address, target_amount, btc_balance):
    
        fee_data = requests.get("https://mempool.space/api/v1/fees/recommended").json()
        recommended_fee = fee_data['fastestFee']

        txn_ins = []
        txn_outs = []
        change_amount = btc_balance - target_amount

        for txn_id in prev_txn_list.items():
            txn_ins.append(TxIn(bytes.fromhex(prev_txn_list(txn_id)), prev_index_list(txn_id)))
    
        '''Outputs TxOut for target address'''
        h160 = decode_base58(target_address)
        script_pubkey = p2pkh_script(h160)
        target_satoshis = int(target_amount * 100000000)
        txn_outs.append(TxOut(target_satoshis, script_pubkey))

        '''Outputs TxOut for change address'''
        h160 = decode_base58(change_address)
        script_pubkey = p2pkh_script(h160)
        change_satoshis = int(change_amount * 100000000)
        txn_outs.append(TxOut(change_satoshis, script_pubkey))

        '''Builds the raw transaction data object'''
        txn_obj = Tx(1, txn_ins, txn_outs, 0, testnet=False)

        ''' The transaction size in bytes is the length of the transaction raw data ''' 
        txn_size = len(txn_obj)
        fee = txn_size * recommended_fee
        return fee

    def create_change(HDWalletTree, root_change, change_dict):

        if bool(change_dict):
            index = len(change_dict) + 1
        else:
            index = 1

        new_change = WalletClass.create_address(HDWalletTree, root_change, index)
        new_address = new_change[1]
        new_entry = {index:new_address}
        change_dict.update(new_entry)

        return new_address

    def balance_total(tree, receiving, change):

        balance = 0
        for key in receiving:
            address_balance = getattr(tree.get_node(receiving[key]).data, 'btc_balance')
            balance = balance + address_balance
        for key in change:
            address_balance = getattr(tree.get_node(change[key]).data, 'btc_balance')
            balance = balance + address_balance
        
        return balance

'''
Child Key Derivation Functions

From BIP32 specification documentation: To construct the HD wallet, CKD functions have to be run for 3 scenarios:

1) Parent Extended Private Key --> Private Extended Child Key, Hardened (index >= 2^31) & Non-Hardened (index < 2^31)
       
2) Parent Extended Public Key --> Public Extended Child Key, Non-Hardened (index < 2^31) only
    Note: it is not possible to derive the hardened child extended public keys.  

3) Parent Extended Private Key --> Child Extended Public Key for Hardened & Non-Hardened
    Note: The resulting child public key cannot be used for signing transactions. Therefore, it is a "neutered version".


Basically, all private keys can be used to derive their corresponding public key, so there is no issue in using the priv_to_pub_ecdsa function, 
even for hardened child private keys to derive their corresponding hardened child public keys. What is not allowed, however, is deriving the hardened
child public key from the parent public key.   

The reason is that if an attacker got hold of the master public key and any one of the non-hardened child private keys, they can comprise the entire wallet. 
The attacker uses simple algebra to solve for the parent private key, which is equivalent to giving up the seed phrase:

child private key = (left 32 bytes + parent private key) % n
parent private key = (child private key - left 32 bytes) % n

Per the code below, an extended parent public key can be used to derive the left 32 bytes. However, a hardened child private key would not allow this because
the formula for calculating the left 32 bytes involve having the parent private key in hand. While this application is useful if the wallet owner needs to share public keys
with others (for example, have others create public addresses for them), this may also be applicable for attackers looking to attack hardware wallets. 
'''

class ChildPublicKey(object):

    def __init__(self, parentpriv, chain_code: bytes, index, key=ecdsa.VerifyingKey):

        # Initiates private key objects for master private key and subsequent children keys

        self.parentpriv = parentpriv
        self.chain_code = chain_code
        self.index = index
        self.K = key
    
    def point(self) -> ecdsa.ellipticcurve.Point:

        return self.K.pubkey.point

    def from_point(cls, point: Point_or_PointJacobi):

        return cls(ecdsa.VerifyingKey.from_public_point(point, curve=SECP256k1))
    
    def ckdpub(self):
    
        '''
        The function for calculating a child public key is the same as CKD Private Key up to the hmac_sha512 input 
        and division of output into left and right 32 bytes. 
        Afterwards, the difference is in the left 32 bytes 
        '''
        
        parentpub = priv_to_pub_ecdsa(self.parentpriv)
        if self.index >= HARDENED:
            raise RuntimeError("failure: hardened child for public ckd")
        data = parentpub + (int_to_big_endian(self.index, 4))
        I = hmac_sha512(self.chain_code, msg=data)
        IL, IR = I[:32], I[32:]
        if big_endian_to_int(IL) >= CURVE_ORDER:
            InvalidKeyError(
                "public key {} is greater/equal to curve order".format(
                    big_endian_to_int(IL)
                )
            )
        aa = big_endian_to_int(IL)
        #point = ecdsa.VerifyingKey.point(aa) 
        #print(point)
        point1 = self.K.pubkey.point
        print(point1)

        if point == INFINITY:
            raise InvalidKeyError("public key is a point at infinity")
        childpub_object = self.__class__(
            chain_code = IR,
            index = self.index,
            parentpriv = self.parentpriv
        )
        return [childpub_object]

class ChildPrivateKey(object):

    def __init__(self, parentpriv, chain_code, index):

        self.parentpriv = parentpriv
        self.chain_code = chain_code
        self.index = index

    def ckdpriv(self):
        parentpub = priv_to_pub_ecdsa(self.parentpriv)
        if self.index >= HARDENED:
                # data concatenates 3 things: 0x00 reflected as bytes, private key reflected as bytes,
                # and index reflected as bytes, with length 4. 
            data = b"\x00" + self.parentpriv + int_to_big_endian(self.index, 4)
        else:
            data = parentpub + (int_to_big_endian(self.index, 4))
        I = hmac_sha512(self.chain_code, msg=data)  # Run chain code and pubkey + index concatenation through SHA512
        IL, IR = I[:32], I[32:]
        if big_endian_to_int(IL) >= CURVE_ORDER:
            InvalidKeyError(
                "private key {} is greater/equal to curve order".format(
                    big_endian_to_int(IL)
                    )
                )
        ki = (int.from_bytes(IL, "big") + big_endian_to_int(bytes(self.parentpriv))) % CURVE_ORDER
        if ki == 0:
            InvalidKeyError("private key is zero")
        childpriv = int_to_big_endian(ki, 32)
        childpriv_object = self.__class__(
            parentpriv = self.parentpriv, 
            chain_code = IR,
            index = self.index
        )
        return [childpriv_object, childpriv]

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
cli.add_command(newwallet)
cli.add_command(balance)
cli.add_command(transferin)
cli.add_command(tree)
cli.add_command(syncwallet)
cli.add_command(transferout)
cli.add_command(display_txn)

if __name__ == "__main__":
    cli()