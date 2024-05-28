# Chat App

This is documentation on the assessment from Tempo AI ventures.

Live url: [https://chat-app-t5i4.onrender.com](https://chat-app-t5i4.onrender.com)

## Running

To set up this service for local or remote deployment on a computer environment, you need to follow the steps below.

#### Clone the repository

```shell
git clone https://github.com/Fuad28/chat-app.git

```

#### Move into the directory and create a .env file from the .env.example file in the root directory.

```shell
cd chat-app
```

#### Start the docker-compose file

```shell
docker-compose -f docker-compose.dev.yml up -d --build
```

> Note that the assumption is that you already have docker installed and running on your computer

Now that you've built the containers, you're ready to start making requests on [http//:127.0.0.1:8000/api/v1/](http:127.0.0.1:8000/api/v1) and [ws//:127.0.0.1:8000/ws/conversations/](ws//:127.0.0.1:8000/ws/conversations/)

## Running tests

In the root directory, run

```shell
docker-compose -f docker-compose.dev.yml exec web ./run_tests.sh
```

In addition, a GitHub workflow has been set up with the name `run_tests.yml` to automatically run tests on all following changes created either by a push or pull request to the master branch.

## API documentation can be accessed via

HTTP endpoints: [https://documenter.getpostman.com/view/20100124/2sA3Qs9roh](https://documenter.getpostman.com/view/20100124/2sA3Qs9roh)

WS endpoint: [ws//:127.0.0.1:8000/ws/conversations/?token=...](ws//:127.0.0.1:8000/ws/conversations/?token=...)

> An Image will be attached since we couldn't publish WebSockets on Postman
> <img width="1135" alt="Screenshot 2024-05-27 at 7 53 35 PM" src="https://github.com/Fuad28/chat-app/assets/63596779/54404eb7-3084-409c-bbba-e25951a1e428">

## Deployment

### Render Cloud

To deploy this service on Render, you need to create a Render web service and select a Python environment as your deployment environment as well as set the required env variables so they can become available to the Docker context. Check the `.env.example` file for the list of required env variables. Connect the right GitHub repository to the Render service set the branch to `master` and the path to `./` and then proceed to deploy.

In addition, a CI/CD pipeline has been set up to redeploy changes in the master branch. This is subject to passing the test mentioned above.

## Implementation details and design decisions.

#### Data storage.

Data first persists in the Postgres database and is then saved in the Redis. This is due to the in-memory nature of Redis and we understand how important users chats are. We certainly don't want users to have missing messages.

At every point in time, we store at most 500 messages per conversation for instance, this gives users enough to read before it's necessary to send a request.

#### Database schema

A simple schema is adopted to capture all necessary data. An API was subsequently built around it to allow for necessary data to be conveniently shown while keeping network calls minimum.

PostgreSQL was selected due to its scalability, performance, and exciting features.

<img width="1082" alt="Screenshot 2024-05-27 at 11 55 06 AM" src="https://github.com/Fuad28/chat-app/assets/63596779/e2989db0-dd75-4819-95eb-c1187f21a93f">

#### Features

-   User management and authentication is handled by Djoser
-   WebSocket implementation by django-channels.
-   Conversation activities such as joins and exits are broadcast.
-   Tests are by pytest
-   Local development was handled by Docker
-   Logging by Django built-in logger leveraging file and console.
-   Monitoring by sentry. We can further configure this to send logs to a Slack channel.
-   Throttling is implemented project-wise and also specifically on messages. The throttle rate for users is 1000 messages per day and that of messages is set to 60 messages per minute. These values are abstract and subsequent observation and data analytics can help establish a sensible value.
-   The API is deployed on render.
-   Mails are sent using Mailjet API in production. We however use a development smtp server called smtp4dev for development. The emails can be accessed via [http://127.0.0.1:8001/](http://127.0.0.1:8001/) in development.
-   Soft delete is implemented for messages. Further discussions can be had on how to handle them.

#### Recommendation for improvement

-   We can write a lot more tests.
-   We can extend the documentation to be more idiomatic.
-   Upon user registration, we can implement an activate account feature for more security.
-   We can give more responsibilities to conversation admins. For now, admins can add and remove people from the group (although a group creator can't be removed). Admins can also delete a conversation member message.
-   We can also look into data encryption so that users can be assured of their privacy.

#### Final note

Since free resources from render are being used (i.e. webserver, redis, and Postgres), there's bound to be some delays most especially when there's been no activity for a while.
