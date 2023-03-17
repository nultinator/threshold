# Hierarchical Deterministic Wallet

The following document is a guide on setup and usage of this Python implementation of a hierarchical deterministic Bitcoin wallet (HD Wallet). 

Future implementation:

* 

## Setup

### Linux

The following steps are for a new AWS EC2 Linux instance:

1) After logging into your instance, run `sudo yum update -y` and `sudo yum install git -y` to both update the instance and install git. 
2) Run `git clone https://github.com/tycm4109/Threshold-HD-Wallet`. Enter `tycm4109` as the Username and enter the Personal Access Token for Password. 
3) Run `ls -la` and double check the directory `Threshold-HD-Wallet` exists. 
4) Install the latest version of Python 3 by running `sudo yum install python37`. Run `python3 --version` to ensure you have the latest version of Python 3 installed. 
5) Run `python3 get-pip.py --user` to install pip. 
6) Once the latest version of pip has been confirmed installed, navigate into the `Threshold-HD-Wallet` directory and then into the `python_HD_wallet` directory. Install Python virtual environment by running `pip install virtualenv --user`.
7) Activate the virtual environment by running `. .venv/bin/activate`.
8) Install required Python modules from the requirements.txt file by running `pip install -r requirements.txt`.
9) Run `python3 wallet.py` to pull up the Python Wallet commands menu. 

### MacOS

The following steps are for setting up the Python Wallet on your MacOS computer:

1) Ensure you have the latest versions of Python 3 and pip installed. 
2) Run `git clone https://github.com/tycm4109/Threshold-HD-Wallet`. Enter `tycm4109` as the Username and enter the Personal Access Token for Password.
3) Navigate into the `Threshold-HD-Wallet` directory and then into the `python_HD_wallet` directory. Install Python virtual environment by running `pip install virtualenv --user`.
7) Activate the virtual environment by running `. .venv/bin/activate`.
8) Install required Python modules from the requirements.txt file by running `pip install -r requirements.txt`.
9) Run `python3 wallet.py` to pull up the Python Wallet commands menu. 


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

For an existing wallet, this command displays past transaction IDs associated with deposits and withdrawals in the wallet. This command lists transaction IDs along with the BTC amount transacted. The list is not ordered in any way, however, all receiving addresses are shown before the change addresses. 

```
>> python3 wallet.py display-txn

Wallet Transaction History:

Transaction ID: fe21250e20d47af1a60f70f6ff500adc36632fb8447eaa384ebff90260b269e1   BTC Amount: 0.000125
 
Complete
```

#### Recover Wallet

Recover a wallet locally using the 24 word seed and returns BTC balance if wallet recovery was successful. If an optional password was used in creating the wallet, then the password is required as well. 

Keep in mind that the command line may hang for a while after successfully running the command because the recovery process can take several minutes, dependent on how many child addresses had previous transactions. Similar to many other hierarchical deterministic wallets, this wallet has a 20 address gap limit in recovering child addresses. In practice, this may not be necessary since new child addresses are not created unless the previously created child address has been transacted on the blockchain. 

No password example:

```
>> python3 wallet.py recover-wallet --recovery_phrase 'stumble destroy yard mammal draw twin wood lab author fragile notable feed razor citizen exhaust affair motion hub swap mule ridge urban survey cushion'
Wallet recovery in progress, please wait... 

Wallet recovery successfully completed. Total BTC balance:0.0
```

With password example:

```
>> python3 wallet.py recover-wallet --recovery_phrase 'genius motor sauce control know spend neutral mercy surface benefit over steel dolphin fiction law festival motion spray mesh embark pyramid fun catch glide' --password '12345_%NewWallet'
Wallet recovery in progress, please wait... 

Wallet recovery successfully completed. Total BTC balance:0.0
```

#### Display Wallet Tree

For an existing wallet, this command displays the hierarchical tree of the wallet.

```
>>> python3 wallet.py tree 

1CLgNnPqqNtkXe48S8gUpPKqcXaCsawaen
└── 1Cj7uSr5xb5aTF3sbtogUsiK2hBytKwtSX
    └── 1NZH96QW3jzfFvSuVGBg27Wa9VhMxcLCTZ
        └── 162cBExcVwDfh6ts9RmbcPTg4npvcD9Ssr
            ├── 13Mffz9A9UqehWmL7Nxaz4E6KwF59H2ANC
            │   ├── 12bP4dqRgr3r5BKWFQMmFSpYtL14HinPS2
            │   ├── 13AKNRhjtbB8XsVVZggzhLwjtXJaAYvSso
            │   ├── 14EWpuRFQbgMGgHo331n8hxDY2G7FA7J1u
            │   ├── 14yqgrsWH9sB1ZmpnSSb2gLQeHtX6pV6Q5
            │   ├── 196PyWrU46cQDgQjnsQEBLjTD5xYHACFGK
            │   ├── 1A3HZB45icnLZihjE43j2kRGMdthXoBRGm
            │   ├── 1A6UUMvAV7JwVc7N86EPthC82Jo8y6NWqa
            │   ├── 1D3me9yCAcCWdRuEa68LHFmJcUXxNApmVY
            │   ├── 1DgB8BELjpjQwUEUgLMJKJtmpK4AeKENay
            │   ├── 1FSDyfz1wTmPBNSLxeTfdKkCu22L9JTP3s
            │   ├── 1GRVBSz6uPAxbHgay2e1sHnS4nSbPTookp
            │   ├── 1Gar5xLqNzmSqrZArEoSH8shPsyp8CqWPw
            │   ├── 1HADqQVD9mHFCUXNCXJjdw4mKndEysxBqz
            │   ├── 1HDLCuN9C65svg6jjsoD2Jyj5GWzAzYsEr
            │   ├── 1JAf1a8GKtJ6ZMyiZ1jZvE6cRZReKCRv1K
            │   ├── 1LrdejbiQnDuMaApKuV1QhjLfQEnuEzaCG
            │   ├── 1M74M9egNummDMVunMPCCddue5i2BuY5pq
            │   ├── 1Nthm1SRAeAfPt1K18jwDEL8iJ4sC8YYXE
            │   ├── 1RFicJmLK9ihyKhTo3agxYNdyzYuKyJ7z
            │   ├── 1hDRhdukexFMJeGgfKtEZbnceHv9pBcQM
            │   └── 1xQizN1MZAcEbNskW4LNPEpqwzer7876W
            └── 1MziiU9i9AgPJUSQdKFeQmNLDKLqg3HgxN
                ├── 12yt1hrabX49ywwumarsyvYZSPnv5anzjs
                ├── 13iWJ6pwGmiiDJt9DZbVZayDk9pnPFWZML
                ├── 15XhXaTWgRoAQAhQkoHxa4ngH89YywRRSk
                ├── 15x8tojFnFBXrmWU1G2ajsXsXCQmPrDfPG
                ├── 16ERGjPGjDUS3bnDWZnU7s6dkQnNDQAUjy
                ├── 16dEXkSXkvMQ9LwafsTNArfwovk1665FEy
                ├── 17u5vJyTWtrqu1yeerVLusLW8dktmuYn4Z
                ├── 197kmSLYKFcVoNxUx6xdRiEqCWpQpAufxy
                ├── 1A6CWxXj8UcQaaex9a16wKV8jiWaCsJqJr
                ├── 1BBZdgwRhHPmRjSCLF12iwsfBc2dSLDuVQ
                ├── 1BkR2DhZyYZeFTYdsgWxAsrSQATsMGaKTJ
                ├── 1EwDGWxyS3tHrdepXonTKeqV2dvyhfbsvs
                ├── 1FiSdCMWFYFsiXYJKNYawaCtAak4eg3emj
                ├── 1G8cVDxgtbhXFWRUnZFk8pm79Nba4DdC7s
                ├── 1HofKTSz3ZTeZrVffEABrEnq37LD2eYcgk
                ├── 1HwR1dz3A9A7HYnvvH52MwSpJRjnpD4aGt
                ├── 1KVHa3qGrHeAnywN5Yq9HxcEpAXm1r9955
                ├── 1KtKJbYbXyTjUt4MQky1iLohTa131eZ6yY
                ├── 1KyBNe9imN4UrdoF8ZdFzByXD3Nfotqkww
                ├── 1M7Y5VtnA7fsGMyqTXqGK2UsveQBo75G16
                └── 1P9WGGVrKVHF1BybGizy5GhepRyUkpsPmF
```


#### Delete Existing Wallet

To create a new wallet or recover a wallet, users need to ensure the existing local wallet is deleted. To delete a local wallet, simply delete the `HDWalletTree_dill.pkl` and `masterkey.pkl` files found in the working directory. 




