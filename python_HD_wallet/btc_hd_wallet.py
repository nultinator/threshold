from constants import *

# Import Python Tools
import dill
from pathlib import Path
import requests
import click
from treelib import *
import secrets
from typing import Union

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
def new_wallet():
    """Create a new wallet"""

    path_to_file = 'mywallet_dill.pkl'
    path = Path(path_to_file)
    if path.is_file():        # .is_file() method returns 'True' if file already exists. 
        print('Wallet already exists. Cannot create new wallet.')
    else:
        random_string = secrets.token_hex()
        mnemonic_new = WalletClass.generate(strength=256)
        seed_new = WalletClass.bip39_seed_from_mnemonic(mnemonic_new, random_string)
        [master_priv_key, chain_code] = WalletClass.master_key(seed_new)
        master_pub_key = priv_to_pub_ecdsa(master_priv_key)
        master_pub_address = pubkey_to_address(master_pub_key)
        # Create the Root Node:
        HDWalletTree = Tree()
        HDWalletTree.create_node(master_pub_address, master_pub_address, parent=None, data=Node_Data(
            publickey = master_pub_key,
            privatekey = master_priv_key,
            pubaddress = master_pub_address,
            btc_balance = 0,
            parentnode = None,
            childnode = None,
            branches = 0,
            index = 1, 
            chain_code = chain_code
        )) 

        # Create 44' Purpose level from master private key
        purpose_44 = WalletClass.create_address(HDWalletTree, master_pub_address, HARDENED)

        # Create 0' Coin Type level from Purpose private key
        coin_type = WalletClass.create_address(HDWalletTree, purpose_44[1], HARDENED)

        # Create 0' Account level from Coin Type private key
        account =  WalletClass.create_address(HDWalletTree, coin_type[1], HARDENED)

        # Create Recieving and Change Root Nodes
        # receive_change = [receive root address, change root address]
        receive_change = []
        while getattr(HDWalletTree.get_node(account[1]).data, 'branches') < BRANCHES_PER_ACCOUNT:
            branches_counter = getattr(HDWalletTree.get_node(account[1]).data, 'branches')
            child = WalletClass.create_address(HDWalletTree, account[1], branches_counter)
            branches_counter += 1
            setattr(HDWalletTree.get_node(account[1]).data, 'branches', branches_counter)   # Iterate node creation until 3 child nodes are created
            receive_change.append(child[1])

        # Create data structures for modifying tree object
        # receiving_dict = {index1:'address1', index2:'address2', index3:'address3', ...}
        # change_dict = {index1:'address1', index2:'address2', index3:'address3', ...}
        receiving_dict = {}
        change_dict = {}

        # Display relevant information to user
        print("24 Word Mnemonic:" + " " + mnemonic_new)
        
        # Serialize and save relevant objects + data structures
        with open('mywallet_dill.pkl', 'wb') as file:
            dill.dump(HDWalletTree, file)
            dill.dump(receive_change, file)
            dill.dump(receiving_dict, file)
            dill.dump(change_dict, file)


'''
Display Wallet BTC balance

User input parameters: None
Expected behavior: Wallet displays total BTC amount.
If wallet not created, let user know. 
'''

#@click.command
#def display_balance(tree=HDWalletTree, receiving=receiving_dict, change=change_dict):
#    """Display wallet BTC balance"""
#    if os.getenv["WALLET_EXIST"] == 1:
#        print("Wallet does not exist. Please create a new wallet first.")
#    else:
#        btc_balance = WalletClass.balance_total(HDWalletTree, receiving_dict, change_dict)  # Set default input arguments in method definition to query total balance

#    print("BTC Balance:" + btc_balance)

'''
Transfer in BTC

User input parameters: None
Expected behavior: Wallet displays new public address for transferring BTC
If wallet not created, let user know. 
'''

@click.command()
def transfer_in():
    """Transfer BTC into wallet"""
    path_to_file = 'mywallet_dill.pkl'
    path = Path(path_to_file)
    # .is_file() method returns 'True' if file already exists. 
    if path.is_file():
        # Load object and data structures
        with open('mywallet_dill.pkl', 'rb') as file:
            mywallet = dill.load(file)
            receive_change = dill.load(file)
            receiving_dict = dill.load(file)
            change_dict = dill.load(file)

        receive_root = receive_change[0]
        
        if bool(receiving_dict):
            index = len(receiving_dict) + 1
            print('A')
        else:
            index = 1
            print('B')
        new = WalletClass.create_address(mywallet, receive_root, index)
        new_address = new[1]
        
        # Update receiving_dict
        new_entry = {index:new_address}
        receiving_dict.update(new_entry)

        # Save modified object and data structures back onto pickle file
        with open('mywallet_dill.pkl', 'wb') as file:  
            dill.dump(mywallet, file)
            dill.dump(receive_change, file)
            dill.dump(receiving_dict, file)
            dill.dump(change_dict, file)

        # Display to relevant information user
        print("Send only BTC to this address:" + " " + new_address)
    else:
        print('Wallet does not exist. Please run "new_wallet" command first.')



'''
Transfer out BTC

User input parameters: BTC Amount Requested, Target BTC Address
Expected behavior: Wallet displays Transaction ID associated with BTC transfer.
If wallet not created, let user know. 
'''

'''
Display past tansactions

User input parameters: None
Expected behavior: Wallet displays list of total Transaction IDs, sorted by timestamp. If no transactions, let user know. 
'''

#def display_txn():


#    print("Wallet Transaction History:")
#    print(" ")
#    print('wallet_transactions')

'''
Display current HD Wallet Hierarchy

User input parameters: None
Expected behavior: Wallet displays entire tree hierarchy. 
If wallet not created, let user know. 
'''

@click.command()
def wallet_hierarchy():
    """Display wallet hierarchy"""
    path_to_file = 'mywallet_dill.pkl'
    path = Path(path_to_file)
    # .is_file() method returns 'True' if file already exists. 
    if path.is_file():
        with open('mywallet_dill.pkl', 'rb') as f:
            mywallet = dill.load(f)
            mywallet.show()
    else:
        print('Wallet does not exist. Please run "new_wallet" command first.')


'''
End Core Front End Features
'''


# HD Wallet Key Derivation Path

# m (master priv/pub key) / 44' (purpose) / 0' (cointype - 0 for Bitcoin) / 0 ' (account) / 0 (recieving/change) / 0 (address_index)

""""
account - For each coin type, you can have multiple accounts. This is analogous to having multiple types of accounts in a bank (savings, checking, etc.) 
Under each account are generated addresses for recieving and and spending bitcoin, along with their change addresses. 

recieving/change - these two categories/root nodes are at the same depth. The recieving address recieves the BTC, and if a part of the BTC is sent out of the wallet,
the change address stores the unsent portion. The reason for a change address is to anonymize addresses from the sender. 

"""

# Need to update this function so it can handle a variable number of input txns, a variable number of output target addresses, and the equivalent number of change addresses. 

# prev_txn_dict = {prev_txn : prev_index}   key = prev_txn, value = prev_index
# keypair_dict = {pub_address : priv_key}
# target_list = []
# change_list =[]


def traverse_tree(HDWalletTree):

    HDWalletTree.expand_tree(nid=None, mode=1, filter = lambda x: getattr(HDWalletTree.get_node(x).data, 'btc_balance') != 0, key=None, reverse=False, sorting=True)


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

    def bip39_seed_from_mnemonic(mnemonic: str, password: str = "1129") -> bytes:
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
        '''

        privatekey = getattr(HDWalletTree.get_node(parent_node_id).data, 'privatekey')
        chain_code = getattr(HDWalletTree.get_node(parent_node_id).data, 'chain_code')
        [CKD_object, ckd_priv_key] = ChildPrivateKey(privatekey, chain_code, index).ckdpriv()  

        #xpubkey = ChildPublicKey(privatekey, chain_code, index).ckdpub()
        xpubkey = priv_to_pub_ecdsa(ckd_priv_key) # Temporarily use this until we can figure out ckd algorithm for deriving child public key from master public key. 
        xpubaddress = pubkey_to_address(xpubkey)

        # Check if number of # of branches for node related to this 
        HDWalletTree.create_node(xpubaddress, xpubaddress, parent=parent_node_id, data=Node_Data(
            publickey = xpubkey,
            privatekey = ckd_priv_key,
            pubaddress = xpubaddress,
            btc_balance = 0,
            parentnode = parent_node_id,
            childnode = None,
            branches = 0,
            index = index + 1,
            chain_code = CKD_object.chain_code
        ))
        return [HDWalletTree, xpubaddress]


    def transfer_out(btc_amount, target_address):

        '''
        This function parses the child accounts until the requested BTC balance amount + necessary fees can be summed up. 
        '''
        address_list = []
        balance_list = []
        '''
        Parse the dictionary stored BTC addresses for requisite BTC balance in the receiving addresses 
        '''
        if WalletClass.balance_total < btc_amount:                         # Ensures no infinite while loop due to wallet BTC balance < requested BTC amount. 
            print("Requested BTC amount exceeds wallet balance") 
        else:
            while sum(balance_list) < btc_amount + WalletClass.fee_estimate():   
                index = 1
                value = receiving_dict[index]
                balance = getattr(HDWalletTree.get_node(value).data, 'btc_balance')
                index += 1
                if balance > 0:
                    address_list.append(value)
                    balance_list.append(balance)

        WalletClass.build_txn_object()

        # Once parsed BTC amount > requested amount, build a txn object using # of inputs vs # of outputs
        print("Transaction ID:")


    def build_txn_object(prev_txn_dict, keypair_dict, target_address, change_address, target_amount, btc_balance):

        '''
        This function uses the multiple in, 2 out BTC txn template. The 2 outputs are the target address and the 
        HD wallet change address. The output is a signed raw transaction object which only needs to be broadcasted.  
        '''

        txn_ins = []
        txn_outs = []
        change_amount = btc_balance - (target_amount + fee_estimate())

        for key, value in prev_txn_dict.items():
            txn_ins.append(TxIn(bytes.fromhex(key), value))
    
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


    def fee_estimate(prev_txn_dict, target_address, change_address, target_amount, btc_balance):
    
        fee_data = requests.get("https://bitcoinfees.earn.com/api/v1/fees/recommended").json()
        recommended_fee = fee_data['fastestFee']

        txn_ins = []
        txn_outs = []
        change_amount = btc_balance - target_amount

        for key, value in prev_txn_dict.items():
            txn_ins.append(TxIn(bytes.fromhex(key), value))
    
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

        return [txn_size, recommended_fee]

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

    @classmethod
    def balance_total(tree, receiving, change):

        balance = 0
        for value in receiving:
            address_balance = getattr(tree.get_node(value).data, 'btc_balance')
            balance = balance + address_balance
        for value in change:
            address_balance = getattr(tree.get_node(value).data, 'btc_balance')
            balance = balance + address_balance
        
        return balance


# Child Key Derivation Functions

# To construct the HD wallet, CKD functions have to be run for 3 scenarios:
# 1) Parent Extended Private Key --> Normal Child Extended Private Key (index <= 2^31)
# 2) Parent Extended Private Key --> Hardened Child Extended Private Key (index > 2^31)
# 3) Parent Extended Public Key --> Normal Child Extended Public Key (index <= 2^31)
# Note: it is not possible to derive the hardened child extended public keys  

# Function ckdpub is used for scenario 3. Function ckdpriv is used for scenarios 1 and 2.  

class ChildPublicKey(object):

    def __init__(self, parentpriv, chain_code: bytes, HDWalletTree, key: ecdsa.VerifyingKey):

        # Initiates private key objects for master private key and subsequent children keys

        self.childpriv = None
        self.parentpriv = parentpriv
        self.chain_code = chain_code
        self.index = HDWalletTree.depth()
        self.K = key
    
    def point(self) -> ecdsa.ellipticcurve.Point:

        return self.K.pubkey.point

    def from_point(cls, point: Point_or_PointJacobi):

        return cls(ecdsa.VerifyingKey.from_public_point(point, curve=SECP256k1))
    
    def ckdpub(self, parentpriv, chain_code, index: int):
    
        # The function for calculating a child public key is the same as CKD Private Key up to the hmac_sha512 input 
        # and division of output into left and right 32 bytes. 
        # Afterwards, the difference is in the left 32 bytes 

        parentpub = priv_to_pub_ecdsa(parentpriv)
        if index >= HARDENED:
            raise RuntimeError("failure: hardened child for public ckd")
        data = bytearray(parentpub, 'utf-8')+(int_to_big_endian(index, 4))
        I = hmac_sha512(chain_code, msg=data)
        IL, IR = I[:32], I[32:]
        if big_endian_to_int(IL) >= CURVE_ORDER:
            InvalidKeyError(
                "public key {} is greater/equal to curve order".format(
                    big_endian_to_int(IL)
                )
            )
        aa = big_endian_to_int(IL)
        point = ecdsa.VerifyingKey.point(aa) 
        print(point)
        point1 = self.K.pubkey.point
        print(point1)

        if point == INFINITY:
            raise InvalidKeyError("public key is a point at infinity")
        childpub_object = self.__class__(
            chain_code = IR,
            index = index,
            parentpriv = parentpriv
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
            # data = bytearray(parentpub, 'utf-8')+(int_to_big_endian(self.index, 4)) # If not hardened, data concatenates the public key serialization and index. 
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

    def __init__(self, publickey, privatekey, pubaddress, btc_balance: int, parentnode, childnode, branches: int, index: int, chain_code):
        self.publickey = publickey
        self.privatekey = privatekey
        self.pubaddress = pubaddress
        self.btc_balance = btc_balance
        self.parentnode = parentnode     # The public key of the parent node.
        self.childnode = childnode       # The public key of the child node.
        self.branches = branches         # The counter for number of child nodes attached to this node.
        self.index = index               # The index level this node resides at.
        self.chain_code = chain_code


cli.add_command(new_wallet)
cli.add_command(transfer_in)
cli.add_command(wallet_hierarchy)

if __name__ == "__main__":
    cli()