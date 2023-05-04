# Hierarchical Deterministic Wallet

The following document is a guide on setup and usage of this Python implementation of a hierarchical deterministic Bitcoin wallet (HD Wallet). 



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

![image](https://user-images.githubusercontent.com/72562693/236236145-f2587811-b479-4b4c-996a-1abd5defd2f6.png)


### Contents

* [Create a New Wallet](#create-a-new-wallet)
* [Check Balances](#check-balances)
* [Remove a Wallet](#remove-a-wallet)
* [Block Explorer](#block-explorer)
* [Generate a Receiving Address](#generate-a-receiving-address)
* [Send a Transaction](#send-a-transaction)
* [Export Wallet](#export-wallet)



### Create a New Wallet

<p>On the first run, you will be automatically prompted to set up a wallet</p>

![image](https://user-images.githubusercontent.com/72562693/236253273-b2bd44d5-b0b3-4fd3-a89f-acfb3a38728d.png)



<p>Give your wallet a name and enter a ticker name</p>.  

![image](https://user-images.githubusercontent.com/72562693/236238666-c17be462-2170-41c4-b4cb-9ae375e0d57f.png)


<p>You may input a seed phrase to restore an existing wallet or create a new wallet from scratch.  Your first wallet will be created with one address and generate new addresses as you use them. After creating your initial wallet, you may select <b>1</b> to create or restore additional wallets.  When creating additional wallets, your first 30 change and receiving addresses will be generated and scanned for existing balances.  You can see an example below.</p>

### Check Balances

![image](https://user-images.githubusercontent.com/72562693/236239837-839369d1-f395-4f64-8703-e8c3301a5d17.png)

### Remove a Wallet

<p> You will be prompted to enter the name of the wallet and upon entering it, the wallet will be removed.  As you can see below,
entering the name <i>"exodus"</i> removes the wallet with the same name.</p>

![image](https://user-images.githubusercontent.com/72562693/236241553-65719f99-2fc1-4d5e-af60-1f73585fa751.png)

### Block Explorer

<p>With this option, you may lookup the unconfirmed balance of an address, details about a specific transaction,
or lookup the coins held by an individual address.</p>

![image](https://user-images.githubusercontent.com/72562693/236248377-36f50ec1-f807-40e8-a217-a442752ecbed.png)



### Generate a Receiving Address
<p>As is recommended when receiving Bitcoin, you should always use a fresh wallet. <b>5</b> will generate a new receiving wallet for you.
Simply enter the name of the parent wallet you wish to use.  Next a new wallet will be generated and you will be given the option to
display the receiving address as a QR code.
</p>

![image](https://user-images.githubusercontent.com/72562693/236243806-64adcafb-cf25-4852-bbe1-b0ce63b3e522.png)


### Send a Transaction

<p>When sending a transaction, you will give the option to use either <strong>Simple Send</strong> or <strong>Create a Raw Transaction</strong>.
When using <strong>Simple Send</strong>, the coins you are spending will be automatically selected for you, when creating a raw transaction,
you select the individual coins going into the transaction.  Next you will be promtpted to enter an address to send to and an amount to send.
A fresh change wallet will be automatically generated for you. The wallet calculates a recommended fee based on current network conditions.
You may elect to use the recommended fee or to enter a custom amount.  After creating the transaction, the wallet will display the TXID of your new transaction and submit it to the network.  If the transaction was successful, the server will respond with an identical TXID as you can see below.</p>

![image](https://user-images.githubusercontent.com/72562693/236247754-f08ddb70-b16c-4f3d-8160-93784210beb2.png)

### Export Wallet

<p>When exporting a wallet, you will display both your seed phrase and "wif" private key as both text and a QR code as you can see below.</p>

<h4>Seed Phrase</h4>

![image](https://user-images.githubusercontent.com/72562693/236250101-4b21383e-8985-4740-926f-303156e71bfe.png)

<h4>Private Key</h4>

<p>
<strong>DISCLAIMER:</strong> it is highly recommended to back up your seed phrase.  You can derive new wallets from seed phrase.
<strong>YOU CAN NOT DERIVE NEW WALLETS FROM A WIF PRIVATE KEY!!!</strong>  In the future, should users express interest in it,
options could be added to export your <i>Root XPrivate Key</i> but at the moment, this is not an industry standard so it will not be included 
in the first release.
</p>

![image](https://user-images.githubusercontent.com/72562693/236250339-a2762029-824f-4b1e-9207-29bb68aa622d.png)


