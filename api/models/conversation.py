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
	members= models.ManyToManyField(User, through= "ConversationMembers", through_fields=("group", "user"), related_name= "conversations")
	is_private= models.BooleanField(default= False)


	def __str__(self):
		return f"{self.id}-{self.name}"
	
	def add_member(self, user: User):
		self.members.add(user)

	def remove_member(self, user: User):
		self.members.remove(user)


class ConversationMembers(models.Model):
	""" Holds members of a conversation record. """
	
	user= models.ForeignKey(User, on_delete= models.CASCADE)
	conversation= models.ForeignKey(Conversation, on_delete= models.CASCADE)
	joined_at= models.DateTimeField(auto_now= True)
	is_admin= models.BooleanField(default= False)

class Message(models.Model):
	""" Message model. """

	id= models. UUIDField(default= uuid.uuid4, editable= False, primary_key= True)
	conversation= models.ForeignKey(Conversation, on_delete= models.CASCADE, related_name= "messages")
	sent_by= models.ForeignKey(User, on_delete= models.SET_NULL, related_name= "sent_messages", **null_blank)
	sent_at= models.DateTimeField(auto_now= True)
	seen_by= models.ManyToManyField(User, through= "MessageViewers", through_fields=("message", "user"), related_name= "seen_messages")
	updated_at= models.DateTimeField(auto_now_add= True)
	media_url= models.URLField(**null_blank)
	text= models.TextField(**null_blank)
	message_type= models.CharField(max_length= 50, choices= MessageTypeEnum.choices)
	is_sent = models.BooleanField(default= False)

	def __str__(self):
		return f"{self.id}"
	

class MessageViewers(models.Model):
	""" Holds users that have seen a message. """
	
	user= models.ForeignKey(User, on_delete= models.CASCADE)
	message= models.ForeignKey(Message, on_delete= models.CASCADE)
	seen_at= models.DateTimeField(auto_now= True)