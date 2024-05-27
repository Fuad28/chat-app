from rest_framework import status 
from api.models import  User
from rest_framework.test import APIClient
import pytest


@pytest.fixture
def user_login():
	def do_user_login(login_cred):
		client= APIClient()
		return client.post('/api/v1/login/', login_cred)
	return do_user_login

	

@pytest.mark.django_db
class TestUserLogin:
	valid_data= {
		"first_name": "John",
		"last_name": "Doe",
		"email": "johndoe@gmail.com",
		"password": "user1234"
	}

	invalid_data= {
		"first_name": "John",
		"last_name": "Doe", 
		"email": "johndoe@gmail.com"
	}

	
	def test_invalid_login_credentials_returns_401(self, user_login):
		User.objects.create_user(is_active= True, **self.valid_data)

		response= user_login({
			"email": self.valid_data.get("email"),
			"password": "balablu"
		})

		assert response.status_code == status.HTTP_401_UNAUTHORIZED

	def test_valid_login_credentials_returns_200(self, user_login):
		User.objects.create_user(is_active= True, **self.valid_data)

		response= user_login({
			"email": self.valid_data.get("email"),
			"password": self.valid_data.get("password")
		})

		assert response.status_code == status.HTTP_200_OK