#! /usr/bin/env bash

script_path="$( cd "$(dirname "$0")" >/dev/null 2>&1 ; pwd -P )"

pushd "${script_path}"

if [ ! -d "venv" ]; then
    python3 -m venv venv
fi

source ./venv/bin/activate
pip3 install --upgrade pip setuptools wheel
pip3 install .

sudo systemctl stop work_assistant_bot
sudo systemctl start work_assistant_bot
sudo systemctl status work_assistant_bot

popd