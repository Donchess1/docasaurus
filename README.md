# MyBalance API

[![Black Code Style](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/ambv/black)

## Technologies

- [Python 3.10](https://python.org): Base programming language for development
- [PostgreSQL](https://www.postgresql.org/): Application relational databases for development, staging and production environments
- [Django Framework](https://www.djangoproject.com/): Development framework used for the application
- [Django Rest Framework](https://www.django-rest-framework.org/) : Provides API development tools for easy API development
- [Celery](https://github.com/celery/celery): A simple, flexible, and reliable distributed system to process vast amounts of tasks
- [Redis](https://github.com/redis/redis-py): A NoSQL Database that serves as Cache, Celery Broker and Result Backend
- [SendGrid](https://sendgrid.com/): An Email Service Provider for sending emails
- [Docker Engine and Docker Compose](https://www.docker.com/) : Containerization of the application and services orchestration

## How To Start App

- Clone the Repository
- create a .env file with the variables in the .env.example file
  - `cp env.example .env`
  - You will also need to create an account with [SendGrid](https://sendgrid.com/) and get an API Key. You will need to add this to the .env file

- Run `make build`

  - Running the above command for the first time will download all docker-images and third party packages needed for the app.
  - **NB: This will take several minutes for the first build**

- Run `make up`

  - Running the above command will Start up the following Servers:
    - Postgres Server --> http://localhost:5435
    - Django Development Server --> http://localhost:8000
    - Redis Server --> http://localhost:6379

- Run `make down` to stop the servers

- Run `make test` to run tests

- Other commands can be found in the Makefile

## Exploring The App

Make sure that all the above servers are running before you start exploring the project.
