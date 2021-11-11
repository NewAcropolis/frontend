#!/bin/bash
if [ ! -d "venv" ]; then
    python3 -m venv ./venv
fi

if [ -z "$VIRTUAL_ENV" ] && [ -d venv ]; then
  echo 'activate venv'
  source ./venv/bin/activate
fi

pip3 install -r requirements.txt
