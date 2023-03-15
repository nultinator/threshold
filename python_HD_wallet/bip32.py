# Import Python HD Wallet Modules
from helper import *
from ecc import *
from txn import *
from script import *
from op import *
from bech32 import *
from p2sh import *
from bip32 import *
from wallet import InvalidKeyError
from constants import *


SECP256k1 = ecdsa.curves.SECP256k1
CURVE_GEN = ecdsa.ecdsa.generator_secp256k1
CURVE_ORDER = CURVE_GEN.order()
FIELD_ORDER = SECP256k1.curve.p()
INFINITY = ecdsa.ellipticcurve.INFINITY


# Below functions are not tested to be functional yet. 

def to_xprv(self, *, net=None) -> str:
    payload = self.to_xprv_bytes(net=net)
    return EncodeBase58Check(payload)

def to_xprv_bytes(self, *, net=None) -> bytes:
    if not self.is_private():
        raise Exception("cannot serialize as xprv; private key missing")
    payload = (xprv_header(self.xtype, net=net) +
               bytes([self.depth]) +
               self.fingerprint +
               self.child_number +
               self.chaincode +
               bytes([0]) +
               self.eckey.get_secret_bytes())
    assert len(payload) == 78, f"unexpected xprv payload len {len(payload)}"
    return payload

def to_xpub(self, *, net=None) -> str:
    payload = self.to_xpub_bytes(net=net)
    return EncodeBase58Check(payload)

def to_xpub_bytes(self, *, net=None) -> bytes:
    payload = (xpub_header(self.xtype, net=net) +
               bytes([self.depth]) +
               self.fingerprint +
               self.child_number +
               self.chaincode +
               self.eckey.get_public_key_bytes(compressed=True))
    assert len(payload) == 78, f"unexpected xpub payload len {len(payload)}"
    return payload


def calc_fingerprint_of_this_node(self) -> bytes:
        """Returns the fingerprint of this node.
        Note that self.fingerprint is of the *parent*.
        """
        # TODO cache this
        return hash_160(self.eckey.get_public_key_bytes(compressed=True))[0:4]


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

    def __init__(self, parentpub: bytes, chain_code: bytes, index):

        # Initiates private key objects for master private key and subsequent children keys

        self.parentpub = parentpub
        self.chain_code = chain_code
        self.index = index
    
    def ckdpub(self):
    
        '''
        The function for calculating a child public key is the same as CKD Private Key up to the hmac_sha512 input 
        and division of output into left and right 32 bytes. 
        Afterwards, the difference is in the left 32 bytes 
        '''

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

        if point == INFINITY:
            raise InvalidKeyError("public key is a point at infinity")
        childpub_object = self.__class__(
            chain_code = IR,
            index = self.index,
            parentpriv = self.parentpriv
        )
        return [childpub_object]


class ChildPrivateKey(object):

    def __init__(self, parentpriv: bytes, chain_code: bytes, index):

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
