#!/usr/bin/env bash

echo "updating..."

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"

cd "$DIR" || exit 1

BRANCH=stable
if [[ -f /boot/ucloud-thing-branch.txt ]]; then
  BRANCH=$(cat /boot/ucloud-thing-branch.txt)
fi

git reset --hard
git pull origin "$BRANCH"
git checkout -f "$BRANCH"

source venv/bin/activate
pip install -r requirements.txt

hciconfig hci0 piscan

echo "updated"