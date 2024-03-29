#!/bin/bash
set +e

port=8080

if [ -z "$VIRTUAL_ENV" ] && [ -d venv ]; then
  echo 'activate venv'
  source ./venv/bin/activate
fi

if [ "$ENVIRONMENT" = 'development' ]; then
  debug='--debug'
fi

flask --app main $debug run -p 8080
