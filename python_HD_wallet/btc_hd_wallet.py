from constants import *

# Import Python Tools
import click
import itertools
import os
import parse
from treelib import *
import time
import string
import secrets

# Import Python Crypto Libraries

from helper import *
import secrets
import unicodedata
import base58
from mnemonic import Mnemonic


SECP256k1 = ecdsa.curves.SECP256k1
CURVE_GEN = ecdsa.ecdsa.generator_secp256k1
CURVE_ORDER = CURVE_GEN.order()
FIELD_ORDER = SECP256k1.curve.p()
INFINITY = ecdsa.ellipticcurve.INFINITY

class InvalidKeyError(Exception):
    """Raised when derived key is invalid"""

mnemo = Mnemonic("english")

def main():

    level_list = []
    node_list = []
    HDWalletTree = btc_initialize(256)
    print(" ")
    HDWalletTree.show()


# HD Wallet Key Derivation Path

# m (master priv/pub key) / 44' (purpose) / 0' (cointype - 0 for Bitcoin) / 0 ' (account) / 0 (recieving/change) / 0 (address_index)

a = ['recieving', 'change']
b = ['account']
c = ['cointype']
d = ['purpose']
deriv_path = ['m']
deriv_path.append(d)
deriv_path[len(deriv_path)-1].append(c)
deriv_path[len(deriv_path)-1].append(b)
deriv_path[len(deriv_path)-1].append(a)


print(deriv_path)

['m', ['purpose', ['cointype'], ['account'], ['recieving', 'change']]]

""""
account - For each coin type, you can have multiple accounts. This is analogous to having multiple types of accounts in a bank (savings, checking, etc.) 
Under each account are generated addresses for recieving and and spending bitcoin, along with their change addresses. 

recieving/change - these two categories/root nodes are at the same depth. The recieving address recieves the BTC, and if a part of the BTC is sent out of the wallet,
the change address stores the unsent portion. The reason for a change address is to anonymize addresses from the sender. 

"""

#def create_recieving():

#    return recieving


#def create_change():

#    return change

def btc_initialize(strength):
   
    # Initialization process generates the 24 word mnemonic, creates the bip39 seed, produces the master private & public keys, 
    # and sets up that key-pair as the root in the tree hierarchy. 

    random_string = secrets.token_hex()
    seed_new = Initialization.bip39_seed_from_mnemonic(Initialization.generate(strength), random_string)
    [master_priv_key, chain_code] = Initialization.master_key(seed_new)
    master_pub_key = priv_to_pub_ecdsa(master_priv_key)
    master_pub_address = pubkey_to_address(master_pub_key)
    HDWalletTree = Tree()
    # Create the Root Node:
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
    purpose_44 = create_address(HDWalletTree, master_pub_address, HARDENED)

    # Create 0' Coin Type level from Purpose private key
    coin_type = create_address(HDWalletTree, purpose_44[1], HARDENED)

    # Create 0' Account level from Coin Type private key
    account =  create_address(HDWalletTree, coin_type[1], HARDENED)

    # Create Recieving and Change Root Nodes
    while getattr(HDWalletTree.get_node(account[1]).data, 'branches') < BRANCHES_PER_ACCOUNT:
          branches_counter = getattr(HDWalletTree.get_node(account[1]).data, 'branches')
          child = create_address(HDWalletTree, account[1], branches_counter)
          branches_counter += 1
          setattr(HDWalletTree.get_node(account[1]).data, 'branches', branches_counter)   # Iterate node creation until 3 child nodes are created

    return HDWalletTree


def create_address(HDWalletTree, parent_node_id, index):

    # Create_address function creates the Child Private Key based on ckd algorithm, derives the corresponding Child Public Key, produces a public address
    # based on the Child Public Key, and adds the information to the most recent level of the tree. 

    privatekey = getattr(HDWalletTree.get_node(parent_node_id).data, 'privatekey')
    chain_code = getattr(HDWalletTree.get_node(parent_node_id).data, 'chain_code')
    [CKD_object, ckd_priv_key] = ChildPrivateKey(privatekey, chain_code, index).ckdpriv()   
    # xpubkey = ChildPublicKey(master_priv_key, chain_code, index).ckdpub()
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
   
# def transfer_out(btc_amount, transfer_address):

    # Transfer_out function parses the HD wallet tree, gathers the bitcoin addresses for sending out BTC, and transfers the BTC amount matching what the user requests.  
    # 
  #  Tree.get_level
   # return btc_transaction


class Initialization(object):

    # The Initialization class instantiates objects for creating the master private key.  

    def __init__(cls, strength, password):

        cls.strength = strength
        cls.password = password
        cls.key = []
        cls.chain_code = []

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
        print("24 Word Mnemonic:" + " " + mnemonic_new)
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
        

    # Function to generate Parent Extended Private Key from Mnemonic. Then check if extended private key is valid. 

    def master_key(bip39_seed: bytes) -> bytes:
       
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

if __name__ == "__main__":
    main()


   #def ckdpub(self, parentpriv, chain_code, index: int):
    
        # The function for calculating a child public key is the same as CKD Private Key up to the hmac_sha512 input 
        # and division of output into left and right 32 bytes. 
        # Afterwards, the difference is in the left 32 bytes 

     #   parentpub = priv_to_pub_ecdsa(parentpriv)
      #  if index >= HARDENED:
       #     raise RuntimeError("failure: hardened child for public ckd")
      #  data = bytearray(parentpub, 'utf-8')+(int_to_big_endian(index, 4))
      #  I = hmac_sha512(chain_code, msg=data)
      #  IL, IR = I[:32], I[32:]
      #  if big_endian_to_int(IL) >= CURVE_ORDER:
      #      InvalidKeyError(
      #          "public key {} is greater/equal to curve order".format(
      #              big_endian_to_int(IL)
      #              )
      #          )
        #aa = big_endian_to_int(IL)
        #point = ecdsa.VerifyingKey.point(aa) + 

        # self.K = key = ecdsa.VerifyingKey()
        # point = PrivateKey.parse(IL).K.point + xpubkey.public_key.point
        #if point == INFINITY:
     #       raise InvalidKeyError("public key is a point at infinity")
        #childpubkey = self.__class__(
            #key = PublicKey.from_point(point=point).sec(),
            #chain_code = IR,
           # index = index,
          #  parentpriv = parentpriv,
         #   parentpub = 
        #)
        #return childpubkey