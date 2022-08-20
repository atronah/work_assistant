#! /usr/bin/env bash

source ./venv/bin/activate
pip3 install --upgrade pip setuptools
pip3 install .

sudo systemctl stop work_assistant_bot
sudo systemctl stop work_assistant_bot