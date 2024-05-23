from django.db import models

import uuid

from api.models import User
from api.enums import MessageTypeEnum

null_blank = {"null": True, "blank": True}

class Conversation(models.Model):
	""" Conversation model. """
	
	id= models. UUIDField(default= uuid.uuid4, editable= False, primary_key= True)
	name= models.CharField(max_length= 100)
	created_by= models.ForeignKey(User, on_delete= models.SET_NULL, related_name= "created_conversations", **null_blank)
	created_at= models.DateTimeField(auto_now= True)
	updated_at= models.DateTimeField(auto_now_add= True)
	members= models.ManyToManyField(User, related_name= "conversations")
	is_private= models.BooleanField(default= False)


	def __str__(self):
		return f"{self.id}-{self.name}"
	

class Message(models.Model):
	""" Message model. """

	id= models. UUIDField(default= uuid.uuid4, editable= False, primary_key= True)
	conversation= models.ForeignKey(User, on_delete= models.CASCADE, related_name= "messages")
	sent_by= models.ForeignKey(User, on_delete= models.SET_NULL, related_name= "sent_messages", **null_blank)
	sent_at= models.DateTimeField(auto_now= True)
	seen_by= models.ManyToManyField(User, related_name= "seen_messages")
	updated_at= models.DateTimeField(auto_now_add= True)
	media_url= models.URLField(**null_blank)
	text= models.TextField(**null_blank)
	message_type= models.CharField(max_length= 50, choices= MessageTypeEnum.choices)
	is_sent = models.BooleanField(default= False)

	def __str__(self):
		return f"{self.id}"

