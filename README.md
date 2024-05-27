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

Now that you've built the containers, you're ready to start making requests on ```http:127.0.0.1:8000/api/v1``` and ```ws:127.0.0.1:8000/ws/conversations```

## Running tests
In the root directory, run
```shell
docker-compose -f docker-compose.dev.yml exec web ./run_tests.sh
```
In addition, a GitHub workflow has been set up with the name `run_tests.yml` to automatically run tests for all following changes created either by a push or pull request to the master branch.



## API documentation can be found
```HTTP endpoints: https://documenter.getpostman.com/view/20100124/2sA3Qs9roh```

```WS endpoint: ws://127.0.0.1:8000/ws/conversations/?token=…```

## Deployment

### Render Cloud

To deploy this service on Render, you need to create a Render web service and select a Python environment as your deployment environment as well as set the required env variables so they can become available to the Docker context. Check the `.env.example` file for the list of required env variables. Connect the right GitHub repository to the Render service set the branch to `master` and the path to `./` and then proceed to deploy.

In addition, a CI/CD pipeline has been set up to redeploy changes in the master branch. This is subject to passing the test mentioned above.


## Implementation details and design decisions.

#### Data storage.
Data first persists in the Postgres database and is then saved in the Redis cache. This is due to the in-memory nature of Redis and we understand how important users' chats are. We certainly don't want users to have missing messages. 

We cache at most 500 messages per conversation, this gives users enough to read before it's necessary to send a request. This drastically reduces network calls and also ensures data security while delivering a good experience.


#### Database schema
A simple schema is adopted to capture all necessary data. An API was  subsequently built around it to allow for necessary data to be conveniently shown while keeping network calls minimum.

PostgreSQL was selected due to its scalability, performance, and exciting features.

<img width="1082" alt="Screenshot 2024-05-27 at 11 55 06 AM" src="https://github.com/Fuad28/chat-app/assets/63596779/9258d989-9a00-42a1-b7da-2018ea2f090a">


#### Features
* User management and authentication is handled by Djoser
* WebSocket implementation by django-channels
* Tests are by pytest
* Local development was handled by Docker
* Logging by django built-in logger leveraging file and console.
* Monitoring by sentry. We can further configure this to send logs to a Slack channel.
* Throttling is implemented project-wise and also specifically on messages. The throttle rate for users is 1000 messages per day and that of messages is set to 60 messages per minute. These values are abstract and subsequent observation and data analytics can help establish a sensible value.
* The API is deployed on render.

#### Recommendations for improvement
* We can write a lot more tests. 
* We can extend the documentation to be more idiomatic.
* Upon user registration, we can implement an activate account feature for more security.
* We can give more responsibilities to conversation admins. Admins can currently add and remove people from the conversation (a group creator can't be removed). Admins can also delete a conversation member message.
* We can also leverage our WebSocket connection to broadcast conversation events such as joins and exits.
