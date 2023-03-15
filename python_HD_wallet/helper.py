# Import Python Crypto Libraries & Dev Tools
import hashlib
import hmac
import ecdsa
import codecs
import base58
import dill
from enum import Enum


SIGHASH_ALL = 1
SIGHASH_NONE = 2
SIGHASH_SINGLE = 3
BASE58_ALPHABET = '123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz'


# The hmac.new function from the hmac python library takes 3 arguments. 
# "key" refers to the private key used to authenticate the message. See glossary term on message authentication.  
# "msg" refers to the message being encrypted. 
# "digestmod" refers to the type of hashing algorithm being used (i.e. sha256, sha512)


def encode_int(i, nbytes, encoding='little'):
    """ encode integer i into nbytes bytes using a given byte ordering """
    return i.to_bytes(nbytes, encoding)

def update_files(HDWalletTree, receive_change, receiving_dict, change_dict):
    '''
    This helper function will save and then re-load the serialized files. 
    This is necessary at several points because some functions use the serialized files 
    as the source of truth. 
    '''    

    with open('wallet/wallet.pkl', 'wb') as file:  
            dill.dump(HDWalletTree, file)
            dill.dump(receive_change, file)
            dill.dump(receiving_dict, file)
            dill.dump(change_dict, file)

    with open('wallet/wallet.pkl', 'rb') as file:
            HDWalletTree = dill.load(file)
            receive_change = dill.load(file)
            receiving_dict = dill.load(file)
            change_dict = dill.load(file)


def to_sats(btc):
    sats = btc*100000000
    return sats

def to_btc(sats):
    btc = sats*(1/100000000)
    return btc

def hmac_sha512(key: bytes, msg: bytes) -> bytes:
    return hmac.new(key=key, msg=msg, digestmod=hashlib.sha512).digest()

def big_endian_to_int(b: bytes) -> int:
    return int.from_bytes(b, "big")

def int_to_big_endian(n: int, length: int) -> bytes:
    return n.to_bytes(length, "big")

def little_endian_to_int(b):
    '''little_endian_to_int takes byte sequence as a little-endian number.
    Returns an integer'''
    return int.from_bytes(b, 'little')

def int_to_little_endian(n, length):
    '''endian_to_little_endian takes an integer and returns the little-endian
    byte sequence of length'''
    return n.to_bytes(length, 'little')

def read_varint(s):
    '''read_varint reads a variable integer from a stream'''
    i = s.read(1)[0]
    if i == 0xfd:
        # 0xfd means the next two bytes are the number
        return little_endian_to_int(s.read(2))
    elif i == 0xfe:
        # 0xfe means the next four bytes are the number
        return little_endian_to_int(s.read(4))
    elif i == 0xff:
        # 0xff means the next eight bytes are the number
        return little_endian_to_int(s.read(8))
    else:
        # anything else is just the integer
        return i


def encode_varint(i):
    '''encodes an integer as a varint
    Varint refers to "variable-width integer". 
    '''

    if i < 0xfd:
        return bytes([i])
    elif i < 0x10000:
        return b'\xfd' + int_to_little_endian(i, 2)
    elif i < 0x100000000:
        return b'\xfe' + int_to_little_endian(i, 4)
    elif i < 0x10000000000000000:
        return b'\xff' + int_to_little_endian(i, 8)
    else:
        raise ValueError('integer too large: {}'.format(i))


def pub_to_legacy(pubkey):

    # Perform SHA-256 hashing on the public key. 
    # Perform RIPEMD-160 hashing on SHA-256 result:
    ripemd_hash = hashlib.new('ripemd160', hashlib.sha256(pubkey).digest()).digest()

    # Add version byte in front of RIPEMD-160 hash (0x00 for Main Network):
    extended_ripemd = b"\x00" + ripemd_hash

    # Perform SHA-256 on the extended RIPEMD-160 result. 
    # Perform SHA-256 hash on that SHA-256 result:
    double_sha256 = hashlib.sha256(hashlib.sha256(extended_ripemd).digest()).digest()

    # Take the first 4 bytes of the second SHA-256 hash. This is the address checksum.
    # Add the 4 checksum bytes from stage 7 at the end of extended RIPEMD-160 hash from stage 4. This is the 25-byte binary Bitcoin Address:
    binary_address = extended_ripemd + double_sha256[0:4]

    # Convert the result from a byte string into a base58 string using Base58Check encoding:
    p2pkh_address = base58.b58encode(binary_address).decode()
    return p2pkh_address


# IMPORTANT: This function outputs the SEC format uncompressed public key with the 04 marker and 32 bytes for x, and 32 bytes for y. 
def priv_to_pub_ecdsa(priv_key) -> bytes:      

    #private_key_bytes = codecs.decode(priv_key, 'hex') commenting out because input arguments are in byte format, rather than hex. 
    public_key_raw = ecdsa.SigningKey.from_string(priv_key, curve=ecdsa.SECP256k1).verifying_key
    public_key_bytes = public_key_raw.to_string()
    public_key_hex = codecs.encode(public_key_bytes, 'hex')
    pub_key = (b'04' + public_key_hex)
    return pub_key


def two_round_hash160(s):
    '''sha256 followed by ripemd160'''
    return hashlib.new('ripemd160', hashlib.sha256(s).digest()).digest()


def two_round_hash256(s):
    '''two rounds of sha256'''
    return hashlib.sha256(hashlib.sha256(s).digest()).digest()


def encode_base58(s):
    # determine how many 0 bytes (b'\x00') s starts with
    count = 0
    for c in s:
        if c == 0:
            count += 1
        else:
            break
    # convert to big endian integer
    num = int.from_bytes(s, 'big')
    prefix = '1' * count
    result = ''
    while num > 0:
        num, mod = divmod(num, 58)
        result = BASE58_ALPHABET[mod] + result
    return prefix + result


def encode_base58_checksum(s):
    return encode_base58(s + two_round_hash256(s)[:4])


# tag::source1[]
def decode_base58(s):
    num = 0
    for c in s:  # <1>
        num *= 58
        num += BASE58_ALPHABET.index(c)
    combined = num.to_bytes(25, byteorder='big')  # <2>
    checksum = combined[-4:]
    if two_round_hash256(combined[:-4])[:4] != checksum:
        raise ValueError('bad address: {} {}'.format(checksum, 
          two_round_hash256(combined[:-4])[:4]))
    return combined[1:-4]  # <3>
# end::source1[]


def bytes_to_WIF(s):
    '''Convert Private Key from bytes format to WIF format'''

    # convert bytes into 64 character, 32 byte, long hexadecimal format.
    privkey = s.hex() 

    # Add a 0x80 byte in front for mainnet address.
    privkey_80 = ('80' + privkey)

    # Perform two rounds of SHA-256 hash on the extended key.
    privkey_80_hashed = two_round_hash256(bytes.fromhex(privkey_80))

    # Take the first four bytes of the result (this is the checksum).  
    firstfour = privkey_80_hashed[0:4]

    # Add the checksum to the end of the extended key.
    stepsix = privkey_80 + firstfour.hex()

    # Convert the result into a base58 string using base58 encoding. This is the WIF format. 
    WIFformat = encode_base58(bytes.fromhex(stepsix))

    return WIFformat


def uncompress_to_compress(pubkey: bytes):
    '''Converts an uncompressed public key to compressed SEC version'''
    # Check if public key is uncompressed
    if len(pubkey) != 130:
        print('Public key is not in uncompressed SEC format')
    else:
        # Extract x & y coordinates from uncompressed public key
        x_coor = pubkey[2:66]
        y_coor = pubkey[66:]

        # Convert y to hex, check if y is even or odd.
        # Append the x coordinate in 32 bytes as big-endian integer to the appropriate prefix. 
        if int(y_coor.hex()) % 2 == 0:
            return b'\x02' + x_coor
        else:
            return b'\x03' + x_coor
    










    

    



    