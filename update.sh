#!/usr/bin/env bash

echo "updating..."

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"

cd "$DIR" || exit 1

git reset --hard
git pull

apt install libbluetooth-dev libglib2.0-dev libboost-python-dev libboost-thread-dev -y

source venv/bin/activate
pip install -r requirements.txt

hciconfig hci0 piscan

echo "updated"