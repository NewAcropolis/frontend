# New Acropolis UK frontend  [![Build Status](https://travis-ci.org/NewAcropolis/frontend.svg?branch=master)](https://travis-ci.org/NewAcropolis/frontend)

## Pre-requisites

Before starting, ensure you are using python 2.7 and that you have (gcloud sdk)[https://cloud.google.com/sdk/docs/] and follow the instructions to install it.

Then install google app engine 

`gcloud components install app-engine-python`

To get the frontend running you may need to update the `PYTHONPATH` to pick up the `google_appengine` SDK:

```
export PYTHONPATH="$PYTHONPATH:<location of google-cloud-sdk>/platform/google_appengine:<location of google-cloud-sdk>/platform/google_appengine/lib/:<location of google-cloud-sdk>/platform/google_appengine/lib/yaml/"
```

## Using Makefile

Before executing `make run`, execute `make dependencies` to build the `lib` directory.

Run `Make` to list available commands

## Adding secrets

Make a copy of `app.yaml` to `app-dev.yaml` and add secrets as environment vars to `app-dev.yaml`

```
env_variables:
  SECRET_KEY: <secret key>
  API_BASE_URL: <new acropolis api url>
  FRONTEND_BASE_URL: <frontend base url>
  ADMIN_CLIENT_ID: <admin client id - should match api>
  ADMIN_CLIENT_SECRET: <admin secret - should match api>
  AUTH_USERNAME: <basic auth username>
  AUTH_PASSWORD: <basic auth password>
```

To update a secret you will need to log into the datastore and edit the value there or remove the value and deploy the changes.

Then run `make deploy`, this will add the env vars to the datastore.

Pushing changes to the github repo will trigger an automatic deployment onto app engine.
