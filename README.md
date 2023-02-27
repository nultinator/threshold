# Hierarchical Deterministic Wallet

## Setup

## Usage

#### Create a New Wallet

The `create-wallet` command creates a local wallet and outputs the 24-word mnemonic required for wallet recovery. This command also allows the user to optionally add in a password for extra security. If a local wallet already exists in the user's directory, this command will not create a new wallet. Instead, the user must delete the existing wallet files (delete the `HDWalletTree.dill.pkl` and `masterkey.pkl` files) before this command can create a new wallet. 

Create a wallet:

```
>> python3 wallet.py create-wallet

24 Word Mnemonic: cause question start option wheel auto hand razor razor scan paper nasty olive jeans category quarter elbow drill keen clerk simple market antenna tube
```

Optionally add in password for extra security in wallet recovery. Your password can be any combination of numbers, letters, and special characters, as long as it does not contain the exact same characters as linux/shell commands (i.e. && or ||):

```
>> python3 wallet.py create-wallet --password 12345_%NewWallet

24 Word Mnemonic: genius motor sauce control know spend neutral mercy surface benefit over steel dolphin fiction law festival motion spray mesh embark pyramid fun catch glide
```

#### Check Wallet Balance

For an existing wallet, the `balance` command outputs the wallet balance in BTC:

```
>> python3 wallet.py balance

BTC Balance: 0.0
```

#### Deposit BTC

For an existing wallet, you can generate a child BTC address for deposits. New child BTC addresses will not be generated unless an existing child BTC address has already had transactions on the blockchain:

```
>> python3 wallet.py deposit

Send only BTC to this address: 18LMcFA4C5ybAPchb4po1W8cQPHeue8SwW
```

#### Withdraw BTC

#### Sync Wallet Balance

For an existing wallet, the wallet needs to be sync'ed with the blockchain in order to display the correct wallet balance. This would be similar to a "Refresh" feature on front-end client:

```
>>> python3 wallet.py sync-wallet

Wallet sync successfully completed.
```

#### Display all Transactions

For an existing wallet, this command displays 

```

```

#### Recover Wallet

#### Display Wallet Tree

#### Delete Existing Wallet





