from django.db import models
from django.utils import timezone

import uuid

from api.models import User
from api.enums import MessageTypeEnum
from api.managers import CachedMessageQuerySet

null_blank = {"null": True, "blank": True}

class Conversation(models.Model):
	""" Conversation model. """
	
	id= models. UUIDField(default= uuid.uuid4, editable= False, primary_key= True)
	name= models.CharField(max_length= 100)

	created_by= models.ForeignKey(
		User, 
		on_delete= models.SET_NULL, 
		related_name= "created_conversations",
		**null_blank
	)

	members= models.ManyToManyField(
		User, 
		through= "ConversationMembers", 
		through_fields=("conversation", "user"),
		related_name= "conversations"
	)

	created_at= models.DateTimeField(auto_now_add= True)
	updated_at= models.DateTimeField(**null_blank)
	is_private= models.BooleanField(default= False)

	def to_dict(self):
		return {
			"id": str(self.id),
			"name": self.name,
			"is_private": self.is_private,
			"created_by": self.created_by.get_full_name()
		}

	def __str__(self):
		return f"{self.id}-{self.name}"
	
	def save(self, *args, **kwargs):
		if self.pk:  
			self.updated_at = timezone.now()
		super().save(*args, **kwargs)
		
class ConversationMembers(models.Model):
	""" Holds members of a conversation record. """
	
	user= models.ForeignKey(User, on_delete= models.CASCADE)
	conversation= models.ForeignKey(Conversation, on_delete= models.CASCADE)
	joined_at= models.DateTimeField(auto_now_add= True)
	is_admin= models.BooleanField(default= False)


class Message(models.Model):
	""" Message model. """

	id= models. UUIDField(default= uuid.uuid4, editable= False, primary_key= True)

	conversation= models.ForeignKey(
		Conversation, 
		on_delete= models.CASCADE, 
		related_name= "messages"
	)

	sent_by= models.ForeignKey(
		User, 
		on_delete= models.SET_NULL, 
		related_name= "sent_messages", 
		**null_blank
	)

	seen_by= models.ManyToManyField(
		User, 
		through= "MessageViewers", 
		through_fields=("message", "user"), 
		related_name= "seen_messages"
		)
	
	sent_at= models.DateTimeField(auto_now_add= True)
	updated_at= models.DateTimeField(**null_blank)
	media_url= models.URLField(**null_blank)
	text= models.TextField(**null_blank)
	message_type= models.CharField(max_length= 50, choices= MessageTypeEnum.choices)

	objects= CachedMessageQuerySet.as_manager()

	def __str__(self):
		return f"{self.id}"
	
	def save(self, *args, **kwargs):
		if self.pk:  
			self.updated_at = timezone.now()
		super().save(*args, **kwargs)
	
class MessageViewers(models.Model):
	""" Holds users that have seen a message. """
	
	user= models.ForeignKey(User, on_delete= models.CASCADE)
	message= models.ForeignKey(Message, on_delete= models.CASCADE)
	seen_at= models.DateTimeField(auto_now= True)