#!/bin/bash
set +e

port=8080

if [ -z "$VIRTUAL_ENV" ] && [ -d venv ]; then
  echo 'activate venv'
  source ./venv/bin/activate
fi

python3 main.py runserver --port $port
