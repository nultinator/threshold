# Hierarchical Deterministic Wallet

The following document is a guide on setup and usage of this Python implementation of a hierarchical deterministic Bitcoin wallet (HD Wallet). 

Planned updates:

* Build and broadcast a successful BTC transaction using multiple inputs and two outputs (target address & change address). This should be achieved for legacy, p2sh, and bech32 addresses. 
* Demonstrate the ability to successfully recover a wallet that was created by this HD Wallet program, on either an Electrum or hardware wallet (e.g. Trezor T or Ledger Nano). This should be achieved for legacy, p2sh, and bech32 addresses. 


## Setup

### Linux

The following setup steps are for a new AWS EC2 Linux instance:

1) After logging into your instance, run `sudo yum update -y` and `sudo yum install git -y` to update the instance and install git. 
2) Run `git clone https://github.com/tycm4109/Threshold-HD-Wallet`. Enter `tycm4109` as the Username and enter the Personal Access Token when prompted for a password. 
3) Run `ls -la` and double check the directory `Threshold-HD-Wallet` exists. 
4) Install the latest version of Python 3 by running `sudo yum install python37`. Run `python3 --version` to ensure you have the latest version of Python 3 installed. 
5) Run `python3 get-pip.py --user` to install pip. 
6) Once the latest version of pip has been installed, navigate to the `Threshold-HD-Wallet` directory and then into the `python_HD_wallet` sub-directory. Install Python virtual environment by running `pip install virtualenv --user`.
7) Activate the virtual environment by running `. .venv/bin/activate`.
8) Install required Python modules from the requirements.txt file by running `pip install -r requirements.txt`.
9) Run `python3 wallet.py` to pull up the Python Wallet commands menu. 

### MacOS

The following steps are for setting up the Python Wallet on your MacOS computer:

1) Ensure you have the latest versions of Python 3 and pip installed. 
2) Run `git clone https://github.com/tycm4109/Threshold-HD-Wallet`. Enter `tycm4109` as the Username and enter the Personal Access Token when prompted for a password. 
3) Navigate to the `Threshold-HD-Wallet` directory and then into the `python_HD_wallet` sub-directory. Install Python virtual environment by running `pip install virtualenv --user`.
7) Activate the virtual environment by running `. .venv/bin/activate`.
8) Install required Python modules from the requirements.txt file by running `pip install -r requirements.txt`.
9) Run `python3 wallet.py` to pull up the Python Wallet commands menu. 


## Usage

### Contents

* [Create a New Wallet](#create-a-new-wallet)
* [Check Wallet Balance](#check-wallet-balance)
* [Deposit BTC](#deposit-btc)
* [Withdraw BTC](#withdraw-btc)
* [Sync Wallet Balance](#sync-wallet-balance)
* [Display Transactions](#display-transactions)
* [Recover Wallet](#recover-wallet)
* [Display Wallet Tree Hierarchy](#display-wallet-tree)
* [Delete an Existing Wallet](#delete-existing-wallet)


#### Create a New Wallet

The `create-wallet` command creates a local wallet and outputs the 24-word mnemonic required for wallet recovery. This command also allows the user to optionally add in a password for extra security. The password can be any combination of numbers, letters, and special characters, as long as it does not contain the exact same characters as linux/shell commands (i.e. && or ||). If a local wallet already exists in the user's directory, this command will not create a new wallet unless the user deletes the wallet directory containing the *wallet.pkl* and *masterkey.pkl* files. 

The following animation shows the process of creating a new p2sh address type wallet with a user designated password of *12345_%NewWallet*. The *deposit* command then displays a new receiving child address and the *tree* command displays the entire tree hierarchy of the wallet:

![](https://github.com/tycm4109/Threshold-HD-Wallet/blob/main/Readme%20GIFs/create_wallet.gif)

#### Check Wallet Balance

For an existing wallet, the `balance` command outputs the wallet balance in BTC:

```
>> python3 wallet.py balance

BTC Balance: 0.0
```

#### Deposit BTC

For an existing wallet, you can generate a child BTC address for deposits. New child BTC addresses are not generated unless the previous index child BTC address already had UTXOs on the blockchain:

```
>> python3 wallet.py deposit

Send only BTC to this address: 18LMcFA4C5ybAPchb4po1W8cQPHeue8SwW
```

#### Withdraw BTC

In development. 

#### Sync Wallet Balance

For an existing wallet, the wallet needs to be sync'ed with the blockchain in order to display the correct wallet balance. This would be similar to a "Refresh" feature on a front-end client:

```
>>> python3 wallet.py sync-wallet

Wallet sync successfully completed.
```

#### Display Transactions

For an existing wallet, this command displays past transaction IDs associated with deposits and withdrawals in the wallet, as well as the BTC amount transacted. The list is not ordered in any way, however, all receiving addresses are shown before the change addresses. 

```
>> python3 wallet.py display-txn

Wallet Transaction History:

Transaction ID: fe21250e20d47af1a60f70f6ff500adc36632fb8447eaa384ebff90260b269e1   BTC Amount: 0.000125
 
Complete
```

#### Recover Wallet

This function recovers a wallet locally using the 24-word mnemonic, and returns the BTC balance if wallet recovery was successful. If an optional password was used in creating the wallet, then the password is required as well. 

Keep in mind the command line may hang for a while after successfully running the command because the recovery process can take several minutes, depending on how many child addresses had UTXOs. Similar to many other hierarchical deterministic wallets, this wallet has a 20 address gap limit in recovering child addresses. In practice, this may not be necessary since new child addresses are not created unless the previously created child address has UTXOs. 

![](https://github.com/tycm4109/Threshold-HD-Wallet/blob/main/Readme%20GIFs/wallet_recovery.gif)

#### Display Wallet Tree

For an existing wallet, this command displays the hierarchical tree of the wallet.


#### Delete Existing Wallet

To create a new wallet or recover an existing wallet from a 24-word mnemonic, users need to ensure no local wallet file already exists. To delete an existing local wallet, simply delete the *wallet* directory containing the *wallet.pkl* and *masterkey.pkl* files.  




