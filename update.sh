#!/usr/bin/env bash
set -e

echo "updating..."

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"

cd "$DIR" || exit 1

BRANCH=master
if [[ -f /boot/ucloud-thing-branch.txt ]]; then
  BRANCH=$(cat /boot/ucloud-thing-branch.txt)
fi

git reset --hard
git checkout -f "$BRANCH"
git pull

apt install libbluetooth-dev libglib2.0-dev libboost-python-dev libboost-thread-dev -y

source venv/bin/activate
pip install -r requirements.txt

hciconfig hci0 piscan

echo "updated"