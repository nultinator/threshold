import hashlib
import hmac
import ecdsa
import codecs
import base58


SIGHASH_ALL = 1
SIGHASH_NONE = 2
SIGHASH_SINGLE = 3
BASE58_ALPHABET = '123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz'


# The hmac.new function from the hmac python library takes 3 arguments. 
# "key" refers to the private key used to authenticate the message. See glossary term on message authentication.  
# "msg" refers to the message being encrypted. 
# "digestmod" refers to the type of hashing algorithm being used (i.e. sha256, sha512)

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
    '''encodes an integer as a varint'''
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


def pubkey_to_address(pubkey):

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


def hash160(s):
    '''sha256 followed by ripemd160'''
    return hashlib.new('ripemd160', hashlib.sha256(s).digest()).digest()


def hash256(s):
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
    return encode_base58(s + hash256(s)[:4])


# tag::source1[]
def decode_base58(s):
    num = 0
    for c in s:  # <1>
        num *= 58
        num += BASE58_ALPHABET.index(c)
    combined = num.to_bytes(25, byteorder='big')  # <2>
    checksum = combined[-4:]
    if hash256(combined[:-4])[:4] != checksum:
        raise ValueError('bad address: {} {}'.format(checksum, 
          hash256(combined[:-4])[:4]))
    return combined[1:-4]  # <3>
# end::source1[]



    

    



    