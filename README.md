# Hierarchical Deterministic Wallet

The following document is a guide on setup and usage of this Python implementation of a hierarchical deterministic Bitcoin wallet (HD Wallet). 

Planned updates:

* Build and broadcast a successful BTC transaction using multiple inputs and two outputs (target address & change address). This should be achieved for legacy, p2sh, and bech32 addresses. 
* Demonstrate the ability to successfully recover a wallet that was created by this HD Wallet program, on either an Electrum or hardware wallet (e.g. Trezor T or Ledger Nano). This should be achieved for legacy, p2sh, and bech32 addresses. 


## Setup And Installation

### Linux and Mac

<h4>Clone the Repo</h4>

```
git clone -b dev https://github.com/nultinator/threshold
```

<h4>Installation</h4>
<p>First we hop into the "threshold" directory</p>

```
cd threshold
```

<p>Next we allow the install script to run as a program</p>

```
chmod +x install.sh
```

<p>Run the installation</p>

```
./install.sh
```

<p>Run the main program</p>

```
python main.py
```


## Usage

### Contents

* [Create a New Wallet](#create-a-new-wallet)



### Create a New Wallet

<p>On the first run, you will be automatically prompted to set up a wallet</p>


![image](https://user-images.githubusercontent.com/72562693/231815704-d9770263-543c-4a1c-951a-7bb3903af6c9.png)

<p>Give your wallet a name and choose whether or not to run the wallet interactively. If you select not to run, the wallet will fetch your balances and then exit the program, otherwise you will see the options listed below.  Simply enter the number shown next to the action you would like to perform.  For example, if you would like to fetch balances, enter "2", and the your wallet will check the balances of all your addresses.</p>

![image](https://user-images.githubusercontent.com/72562693/234404710-d482e83c-a0ca-40eb-ad24-d2d88db34a85.png)
