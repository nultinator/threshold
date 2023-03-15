# Import Python Crypto Libraries and Dev Tools
import json
import requests

# Import Python HD Wallet Modules
from io import BytesIO
from helper import *
from script import Script


def encode_int(i, nbytes, encoding='little'):
    """ encode integer i into nbytes bytes using a given byte ordering """
    return i.to_bytes(nbytes, encoding)


class TxFetcher:
    cache = {}

    @classmethod
    def get_url(cls, testnet=False):
        if testnet:
            return 'https://blockstream.info/testnet/api'
        else:
            return 'https://blockstream.info/api'

    @classmethod
    def fetch(cls, tx_id, testnet=False, fresh=False):
        if fresh or (tx_id not in cls.cache):
            url = '{}/tx/{}/hex'.format(cls.get_url(testnet), tx_id)
            response = requests.get(url)
            try:
                raw = bytes.fromhex(response.text.strip())
            except ValueError:
                raise ValueError('unexpected response: {}'.format(response.text))
            # make sure the tx we got matches to the hash we requested
            if raw[4] == 0:
                raw = raw[:4] + raw[6:]
                tx = Tx.parse(BytesIO(raw), testnet=testnet)
                tx.locktime = little_endian_to_int(raw[-4:])
            else:
                tx = Tx.parse(BytesIO(raw), testnet=testnet)
            if tx.id() != tx_id:
                raise ValueError('not the same id: {} vs {}'.format(tx.id(), tx_id))
            cls.cache[tx_id] = tx
        cls.cache[tx_id].testnet = testnet
        return cls.cache[tx_id]

    @classmethod
    def load_cache(cls, filename):
        disk_cache = json.loads(open(filename, 'r').read())
        for k, raw_hex in disk_cache.items():
            raw = bytes.fromhex(raw_hex)
            if raw[4] == 0:
                raw = raw[:4] + raw[6:]
                tx = Tx.parse(BytesIO(raw))
                tx.locktime = little_endian_to_int(raw[-4:])
            else:
                tx = Tx.parse(BytesIO(raw))
            cls.cache[k] = tx

    @classmethod
    def dump_cache(cls, filename):
        with open(filename, 'w') as f:
            to_dump = {k: tx.serialize().hex() for k, tx in cls.cache.items()}
            s = json.dumps(to_dump, sort_keys=True, indent=4)
            f.write(s)


class Tx:

    def __init__(self, version, tx_ins, tx_outs, locktime, testnet=False):
        self.version = version
        self.tx_ins = tx_ins
        self.tx_outs = tx_outs
        self.locktime = locktime
        self.testnet = testnet

    def encode(self, sig_index=-1) -> bytes:
        """
        Encode this transaction as bytes.
        If sig_index is given then return the modified transaction
        encoding of this tx with respect to the single input index.
        This result then constitutes the "message" that gets signed
        by the aspiring transactor of this input.
        """
        out = []
        # encode metadata
        # encode_int: encode integer i into nbytes bytes using a given byte ordering.
        # encode the version number into 4 nbytes
        out += [encode_int(self.version, 4)]       # assignment operator used on "out" list.
        out += [encode_varint(len(self.tx_ins))]  
        if sig_index == -1:
            # we are just serializing a fully formed transaction
            out += [tx_in.encode() for tx_in in self.tx_ins]
        else:
            # used when crafting digital signature for a specific input index
            out += [tx_in.encode(script_override=(sig_index == i))
                    for i, tx_in in enumerate(self.tx_ins)]
        # encode outputs
        out += [encode_varint(len(self.tx_outs))]
        out += [tx_out.encode() for tx_out in self.tx_outs]
        # encode... other metadata
        out += [encode_int(self.locktime, 4)]
        out += [encode_int(1, 4) if sig_index != -1 else b''] # 1 = SIGHASH_ALL
        return b''.join(out)   

    def __repr__(self):
        tx_ins = ''
        for tx_in in self.tx_ins:
            tx_ins += tx_in.__repr__() + '\n'
        tx_outs = ''
        for tx_out in self.tx_outs:
            tx_outs += tx_out.__repr__() + '\n'
        return 'tx: {}\nversion: {}\ntx_ins:\n{}tx_outs:\n{}locktime: {}'.format(
            self.id(),
            self.version,
            tx_ins,
            tx_outs,
            self.locktime,
        )

    def id(self):
        '''Human-readable hexadecimal of the transaction hash'''
        return self.hash().hex()

    def hash(self):
        '''Binary hash of the legacy serialization'''
        return two_round_hash256(self.serialize())[::-1]

    @classmethod
    def parse(cls, s, testnet=False):
        '''Takes a byte stream and parses the transaction at the start
        return a Tx object
        '''
        # s.read(n) will return n bytes
        # version is an integer in 4 bytes, little-endian
        version = little_endian_to_int(s.read(4))
        # num_inputs is a varint, use read_varint(s)
        num_inputs = read_varint(s)
        # parse num_inputs number of TxIns
        inputs = []
        for _ in range(num_inputs):
            inputs.append(TxIn.parse(s))
        # num_outputs is a varint, use read_varint(s)
        num_outputs = read_varint(s)
        # parse num_outputs number of TxOuts
        outputs = []
        for _ in range(num_outputs):
            outputs.append(TxOut.parse(s))
        # locktime is an integer in 4 bytes, little-endian
        locktime = little_endian_to_int(s.read(4))
        # return an instance of the class (see __init__ for args)
        return cls(version, inputs, outputs, locktime, testnet=testnet)

    def serialize(self):
        '''Returns the byte serialization of the transaction'''
        # serialize version (4 bytes, little endian)
        result = int_to_little_endian(self.version, 4)
        # encode_varint on the number of inputs
        result += encode_varint(len(self.tx_ins))
        # iterate inputs
        for tx_in in self.tx_ins:
            # serialize each input
            result += tx_in.serialize()
        # encode_varint on the number of outputs
        result += encode_varint(len(self.tx_outs))
        # iterate outputs
        for tx_out in self.tx_outs:
            # serialize each output
            result += tx_out.serialize()
        # serialize locktime (4 bytes, little endian)
        result += int_to_little_endian(self.locktime, 4)
        return result

    # tag::source1[]
    def fee(self):
        '''Returns the fee of this transaction in satoshi'''
        input_sum, output_sum = 0, 0
        for tx_in in self.tx_ins:
            input_sum += tx_in.value(self.testnet)
        for tx_out in self.tx_outs:
            output_sum += tx_out.amount
        return input_sum - output_sum
    # end::source1[]

    def sig_hash(self, input_index):
        '''Returns the integer representation of the hash that needs to get
        signed for index input_index'''
        # start the serialization with version
        # use int_to_little_endian in 4 bytes
        s = int_to_little_endian(self.version, 4)
        # add how many inputs there are using encode_varint
        s += encode_varint(len(self.tx_ins))
        # loop through each input using enumerate, so we have the input index
        for i, tx_in in enumerate(self.tx_ins):
            # if the input index is the one we're signing
            if i == input_index:
                # the previous tx's ScriptPubkey is the ScriptSig
                # Otherwise, the ScriptSig is empty
                # add the serialization of the input with the ScriptSig we want
                s += TxIn(
                    prev_tx = tx_in.prev_tx, 
                    prev_index = tx_in.prev_index,
                    # Below line calls the script_pubkey method in TxIn class. That method populates the empty script_sig with the previous 
                    # transaction's script_pubkey. 
                    script_sig = tx_in.script_pubkey(self.testnet),
                    sequence=tx_in.sequence,
                ).serialize()
            else:
                s += TxIn(
                    prev_tx = tx_in.prev_tx,
                    prev_index = tx_in.prev_index,
                    sequence = tx_in.sequence,
                ).serialize()
        # add how many outputs there are using encode_varint        
        s += encode_varint(len(self.tx_outs))
        for tx_out in self.tx_outs:
        # add the serialization of each output
            s += tx_out.serialize()
        # add the locktime using int_to_little_endian in 4 bytes
        s += int_to_little_endian(self.locktime, 4)
        # add SIGHASH_ALL using int_to_little_endian in 4 bytes
        s += int_to_little_endian(SIGHASH_ALL, 4)
        # hash256 the serialization
        h256 = hashlib.sha256(s).digest()
        # convert the result to an integer using int.from_bytes(x, 'big')
        return int.from_bytes(h256, 'big')
      

    def verify_input(self, input_index):
        '''Returns whether the input has a valid signature'''
        # get the relevant input
        tx_in = self.tx_ins[input_index]
        # grab the previous ScriptPubKey
        script_pubkey = tx_in.script_pubkey(testnet=self.testnet)
        # otherwise RedeemScript is None 
        # get the signature hash (z)
        # pass the RedeemScript to the sig_hash method
        z = self.sig_hash(input_index)
        # combine the current ScriptSig and the previous ScriptPubKey
        combined = tx_in.script_sig + script_pubkey
        # evaluate the combined script
        return combined.evaluate(z)

    # tag::source2[]
    def verify(self):
        '''Verify this transaction'''
        if self.fee() < 0:  # <1>
            return False
        for i in range(len(self.tx_ins)):
            if not self.verify_input(i):  # <2>
                return False
        return True
    # end::source2[]

    def sign_input(self, input_index, private_key):
        # get the signature hash (z)
        z = self.sig_hash(input_index)
        # get der signature of z from private key
        der = private_key.sign(z).der()
        # append the SIGHASH_ALL to der (use SIGHASH_ALL.to_bytes(1, 'big'))
        sig = der + SIGHASH_ALL.to_bytes(1, 'big')
        # calculate the sec
        sec = private_key.point.sec()
        # initialize a new script with [sig, sec] as the cmds
        script_sig = Script([sig, sec])
        # change input's script_sig to new script
        self.tx_ins[input_index].script_sig = script_sig
        # return whether sig is valid using self.verify_input
        return self.verify_input(input_index)

    def tx_id(self) -> str:
        '''Function for returning the Transaction ID of a completed transaction object'''
        return two_round_hash256(self.encode())[::-1].hex() # little/big endian conventions require byte order swap


class TxIn:

    def __init__(self, prev_tx, prev_index, script_sig=None, sequence=0xffffffff):
        self.prev_tx = prev_tx
        self.prev_index = prev_index
        if script_sig is None:
            self.script_sig = Script()
        else:
            self.script_sig = script_sig
        self.sequence = sequence

    def __repr__(self):
        return '{}:{}'.format(
            self.prev_tx.hex(),
            self.prev_index,
        )

    @classmethod
    def parse(cls, s):
        '''Takes a byte stream and parses the tx_input at the start
        return a TxIn object
        '''
        # prev_tx is 32 bytes, little endian
        prev_tx = s.read(32)[::-1]
        # prev_index is an integer in 4 bytes, little endian
        prev_index = little_endian_to_int(s.read(4))
        # use Script.parse to get the ScriptSig
        script_sig = Script.parse(s)
        # sequence is an integer in 4 bytes, little-endian
        sequence = little_endian_to_int(s.read(4))
        # return an instance of the class (see __init__ for args)
        return cls(prev_tx, prev_index, script_sig, sequence)

    def serialize(self):
        '''Returns the byte serialization of the transaction input'''
        # serialize prev_tx, little endian
        result = self.prev_tx[::-1]
        # serialize prev_index, 4 bytes, little endian
        result += int_to_little_endian(self.prev_index, 4)
        # serialize the script_sig
        '''
        Note: script_sig below is an instantiation of the Script class imported from script.py module. (self.script_sig = Script() in the constructor)
        "serialize" is also the name of a method within the Script class. Thus, it is using *that* method, not the method being defined in this block of code. 
        '''
        result += self.script_sig.serialize()
        # serialize sequence, 4 bytes, little endian
        result += int_to_little_endian(self.sequence, 4)
        return result

    def fetch_tx(self, testnet=False):
        return TxFetcher.fetch(self.prev_tx.hex(), testnet=False)

    def value(self, testnet=False):
        '''Get the outpoint value by looking up the tx hash
        Returns the amount in satoshi
        '''
        # use self.fetch_tx to get the transaction
        tx = self.fetch_tx(testnet=testnet)
        # get the output at self.prev_index
        # return the amount property
        return tx.tx_outs[self.prev_index].amount

    def script_pubkey(self, testnet=False):
        '''This function returns the ScriptPubKey of the previous transaction (prev_tx) by referencing the 
        previous transaction index (prev_index). 
        '''
        # use self.fetch_tx to get the transaction
        tx = self.fetch_tx(testnet=False)
        # get the output at self.prev_index
        # return the script_pubkey property
        #return tx.tx_outs[self.prev_index].script_pubkey
        #txn_info = requests.get("https://blockstream.info/api/tx/" + self.prev_tx.hex()).json()
        #count = 0
        #for i in txn_info['vout']:
        #    if count == self.prev_index:
        #        prev_tx_script_pubkey = i['scriptpubkey']
        #    count += 1
        return tx.tx_outs[self.prev_index].script_pubkey


    def encode(self, script_override=None):
        out = []
        out += [self.prev_tx[::-1]] # little endian vs big endian encodings... sigh
        out += [encode_int(self.prev_index, 4)]

        if script_override is None:
            # None = just use the actual script
            out += [self.script_sig.encode()]
        elif script_override is True:
            # True = override the script with the script_pubkey of the associated input
            out += [self.prev_tx_script_pubkey.encode()]
        elif script_override is False:
            # False = override with an empty script
            out += [Script([]).encode()]
        else:
            raise ValueError("script_override must be one of None|True|False")

        out += [encode_int(self.sequence, 4)]
        return b''.join(out)


class TxOut:

    def __init__(self, amount, script_pubkey):
        self.amount = amount
        self.script_pubkey = script_pubkey

    def __repr__(self):
        return '{}:{}'.format(self.amount, self.script_pubkey)

    @classmethod
    def parse(cls, s):
        '''Takes a byte stream and parses the tx_output at the start
        return a TxOut object
        '''
        # amount is an integer in 8 bytes, little endian
        amount = little_endian_to_int(s.read(8))
        # use Script.parse to get the ScriptPubKey
        script_pubkey = Script.parse(s)
        # return an instance of the class (see __init__ for args)
        return cls(amount, script_pubkey)

    def serialize(self):
        '''Returns the byte serialization of the transaction output'''
        # serialize amount, 8 bytes, little endian
        result = int_to_little_endian(self.amount, 8)
        # serialize the script_pubkey
        result += self.script_pubkey.serialize()
        return result

    def encode(self):
        out = []
        out += [encode_int(self.amount, 8)]
        out += [self.script_pubkey.encode()]
        return b''.join(out)
