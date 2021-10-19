#!/bin/bash
set +e


port=8080

python3 main.py runserver --port $port
