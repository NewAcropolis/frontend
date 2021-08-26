# New Acropolis UK frontend  [![Build Status](https://travis-ci.org/NewAcropolis/frontend.svg?branch=master)](https://travis-ci.org/NewAcropolis/frontend)

## Pre-requisites

Before starting, ensure you are using python 2.7 and that you have (gcloud sdk)[https://cloud.google.com/sdk/docs/] and follow the instructions to install it.

Then install google app engine

`gcloud components install app-engine-python`

To get the frontend running you may need to update the `PYTHONPATH` to pick up the `google_appengine` SDK:

```
export PYTHONPATH="$PYTHONPATH:<location of google-cloud-sdk>/platform/google_appengine:<location of google-cloud-sdk>/platform/google_appengine/lib/:<location of google-cloud-sdk>/platform/google_appengine/lib/yaml/"
```

## Create virtualenv

A Virtual Environment is an isolated working copy of Python which
allows you to work on a specific project without worry of affecting other projects

Follow this guide to set up your virtualenv for this project;
https://virtualenvwrapper.readthedocs.io/en/latest/

## Using Makefile

Before executing `make run`, execute `make dependencies` to build the `lib` directory.

Run `Make` to list available commands

## Adding secrets

Make a copy of `app.yaml` to `app-dev.yaml` and add secrets as environment vars to `app-dev.yaml`

```
env_variables:
  SECRET_KEY: <secret key>
  API_BASE_URL: <new acropolis api url>
  FRONTEND_BASE_URL: <new acropolis frontend url>
  ADMIN_CLIENT_ID: <admin client id - should match api>
  ADMIN_CLIENT_SECRET: <admin secret - should match api>
  AUTH_USERNAME: <basic auth username>
  AUTH_PASSWORD: <basic auth password>
  IMAGES_URL: <image url for events>
  GOOGLE_OAUTH2_CLIENT_ID: <google oauth2 client id>
  GOOGLE_OAUTH2_CLIENT_SECRET: <google oauth2 client secret>
  GOOGLE_OAUTH2_REDIRECT_URI: <google auth redirect>

  PAYPAL_ACCOUNT: <paypal account>
  PAYPAL_ACCOUNT_ID: <paypal account id>
  PAYPAL_ENCRYPTED_1: <paypal view cart encryption up to 1100 chars long>
  PAYPAL_ENCRYPTED_2: <paypal view cart encryption remaining part>
  PAYPAL_DELIVERY = <paypal delivery id>
  SESSION_EXPIRY = <session expiry length in minutes>
  RECAPTCHA_PUBLIC_KEY = <recaptcha public key>
  RECAPTCHA_PRIVATE_KEY = <recaptcha private key>
  GA_ID = <google analytics id>
  GA_TM_ID = <google analytics tag manager id>
  ENABLE_STATS = <set to `true` to enable stats push >

```

To update a secret you will need to log into the datastore and edit the value there or remove the value and deploy the changes.

Then run `make deploy`, this will add the env vars to the datastore.

Pushing changes to the github repo will trigger an automatic deployment onto app engine.

## Viewing the frontend

Run `make dev-server` and visit `http://localhost:8080/`

## Switching between API environments

Remember to remove all sessions, otherwise new keys will not be reloaded
