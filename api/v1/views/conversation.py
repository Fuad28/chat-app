from django.db.models import Q

from rest_framework import status
from rest_framework.viewsets import ModelViewSet
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action 
from rest_framework.response import Response

from api.models import Conversation,  ConversationMembers
from api.v1.permissions import IsConversationMember, IsConversationAdmin
from api.v1.serializers.conversation import (
	CreateConversationSerializer, ConversationSerializer, SimpleConversationSerializer,
	AddORemoveMemberConversationSerializer)


class ConversationViewSet(ModelViewSet):
	http_method_names= ["get", "post", "patch"]
	
	def get_serializer_class(self):
		if self.action in ["add_member", "remove_member", "make_admin"]:
			return AddORemoveMemberConversationSerializer
		
		if self.action == "create":
			return CreateConversationSerializer
		
		if self.action == "retrieve":
			return ConversationSerializer
		

		return SimpleConversationSerializer
	
	def get_permissions(self):
		if self.action in ["add_member", "remove_member", "make_admin"]:
			return [IsAuthenticated(), IsConversationMember(), IsConversationAdmin()]

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
	def join(self, request, **kwargs):
		conversation = self.get_object()

		if not conversation.members.filter(id= self.request.user).exists():
			return Response({
				"detail": "You are already in conversation."
				},
			status= status.HTTP_400_BAD_REQUEST)
		
		if not conversation.is_private:
			conversation.members.add(self.request.user)
			return Response(status= status.HTTP_204_NO_CONTENT)
		
		return Response({
			"detail": "You can't join a private conversation."
			},
			status= status.HTTP_403_FORBIDDEN)
	

	@action(detail=True, methods=["post"])
	def add_member(self, **kwargs):
		conversation = self.get_object()
		serializer = self.get_serializer(data= self.request.data)
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
	def remove_member(self, **kwargs):
		conversation = self.get_object()
		serializer = self.get_serializer(data= self.request.data)
		serializer.is_valid(raise_exception= True)
		user= serializer.data.get("user")

		if self.request.user != conversation.created_by:
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
	def make_admin(self,  **kwargs):
		conversation = self.get_object()
		serializer = self.get_serializer(data= self.request.data)
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
	
