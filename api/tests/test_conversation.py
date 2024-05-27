from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework import status 

from channels.testing import WebsocketCommunicator
from channels.db import database_sync_to_async
from model_bakery import  baker
import pytest

from chat_app.asgi import application
from api.models import  User, Conversation, ConversationMembers


@pytest.fixture
def user_login():
	def do_user_login(login_cred):
		client= APIClient()
		return client.post('/api/v1/login/', login_cred)
	return do_user_login


@pytest.mark.django_db
class TestConversationAuthorization:
	
	def test_if_admin_can_add_returns_204(self):

		client= APIClient()
		user_1 = baker.make(User)
		user_2 = baker.make(User)
		conversation = baker.make(Conversation)
		baker.make(
			ConversationMembers, 
			user= user_1,
			conversation= conversation, 
			is_admin= True
		)

		client.force_authenticate(user_1)

		response= client.post(
			f'/api/v1/conversations/{conversation.id}/add_member/', {
				"user": user_2.id
			})

		assert response.status_code == status.HTTP_204_NO_CONTENT

	def test_if_non_admin_can_add_returns_401(self):

		client= APIClient()
		user_1 = baker.make(User)
		user_2 = baker.make(User)
		client.force_authenticate(user_1)
		conversation = baker.make(Conversation)

		client.force_authenticate(user_1)

		response= client.post(
			f'/api/v1/conversations/{conversation.id}/add_member/', {
				"user": user_2.id
			})

		assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.django_db
class TestMessageThrottling:
	
	def test_user_is_throttled_on_message_if_exceed_60_req_per_minute_returns_429(self):

		client= APIClient()
		user_1 = baker.make(User)
		conversation = baker.make(Conversation)
		baker.make(
			ConversationMembers, 
			user= user_1,
			conversation= conversation, 
		)

		client.force_authenticate(user_1)

		for i in range(65):
			response= client.get(f'/api/v1/conversations/{conversation.id}/messages/')

		assert response.status_code == status.HTTP_429_TOO_MANY_REQUESTS

	
	def test_user_is_not_throttled_on_message_if_not_exceed_60_req_per_minute_returns_429(self):

		client= APIClient()
		user_1 = baker.make(User)
		conversation = baker.make(Conversation)
		baker.make(
			ConversationMembers, 
			user= user_1,
			conversation= conversation, 
		)

		client.force_authenticate(user_1)

		for i in range(10):
			response= client.get(f'/api/v1/conversations/{conversation.id}/messages/')

		assert response.status_code == status.HTTP_200_OK


@pytest.mark.asyncio
@pytest.mark.django_db
class TestConversationConsumer:
	async def test_websocket_connection_is_active(self):
		
		user = await database_sync_to_async(baker.make)(User)
		refresh = RefreshToken.for_user(user)
		access_token = str(refresh.access_token)

		communicator = WebsocketCommunicator(
			application, 
			f"ws/conversations/?token={access_token}"
		)

		connected, _ = await communicator.connect()
		assert connected

		event = await communicator.receive_json_from(timeout= 3)
		assert event.get("message") is not None
		assert event["message"].get("status") == "connected"

		await communicator.disconnect()

	