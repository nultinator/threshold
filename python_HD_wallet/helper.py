import hashlib
import hmac
import ecdsa
import codecs
import base58


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