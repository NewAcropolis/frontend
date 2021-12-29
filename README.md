# New Acropolis UK frontend  ![Build Status](https://github.com/NewAcropolis/frontend/actions/workflows/ci.yml/badge.svg?branch=master)

## Pre-requisites

Before starting, ensure you are using python 3.7 and that you have (gcloud sdk version 357.0.0)[https://cloud.google.com/sdk/docs/] and follow the instructions to install it.

If you have another version of gcloud installed, you can set it to 357.0.0 -

`gcloud components update --version 357.0.0`

Also install the gcloud datastore emulator - 

`gcloud components install cloud-datastore-emulator`

You should have these components installed, `gcloud version` - 

```
Google Cloud SDK 357.0.0
beta 2021.10.04
bq 2.0.71
cloud-datastore-emulator 2.1.0
core 2021.09.10
gsutil 4.67
```

### Quickstart

1. Clone this repo and then run the bootstrap script to set things up:
  - only needs to be run once for setup.

  `./scripts/bootstrap.sh`

2. Run the datastore in another terminal window:
  - this needs to be kept running in another terminal for the duration of the local app life.

  `make datastore`

3. Copy the environment_sample.sh to environment.sh, populate the env vars and then source it:
  - `environment.sh` should also be sourced whenever you want to change an environment variable before running the app.

  `. ./environment.sh`

4. Finally get the app running:

  `make run`

5. Visit the website in your browser - http://localhost:8080/
  - first run might be a bit slow as the cache builds up from API requests
  - subsequent runs should be much faster

## Running tests

In order to test changes locally run `make test`, this will help catch test errors before they appear in github actions.
- test coverage is quite low at the moment, in the future this will be improved so that cover at least 80% of the codebase.

## Using Makefile

Run `Make` to list other available commands

## Updating deployed secrets

1. Update the following JSON block with env var settings:

```
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
    "ENABLE_STATS": "False",
    "SHOW_RESOURCE_MAINTENANCE": "False",
    "IS_APP_ENGINE": "True"
  }
}
```

2. Save the JSON block as `secrets.json`and then convert it to base 64:

  `base64 -i secrets.json > secrets.b64`

3. In Github settings under secret, update the appropriate environment secret with the base 64 string.

4. To deploy new settings re-run the last merge (for preview deployment) or tag (for live deployments) in Github actions.
