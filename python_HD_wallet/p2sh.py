# Import Python Crypto Libraries & Dev Tools
import hashlib

# Import Python HD Wallet Modules
from helper import *


def pub_to_p2sh(pubkey):

    # If the public key is uncompressed, then compress it first:
    if len(pubkey) == 130:
        pubkey = uncompress_to_compress(pubkey)

    # Compute SHA-256 hash and RIPEMD-160 hash of the compressed public key:
    step1 = hashlib.new('ripemd160', hashlib.sha256(pubkey).digest()).digest()

    # Build the redeem script: OP_0 PushData + <Step 1 result>. This redeem script also goes in signature 
    # script of a transaction while spending:
    redeemscript = b'\x00\x14' + step1

    # Compute SHA-256 hash of that script:
    step2 = hashlib.new('ripemd160', hashlib.sha256(redeemscript).digest()).digest()

    # Add P2SH version byte prefix for mainnet (05) and encode the result using Base-58 encoding with a checksum
    step3 = b'\x05' + step2
    return encode_base58_checksum(step3)