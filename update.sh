#!/usr/bin/env bash

echo "updating..."

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"

cd "$DIR" || exit 1

git reset --hard
git pull

source venv/bin/activate
pip install -r requirements.txt

echo "updated"