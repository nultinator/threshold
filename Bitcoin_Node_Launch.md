Steps for launching a Bitcoin Full Node on AWS EC2. Adapted from https://wolfmcnally.com/115/developer-notes-setting-up-a-bitcoin-node-on-aws/, 
and updated to reflect actual AWS Console user journey. 

### Initial Steps

* From the AWS console, navigate to EC2.
* Click the Launch Instance button.

## Step 1: Choose an Amazon Machine Image (AMI)

* Click on the AWS Marketplace tab.
* Search for `Debian Stretch` in the search box.
* Find the AMI for *Debian GNU/Linux 9 (Stretch)* and click **Select**. 
* A box will appear with details and a list of example prices. Click **Continue**.

## Step 2: Names and Tags

* In the *Name* field, enter something like `Bitcoin Node`. 

## Step 3: Choose an Instance Type

You will need an instance with 2-3 gigabytes of memory. 

* Choose the `t3.medium` instance, which has 4GB of memory and can be connected to EBS (Elastic Block Storage) of any size. 

## Step 4: Create Key-Pair Login

* Click on **Create New Key Pair**. Enter the key pair name, choose the key pair type, the private key file format, and click **Create key pair**.
* The key pair file downloads on your computer.

## Step 5: Network Settings & Security Group

* Select Create a New Security Group.
* Enter a Name and Description for the Security Group. For example, *Bitcoin Node* and *Ports and services necessary for running a Bitcoin Node*. 
* A rule allowing SSH access to your instance from any other IP address is already in place. The bitcoin client needs to talk through port 8333 for Mainnet and 18333 for Testnet. We will create rules for allowin them both, as well as a rule that opens the port used by the Lightning Protocol. 
* Click the **Add Rule** button. 
* Select **Custom UDP** for the *Type*. 
* Enter `8333` for *Port Range*.
* Select **Anywhere** for *Source*. 
* Enter `Mainnet` in the *Description* field. 
* Perform the last five steps again, but use `18333` for the *Port Range* and `Testnet` for the *Description*. 
* Do it one more time, but use `9735` for the *Port Range* and `Lightning` for the *Description*. 

## Step 6: Configure Storage

* Click **Add New Volume**.
* Choose `EBS`, `/dev/sdb` for the *Device* column, 300 GB for the *Size*, and **General Purpose SSD** for the *Volume Type*. 
* Launch the Instance.

## Launching

The next page keeps you informed on the launch status. Assuming all goes well, you will receive the message Your instances are now launching and instance ID like this: `i-0d881a693cb29c072`.

* Click **View Instances**.

You should see your new `Bitcoin` instance in the list. Eventually the *Instance State* will change to `Running`. For awhile the *Status Checks* column will also say `Initializing`. 
Wait for this to change (reload the page if necessary) to `2/2 checks passed`.

## Log In to Your Instance for the First Time

From the View Instances page, click on your new instance in the table of instances. At the top you will find a **Public IPv4 address** field with an IP address like: xx.xx.xx.xx. 
This is an ephemeral IP address that will change if you stop and restart your instance. You can set up an EC2 Elastic IP address to keep this from happening (not covered here.)

Prior to SSH'ing into your instance, you will need to modify the pem key file to have certain secure properties. This ensures no other users can easily access the instance. To do this,
simply run the following command for your file:

```
$ sudo chmod 600 /path/to/my/key.pem
```

If you try to SSH into the instance without modifying the key, you will incur an **Unprotected Private Key File Warning**. To copy the file path in Mac, open the file location in a Finder Window. 
Hold down the **Control** button, and left click on the pem key file. While the **Control** button is held down, simultaneously press the **Option** button to show
the menu option *Copy "file" as Pathname*. Select this option, then you can paste into the terminal. 

Note: I had to move my pem file onto my Desktop before the Mac allowed me to run `chmod 600` on it. 

In the terminal:

```
$ ssh -i /path/to/your/keypair.pem admin@xx.xx.xx.xx
```

Successful login should show something like:

```
Linux ip-172-31-56-252 4.9.0-14-amd64 #1 SMP Debian 4.9.240-2 (2020-10-30) x86_64

The programs included with the Debian GNU/Linux system are free software;
the exact distribution terms for each program are described in the
individual files in /usr/share/doc/*/copyright.

Debian GNU/Linux comes with ABSOLUTELY NO WARRANTY, to the extent
permitted by applicable law.
Last login: Tue Feb  2 15:03:11 2021 from 195.181.167.196
admin@ip-172-31-56-252:~$ 
```

## Installing Updates

The first thing to do is update everything that needs updating since this distro was produced:





