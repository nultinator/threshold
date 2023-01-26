#!/bin/bash

# Switch to root account
sudo -s <<EOF
sudo apt-get update && apt-get upgrade
sudo echo "unattended-upgrades unattended-upgrades/enable_auto_updates boolean true" | debconf-set-selections
sudo apt-get -y install unattended-upgrades
sudo apt-get install haveged -y
EOF

touch .bash_profile

echo "alias btcdir="cd ~/.bitcoin/" #linux default bitcoind path" > .bash_profile
echo "alias bc="bitcoin-cli"" >> .bash_profile
echo "alias bd="bitcoind"" >> .bash_profile
echo "alias btcinfo='bitcoin-cli getwalletinfo | egrep "\"balance\""; bitcoin-cli getinfo | egrep "\"version\"|connections"; bitcoin-cli getmininginfo | egrep "\"blocks\"|errors"'" >> .bash_profile
echo "alias btcblock="echo \\\`bitcoin-cli getblockcount 2>&1\\\`/\\\`wget -O - http://blockexplorer.com/testnet/q/getblockcount 2> /dev/null | cut -d : -f2 | rev | cut -c 2- | rev\\\`"" > .bash_profile

export BITCOIN=bitcoin-core-0.21.1
export BITCOINPLAIN=`echo $BITCOIN | sed 's/bitcoin-core/bitcoin/'`

wget https://bitcoin.org/bin/$BITCOIN/$BITCOINPLAIN-x86_64-linux-gnu.tar.gz
wget https://bitcoin.org/bin/$BITCOIN/SHA256SUMS.asc
wget https://bitcoin.org/laanwj-releases.asc

/bin/tar xzf $BITCOINPLAIN-x86_64-linux-gnu.tar.gz
sudo /usr/bin/install -m 0755 -o root -g root -t /usr/local/bin $BITCOINPLAIN/bin/*
/bin/rm -rf $BITCOINPLAIN/

mkdir .bitcoin
touch .bitcoin/bitcoin.conf




/bin/chmod 600 .bitcoin/bitcoin.conf
bitcoind -daemon