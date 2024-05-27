from django.db.models import Q

from rest_framework import status
from rest_framework.viewsets import ModelViewSet
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action 
from rest_framework.response import Response
from rest_framework.request import Request

from api.models import Conversation,  ConversationMembers, Message
from api.v1.utils import CustomLimitOffsetPagination
from api.v1.permissions import (
	IsConversationMember, IsConversationAdmin, IsMessageOwnerorAdmin)

from api.v1.serializers.conversation import (
	CreateConversationSerializer, ConversationSerializer, SimpleConversationSerializer,
	AddORemoveMemberConversationSerializer, CreateUpdateMessageSerializer,
	MessageSerializer, SimpleMessageSerializer, MarkMessageReadSerializer
)

class ConversationViewSet(ModelViewSet):
	http_method_names= ["get", "post", "patch"]
	
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
	

	@action(detail=True, methods=["post"])
	def join(self, request: Request, **kwargs):
		conversation = self.get_object()

		if not conversation.members.filter(id= request.user).exists():
			return Response({
				"detail": "You are already in conversation."
				},
			status= status.HTTP_400_BAD_REQUEST)
		
		if not conversation.is_private:
			conversation.members.add(request.user)
			return Response(status= status.HTTP_204_NO_CONTENT)
		
		return Response({
			"detail": "You can't join a private conversation."
			},
			status= status.HTTP_403_FORBIDDEN)

	@action(detail=True, methods=["post"])
	def add_member(self, request: Request, **kwargs):
		conversation = self.get_object()
		serializer = self.get_serializer(data= request.data)
		serializer.is_valid(raise_exception= True)
		user= serializer.data.get("user")

		if conversation.members.filter(id= user).exists():
			return Response({
				"detail": "User is already in conversation."
				},
			status= status.HTTP_400_BAD_REQUEST)

		if not conversation.is_private:
			conversation.members.add(user)
			return Response(status= status.HTTP_204_NO_CONTENT)
		
		return Response({
				"detail": "You can't join a private conversation."},
				status= status.HTTP_403_FORBIDDEN)
	
	@action(detail=True, methods=["post"])
	def remove_member(self, request: Request, **kwargs):
		conversation = self.get_object()
		serializer = self.get_serializer(data= request.data)
		serializer.is_valid(raise_exception= True)
		user= serializer.data.get("user")

		if (user == conversation.created_by.id) and (request.user != conversation.created_by):
			return Response({
				"detail": "You can't remove group creator."
				},
			status= status.HTTP_403_FORBIDDEN)
		

		if not conversation.members.filter(id= user).exists():
			return Response({
				"detail": "User is not in conversation."
				},
			status= status.HTTP_400_BAD_REQUEST)

		
		conversation.members.remove(user)

		return Response(status= status.HTTP_204_NO_CONTENT)
	
	@action(detail=True, methods=["post"])
	def leave_conversation(self, request: Request, **kwargs):
		conversation = self.get_object()

		if not conversation.members.filter(id= request.user.id).exists():
			return Response({
				"detail": "User is not in conversation."
				},
			status= status.HTTP_400_BAD_REQUEST)

		
		conversation.members.remove(request.user)

		return Response(status= status.HTTP_204_NO_CONTENT)
	
	@action(detail=True, methods=["post"])
	def make_admin(self,  request: Request, **kwargs):
		conversation = self.get_object()
		serializer = self.get_serializer(data= request.data)
		serializer.is_valid(raise_exception= True)
		user= serializer.data.get("user")
		

		if not conversation.members.filter(id= user).exists():
			return Response({
				"detail": "User is not in conversation."
				},
			status= status.HTTP_400_BAD_REQUEST)

		
		member= ConversationMembers.objects.get(
			user= user, 
			conversation= conversation
		)
		member.is_admin= True
		member.save()

		return Response(status= status.HTTP_204_NO_CONTENT)
	
	@action(detail=True, methods=["post"])
	def mark_message_read(self,  request: Request, **kwargs):
		print(request.data)
		conversation = self.get_object()
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
		if self.action in ["create", "partial_update", "update"]:
			return CreateUpdateMessageSerializer
		
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
		return {
			"user": self.request.user,
			"conversation_id": self.kwargs.get("conversation_pk")
			}
	