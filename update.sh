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

if [[ -f requirements.installed.txt && $(cat requirements.installed.txt) = $(cat requirements.txt) ]]; then
  echo "nothing to update"
else
  source venv/bin/activate
  pip install -r requirements.txt && cp requirements.txt requirements.installed.txt
fi

hciconfig hci0 piscan

echo "updated"