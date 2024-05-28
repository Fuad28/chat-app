from django.db.models import Q
from django.utils import timezone

from rest_framework import status
from rest_framework.viewsets import ModelViewSet
from rest_framework.serializers import ModelSerializer
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action 
from rest_framework.response import Response
from rest_framework.request import Request
from rest_framework.filters import SearchFilter

from api.models import Conversation,  ConversationMembers, Message
from api.v1.utils import CustomLimitOffsetPagination
from api.v1.signals import new_conversation_event
from api.v1.permissions import (
	IsConversationMember, IsConversationAdmin, IsMessageOwnerorAdmin)

from api.v1.serializers.conversation import (
	CreateConversationSerializer, ConversationSerializer,
	SimpleConversationSerializer, AddORemoveMemberConversationSerializer,
	CreateMessageSerializer, UpdateMessageSerializer, MessageSerializer,
	SimpleMessageSerializer, MarkMessageReadSerializer
)

class ConversationViewSet(ModelViewSet):
	http_method_names= ["get", "post", "patch"]
	filter_backends= [SearchFilter]
	search_fields= ["name"]
	
	def get_serializer_class(self):
		if self.action in ["add_member", "remove_member", "make_admin"]:
			return AddORemoveMemberConversationSerializer
		
		if self.action == "create":
			return CreateConversationSerializer
		
		if self.action == "retrieve":
			return ConversationSerializer
		
		if self.action == "mark_message_read":
			return MarkMessageReadSerializer
		

		return SimpleConversationSerializer
	
	def get_permissions(self):
		if self.action in ["add_member", "remove_member", "make_admin"]:
			return [IsAuthenticated(), IsConversationMember(), IsConversationAdmin()]
		
		if self.action == "mark_message_read":
			return [IsAuthenticated(), IsConversationMember()]

		return [IsAuthenticated()]

	def get_queryset(self):
		if self.action == "list":
			return Conversation.objects.filter(members= self.request.user)

		return Conversation.objects.filter(
			Q(is_private= False) | 
			Q(is_private=True, members= self.request.user)
		).distinct()
	
	def get_object(self) -> Conversation:
		return super().get_object()

	def perform_update(self, serializer: ModelSerializer):
		serializer.validated_data["updated_at"]= timezone.now()

		return super().perform_update(serializer)
	

	@action(detail=True, methods=["post"])
	def join(self, request: Request, **kwargs):
		conversation = self.get_object()

		if conversation.members.filter(id= request.user.id).exists():
			return Response(
				data= {"detail": "You are already in the conversation."},
				status= status.HTTP_400_BAD_REQUEST
			)
		
		if conversation.is_private:
			return Response(
				data= {"detail": "You can't join a private conversation."},
				status= status.HTTP_403_FORBIDDEN
			)
		
		
		conversation.members.add(request.user)

		new_conversation_event.send_robust(
			sender= None, 
			conversation_id= conversation.id,
			event= {
				"type": "user.join", 
				"message": f"{request.user.first_name} joined the conversation."
			})
		
		return Response(status= status.HTTP_204_NO_CONTENT)

	@action(detail=True, methods=["post"])
	def add_member(self, request: Request, **kwargs):
		conversation = self.get_object()
		serializer = self.get_serializer(data= request.data)
		serializer.is_valid(raise_exception= True)
		user= serializer.validated_data.get("user")
		user_in_conv_qs= conversation.members.filter(id= user.id)

		if user_in_conv_qs.exists():
			return Response(
				data= {"detail": "User is already in conversation."},
				status= status.HTTP_400_BAD_REQUEST
			)

		admin_first_name= request.user.first_name
		user_first_name= user.first_name

		new_conversation_event.send_robust(
			sender= None, 
			conversation_id= conversation.id,
			event= {
				"type": "user.added", 
				"message": f"{admin_first_name} added {user_first_name} to the conversation."
			})
			
		conversation.members.add(user)

		return Response(status= status.HTTP_204_NO_CONTENT)
	
	@action(detail=True, methods=["post"])
	def remove_member(self, request: Request, **kwargs):
		conversation = self.get_object()
		serializer = self.get_serializer(data= request.data)
		serializer.is_valid(raise_exception= True)
		user= serializer.validated_data.get("user")
		user_in_conv_qs= conversation.members.filter(id= user.id)

		if (user == conversation.created_by.id) and (request.user != conversation.created_by):
			return Response(
				data= {"detail": "You can't remove group creator."},
				status= status.HTTP_403_FORBIDDEN
			)
		

		if not user_in_conv_qs.exists():
			return Response(
				data= {"detail": "User is not in conversation."},
				status= status.HTTP_400_BAD_REQUEST
			)

		conversation.members.remove(user)

		admin_first_name= request.user.first_name
		user_first_name= user.first_name

		new_conversation_event.send_robust(
			sender= None, 
			conversation_id= conversation.id,
			event= {
				"type": "user.removed", 
				"message": f"{admin_first_name} removed {user_first_name} to the conversation."
			})

		return Response(status= status.HTTP_204_NO_CONTENT)
	
	@action(detail=True, methods=["post"])
	def leave_conversation(self, request: Request, **kwargs):
		conversation = self.get_object()

		if not conversation.members.filter(id= request.user.id).exists():
			return Response(
				data= {"detail": "User is not in conversation."},
				status= status.HTTP_400_BAD_REQUEST
			)
		
		conversation.members.remove(request.user)

		new_conversation_event.send_robust(
			sender= None, 
			conversation_id= conversation.id,
			event= {
				"type": "user.left", 
				"message": f"{request.user.first_name} left the conversation."
			})

		return Response(status= status.HTTP_204_NO_CONTENT)
	
	@action(detail=True, methods=["post"])
	def make_admin(self,  request: Request, **kwargs):
		conversation = self.get_object()
		serializer = self.get_serializer(data= request.data)
		serializer.is_valid(raise_exception= True)
		user= serializer.validated_data["user"]
		user_in_conv_qs= conversation.members.filter(id= user.id)

		if not user_in_conv_qs.exists():
			return Response(
				data= {"detail": "User is not in conversation."},
				status= status.HTTP_400_BAD_REQUEST
			)
		
		member= ConversationMembers.objects.get(
			user= user, 
			conversation= conversation
		)

		if member.is_admin:
			return Response(
				data= {"detail": "User is already an admin."},
				status= status.HTTP_400_BAD_REQUEST
			)

		member.is_admin= True
		member.save()

		admin_first_name= request.user.first_name
		user_first_name= user.first_name

		new_conversation_event.send_robust(
			sender= None, 
			conversation_id= conversation.id,
			event= {
				"type": "new.admin", 
				"message": f"{admin_first_name} made {user_first_name} admin."
			})

		return Response(status= status.HTTP_204_NO_CONTENT)
	
	@action(detail=True, methods=["post"])
	def mark_message_read(self,  request: Request, **kwargs):
		serializer = self.get_serializer(
			data= request.data.get("data"), 
			context= {"user": self.request.user},
			many= True
		)
		serializer.is_valid(raise_exception= True)
		serializer.save()

		return Response(status= status.HTTP_204_NO_CONTENT)
	

class MessageViewSet(ModelViewSet):
	pagination_class = CustomLimitOffsetPagination
	throttle_scope = 'messages'
	
	def get_serializer_class(self):
		if self.action == "create":
			return CreateMessageSerializer
		
		if self.action in ["partial_update", "update"]:
			return UpdateMessageSerializer
		
		if self.action == "list":
			return SimpleMessageSerializer
		
		if self.action == "mark_message_read":
			return MarkMessageReadSerializer
		
		return MessageSerializer
	
	def get_permissions(self):
		if self.action == ["destroy"]:
			return [IsAuthenticated(), IsMessageOwnerorAdmin()]

		return [IsAuthenticated()]

	def get_queryset(self):
		if self.action == "list":
			limit= int(self.request.query_params.get("limit", 50))
			offset= int(self.request.query_params.get("offset", 0))
			conversation_id= self.kwargs.get("conversation_pk")

			return Message.objects.get_messages(conversation_id, offset, limit)
		
		return Message.objects.filter(
			conversation_id= self.kwargs.get("conversation_pk"), 
		)
	
	def get_serializer_context(self):
		context=  {
			"user": self.request.user,
			"conversation_id": self.kwargs.get("conversation_pk"),
			
			}
		
		if self.action not in ["create", "list"]:
			context["message_type"]= self.get_object().message_type

		return context
	
	def get_object(self) -> Message:
		return super().get_object()
	
	def perform_update(self, serializer: ModelSerializer):		
		serializer.validated_data["updated_at"]= timezone.now()

		return super().perform_update(serializer)
	
	def update(self, request, *args, **kwargs):
		message= self.get_object()

		if message.deleted_at:
			return Response(
				data= {"detail": "Update not allowed on deleted message."},
				status= status.HTTP_400_BAD_REQUEST
			)
		
		return super().update(request, *args, **kwargs)
	
	def destroy(self, request, *args, **kwargs):
		message= self.get_object()

		if message.deleted_at:
			return Response(
				data= {"detail": "Delete not allowed on deleted message."},
				status= status.HTTP_400_BAD_REQUEST
			)
		return super().destroy(request, *args, **kwargs)
	
	def perform_destroy(self, instance: Message):
		instance.deleted_at= timezone.now()
		instance.save()	