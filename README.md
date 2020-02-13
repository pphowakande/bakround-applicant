# Bakround

This repository contains all components that comprise the web app at `my.bakround.com`.

## Project Structure

`bakround_applicant/` - Core app code. This is the main directory for our Python module.\

`bakround_applicant/scraping/indeed_html_parser` - Poonam Pwokande's Indeed HTML resume parser

`bakround_applicant/services/` - Find service code here. `consumer.py` is the entrypoint for any given service.

`bakround_applicant/static/js` - Where Javascript lives

`bakround_applicant/static/bundles` - Where webpack outputs code - These are build products, not source code.

`bakround_applicant/static/css` - Where CSS lives

`compose/` - Docker and deployment-related stuff. You shouldn't need to change anythere here.

`migration_data/` - Contains data to make migrations work. It's extremely bloated and needs cleaning.

`requirements/` - Pip requirements live here, one set for each environment and a common one.

`scripts/` - Contains scripts for various purposes here. Avoid creating one-off scripts in this directory, use an appropriate subdirectory & aim for longevity.


## Basic Commands

###Setting Up Your Users

* To create a **normal user account**, just go to Sign Up and fill out the form. Once you submit it, you'll see a "Verify Your E-mail Address" page. Go to your console to see a simulated email verification message. Copy the link into your browser. Now the user's email should be verified and ready to go.

* To create an **superuser account**, use this command

    $ make superuser

For convenience, you can keep your normal user logged in on Chrome and your superuser logged in on Firefox (or similar), so that you can see how the site behaves for both kinds of users.


###Tests & Test Coverage

To run the tests (currently broken):

    $ make test

To generate coverage, run (untested):

    $ make coverage

The resulting report will be in `htmlcov/index.html`.

###Email Server

In development, all emails sent from the application will be printed to the STDOUT instead of, well, actually being sent.


###Dependencies

You should have a functional Docker installation locally, as well as Node & NPM. Don't worry about
installing anything else, since all dependencies of the app are downloaded and installed inside Docker.


###Running Locally

Run these commands in the root directory of the project:

    $ docker-compose build
    $ make migrate
    $ docker-compose up

The server runs on `http://localhost:8000`. If you'd like to understand more of what's going on with
configuration, take a look at `docker-compose.yml`.


###Deployment

We don't use `docker-compose` anywhere except locally, and we only deploy the `worker` and `django` docker containers. We also have RabbitMQ and Redis in ECS, but they're handled differently than when deploying than locally.

Deploying is as easy as pushing to `master` and waiting for the BitBucket Pipelines build to complete (about 15-20 minutes, thanks LXML and gevent).

###Deployment/Configuration Details

You can run `./scripts/deploy/deploy.sh` to manually deploy Bakround (it's what the BitBucket pipeline executes). You'll need the following ENV vars to be defined before running the script:

1. AWS_ACCESS_KEY_ID - your AWS access key
2. AWS_ACCOUNT_ID - your AWS account ID
3. AWS_REGION - the AWS region you want to deploy to
4. AWS_SECRET_ACCESS_KEY - your AWS secret key

Don't worry about having files locally that might break the build, we've got an excellent `.dockerignore`.

1. First, it will build the frontend for production *directly on your machine*. This is to avoid doing it once for each docker container.
2. Then, it will build the django and worker images. (well, worker is called `services` everywhere but locally)
3. Once done, it will log into ECR and push the images
4. Then, a new task definition is created using the images and the service is configured to use it

The differences between local and production are:

1. Production uses Gunicorn, local uses Werkzeug
2. Production logs via papertrail
3. Production uses different AWS buckets
4. Production builds the frontend without source maps and with optimizations
5. Production Django runs migrations on start
  5b. Local Django does not.

