# New Acropolis UK frontend  [![Build Status](https://travis-ci.org/NewAcropolis/frontend.svg?branch=master)](https://travis-ci.org/NewAcropolis/frontend)

## Pre-requisites

Before starting, ensure you are using python 3.7 and that you have (gcloud sdk version 357.0.0)[https://cloud.google.com/sdk/docs/] and follow the instructions to install it.

Then install google app engine

`gcloud components install app-engine-python`

To get the frontend running you may need to update the `PYTHONPATH` to pick up the `google_appengine` SDK:

```
export PYTHONPATH="$PYTHONPATH:<location of google-cloud-sdk>/platform/google_appengine:<location of google-cloud-sdk>/platform/google_appengine/lib/:<location of google-cloud-sdk>/platform/google_appengine/lib/yaml/"
```

### Quickstart

1. Clone this repo and then run the bootstrap script to set things up:
  - only needs to be run once for setup.

  `./scripts/bootstrap.sh`

2. Run the datastore in another terminal window:
  - this needs to be kept running in another terminal for the duration of the local app life.

  `./scripts/run_datastore.sh`

3. Copy the environment_sample.sh to environment.sh, populate the env vars and then source it:

```
  . ./venv/bin/activate  # run this command if not in virtual environment
  . ./environment.sh     # run this to update the config before running the app
```

4. Finally get the app running:

  `make run`

5. Visit the website - http://localhost:8080/
  - first run might be a bit slow as the cache builds up from API requests
  - subsequent runs should be much faster

## Using Makefile

Run `Make` to list available commands

## Updating deployed secrets

1. Update the following JSON block with env var settings:

{
  "env_variables": {
    "ENVIRONMENT": <environment, defaults to development>,
    "API_BASE_URL": <API URL>,
    "FRONTEND_BASE_URL": <Frontend URL>,
    "ADMIN_CLIENT_ID": <API client ID>,
    "ADMIN_CLIENT_SECRET": <API client secret>,
    "SESSION_EXPIRY": 30,
    "SECRET_KEY": "secret-key",
    "AUTH_USERNAME": <Basic auth username>,
    "AUTH_PASSWORD": <Basic auth password>,
    "IMAGES_URL": <Image path>,
    "RECAPTCHA_PUBLIC_KEY": <Recaptcha public key>,
    "RECAPTCHA_PRIVATE_KEY": <Recaptcha private key>,
    "GA_ID": <Google analytics ID>,
    "GA_TM_ID": <Google Tag Manager ID>,
    "PAYPAL_DELIVERY": <Paypal hosted button ID>,
    "PAYPAL_ENCRYPTED_1": <Part 1 of Paypal encrypted code for shopping cart>,
    "PAYPAL_ENCRYPTED_2": <Part 2 of Paypal encrypted code for shopping cart>,
    "GOOGLE_OAUTH2_CLIENT_ID": <Oauth2 ID>,
    "GOOGLE_OAUTH2_CLIENT_SECRET": <Oauth2 secret>,
    "GOOGLE_OAUTH2_REDIRECT_URI": <Oauth2 redirect after authentication>,
    "PAYPAL_ACCOUNT_ID": <Paypal account ID>,
    "ENABLE_STATS": false,
    "SHOW_RESOURCE_MAINTENANCE": false,
    "IS_APP_ENGINE": true
  }
}

2. Save the JSON block and then convert it to base 64:

  `base64 -i secrets.json > secrets.b64`

3. In Github settings under secret, update the appropriate environment secret with the base 64 string.

4. To deploy new settings re-run the last merge or tag in Github.
