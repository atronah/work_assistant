#! /usr/bin/env bash

script_path="$( cd "$(dirname "$0")" >/dev/null 2>&1 ; pwd -P )"

pushd "${script_path}"

if [ ! -d "venv" ]; then
    python3 -m venv venv
fi

source ./venv/bin/activate
pip3 install --upgrade pip setuptools
pip3 install .

systemctl stop work_assistant_bot
systemctl start work_assistant_bot

popd